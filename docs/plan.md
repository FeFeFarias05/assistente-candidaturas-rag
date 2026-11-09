# Plano técnico: Assistente de Candidaturas

Status: **rascunho, aguardando aprovação**. Base: [spec.md](spec.md) v2.

## 1. Visão geral

```
vaga (texto)                          material (PDF/MD/TXT)
    │                                        │ ingest (1x, ou quando muda)
    ▼                                        ▼
extract (LLM, JSON)                  chunks + embeddings locais ──► index.db
    │ requisitos[]                           │
    ▼                                        │
retrieve: 1 consulta por requisito ◄─────────┘  (cosseno, top-3 cada)
    │ trechos com id [arquivo#chunk]
    ▼
analyze (LLM): só pode usar os trechos
    │
    ▼
validate: toda citação [id] existe? ──► relatório .md em reports/
    │
    ▼
tracker: registra candidatura ──► applications.db
```

Fluxo em um comando: `python -m jobassist analyze vaga.txt` (ou colando no stdin).

## 2. Stack e dependências (mínimas)

| Pacote | Para quê |
|--------|----------|
| `openai` | LLM (e embeddings opcionais) |
| `fastembed` | embeddings locais (ONNX, sem PyTorch) |
| `pypdf` | texto de PDF |
| `numpy` | similaridade de cosseno (já vem com o fastembed) |
| `python-dotenv` | ler `.env` |
| `pytest` | testes (dev) |

Stdlib para o resto: `sqlite3`, `argparse`, `dataclasses`, `json`, `hashlib`, `re`. Sem LangChain, sem banco vetorial, sem pydantic.

## 3. Estrutura de pastas

```
RAG/
├── README.md
├── docs/                   # spec.md, plan.md, tasks.md (SDD)
├── .env.example            # chaves e opções (versionado, sem segredos)
├── .gitignore              # .env, data/private/*, *.db, reports/
├── requirements.txt  pytest.ini
├── prompts/
│   ├── extract.md          # prompt de extração da vaga
│   └── analyze.md          # prompt de análise e rascunhos
├── src/jobassist/
│   ├── config.py           # lê .env
│   ├── llm.py              # chamada ao LLM (única porta de saída)
│   ├── extract.py          # vaga -> requisitos (JSON)
│   ├── ingest.py           # arquivos -> chunks -> embeddings -> index.db
│   ├── embed.py            # embed(textos, tipo) local | openai
│   ├── retrieve.py         # busca top-k por requisito
│   ├── analyze.py          # monta prompt, chama LLM, valida citações
│   ├── tracker.py          # SQLite de candidaturas
│   └── cli.py              # comandos
├── data/
│   ├── sample/             # material FICTÍCIO (versionado)
│   └── private/            # material real (ignorado pelo Git)
├── eval/
│   ├── jobs/               # 5-10 vagas de teste (.txt)
│   ├── run_eval.py         # roda e confere invenções
│   └── results.md          # resultados e notas manuais
└── tests/
```

## 4. Modelos de dados

**Vaga extraída** (JSON; campo ausente = `null` ou lista vazia):
```json
{
  "title": "str|null", "company": "str|null", "language": "pt|en",
  "seniority": "str|null",
  "requirements": [
    {"text": "Python", "kind": "tech|responsibility|soft|other",
     "required": true}
  ]
}
```

**Chunk** (tabela `chunks` em `index.db`):
`id` (ex.: `curriculo.pdf#p2c3`), `source`, `page` (null em MD/TXT), `text`, `embedding` (BLOB float32), `file_hash`.

**Candidatura** (tabela `applications` em `applications.db`):
`id`, `company`, `title`, `applied_on` (ISO), `status` (`interessada|candidatei|entrevista|recusada|oferta`), `report_path`, `created_at`.

Decisão: **dois arquivos SQLite separados**. O índice pode ser apagado e refeito a qualquer momento; o registro de candidaturas é dado precioso e não deve ser perdido numa reindexação.

## 5. RAG

**Ingestão.** PDF: `pypdf` extrai o texto por página. MD/TXT: arquivo inteiro. Se um PDF retorna pouquíssimo texto, avisa que pode ser escaneado.

**Chunking.** Separar por parágrafo ou título (linha em branco ou linha curta em caixa alta/`#`), juntar até ~700 caracteres com sobreposição de ~100. Cada chunk guarda arquivo e página para a citação. Alvo: chunks que cobrem uma experiência ou um projeto, não uma linha solta.

**Embeddings.** Modelo local multilíngue (`multilingual-e5-small`) via `fastembed`. Esse modelo pede prefixos: `passage: ` ao indexar e `query: ` ao buscar (tratado dentro de `embed.py`). `EMBEDDINGS=openai` troca para `text-embedding-3-small` no `.env`. Se o provedor mudar, o índice é refeito (a dimensão difere; o provedor fica gravado no índice e o programa recusa misturar).

**Armazenamento e busca.** Embeddings em BLOB no SQLite; ao buscar, carrega tudo em um array NumPy e calcula cosseno por força bruta. `# ponytail: força bruta, serve até ~10 mil chunks; acima disso, trocar por FAISS/sqlite-vec`. Reindexação incremental por hash do arquivo.

**Busca.** Uma consulta por requisito extraído (não uma consulta com a vaga inteira): top-3 por requisito, removendo duplicatas, limite total de ~12 trechos. Cada requisito mantém a lista dos seus trechos, o que alimenta a seção de lacunas. Um limiar mínimo de similaridade evita devolver lixo: abaixo dele, o requisito fica "sem evidência".

## 6. Prompts principais

Ficam em `prompts/*.md` (editáveis sem tocar no código).

**extract.md** (temperatura 0, saída com JSON Schema do provedor): "Extraia só o que está escrito na vaga. Se um campo não aparece, use null. Não deduza senioridade nem tecnologias que não estejam no texto. Cite as tecnologias com a grafia da vaga."

**analyze.md** (temperatura baixa). Regras no prompt:
1. Use SOMENTE os trechos fornecidos, cada um com id `[arquivo#chunk]`.
2. Toda afirmação sobre mim termina com a citação `[id]`.
3. Se nenhum trecho sustenta um requisito, escreva "sem evidência no material" e coloque em Lacunas. Nunca complete com conhecimento geral.
4. Não invente métricas, datas, empresas nem tecnologias.
5. Seções fixas: Resumo da vaga, Pontos fortes, Lacunas, O que destacar no currículo, Rascunho de mensagem. Rascunho no idioma da vaga, marcado como "RASCUNHO, revisar".

**Validação (código, não prompt).** Depois da resposta, uma regex extrai todos os `[id]`. Citação que não existe no índice = falha: o sistema tenta uma vez de novo com o erro apontado; se persistir, marca o relatório com um aviso visível. Complemento: para cada tecnologia listada como ponto forte, checa se o termo aparece em algum trecho recuperado (cobre CA5).

## 7. Decisões e justificativas

| Decisão | Alternativas | Escolha e motivo |
|---------|--------------|------------------|
| Embeddings locais | API OpenAI | Local: o material completo não sai da máquina (aprovado). Custo: download do modelo e qualidade um pouco menor. |
| Busca por força bruta em NumPy | Chroma, FAISS | Menos dependências e código legível; o material tem poucos milhares de chunks no máximo. |
| Uma consulta por requisito | Uma consulta com a vaga inteira | Mais precisa e dá lacunas por requisito, ao custo de mais chamadas de embedding (locais, baratas). |
| Citação validada por código | Só confiar no prompt | O prompt reduz, mas só código garante que a citação existe (CA3). |
| JSON Schema na extração | Parsear texto livre | Saída previsível e testável (CA1/CA2). |
| Sem framework (LangChain etc.) | LangChain/LlamaIndex | O pipeline tem 5 passos; framework esconderia o que o portfólio quer mostrar. |
| Versão sem RAG primeiro (Dia 2) | Ir direto ao RAG | Cria uma linha de base para medir o ganho do RAG (CA10) e já entrega valor cedo. Mantida como `--no-rag` para a comparação. |
| Modelo de LLM no `.env` | Fixar no código | Troca sem editar código; escolho um modelo pequeno e barato no Dia 1 e registro no README. |
| Dois SQLite | Um só | Índice descartável × registro durável (ver seção 4). |

## 8. Segurança e privacidade
- `.gitignore` criado antes do primeiro commit: `.env`, `data/private/`, `*.db`, `reports/`.
- `.env.example` com `OPENAI_API_KEY=`, `OPENAI_MODEL=`, `EMBEDDINGS=local`, `MATERIAL_DIR=data/sample`. O padrão aponta para o material fictício.
- `llm.py` é o único ponto que chama a API, e registra no terminal quantos trechos estão sendo enviados.
- Commits sem coautor, conforme a sua regra.

## 9. Testes
Poucos e úteis, sem framework além do `pytest`:
- chunking (tamanho, sobreposição, ids únicos);
- validação de citações (existente × inventada);
- busca determinística com embeddings falsos;
- tracker (grava, reinicia, lê);
- avaliação do Dia 6 (`eval/run_eval.py`) com as vagas-isca. Chama a API de verdade, então fica fora do `pytest` padrão.

## 10. Itens ainda abertos (decido com a sua opinião, se quiser)
- Modelo exato da OpenAI: escolho no Dia 1 com base em custo e qualidade, e deixo em `.env`.
- Limiar de similaridade e valor de top-k: calibrados na avaliação do Dia 6.

## 11. Desvios do plano durante a implementação

| Plano | O que foi feito | Por quê |
|-------|-----------------|---------|
| `multilingual-e5-small` | `paraphrase-multilingual-MiniLM-L12-v2` (220 MB) | O `fastembed` não suporta o e5-small. O e5-large tem 2,2 GB. |
| Chunks de ~700 caracteres | ~450 caracteres | O MiniLM lê ~128 tokens; chunks maiores seriam truncados. |
| Prefixos `query:`/`passage:` | Parâmetro `kind` mantido, ignorado pelo MiniLM | Só e5 usa prefixos; a assinatura permite trocar de modelo. |
| Busca só por similaridade | Busca híbrida: bônus para termo de tecnologia citado literalmente | O MiniLM é fraco com nomes soltos ("JavaScript" = 0,24). |
| Temperatura 0 na extração | Sem `temperature`; JSON Schema estrito | Modelos GPT-5 só aceitam a temperatura padrão. |
| Validação: citações e tecnologias; erro = 1 nova tentativa só para citações | Nova tentativa também para tecnologia sem suporte e item contraditório | A avaliação (Dia 6) mostrou invenção que passava pela validação só como aviso. |
| Validação só avisa quando o modelo não corrige | Item sem suporte é movido de Pontos fortes para Lacunas pelo código (`demote`) | O modelo varia entre execuções; só o aviso deixava a afirmação falsa no relatório. |
| Busca híbrida só para tecnologia | Também: versão nos dois lados (HTML5 ≈ HTML) e tabela de idiomas (English ≈ Inglês) | Falsas lacunas achadas ao testar com um currículo real. |
| "Não indexar dados sensíveis" (risco da spec, sem implementação) | Remoção de linhas com endereço, nascimento, telefone, CPF e e-mail em `material.py` | Foi encontrado no currículo real que isso não estava implementado. |
| Vagas em `data/private/vagas/` | Vagas em `data/vagas/` | Dentro de `data/private/` elas seriam lidas como material pessoal. |
| `openai`, `fastembed`, `pypdf`, `numpy`, `python-dotenv` | Mesmas dependências (numpy vem com o fastembed); versões fixadas no Dia 7 | — |

Medidas e justificativas em [avaliacao.md](avaliacao.md).

## 12. Evolução depois da v0.1.0 (v0.2.0)

| Decisão | Alternativas | Escolha e motivo |
|---------|--------------|------------------|
| `.docx` e `.pptx` lidos com `zipfile` e XML da biblioteca padrão | `python-docx`, `python-pptx` | Zero dependência nova; só o texto interessa. Limite de 20 MB por parte do arquivo contra zip malicioso. |
| Sem OCR | `pytesseract` | Exige instalar o Tesseract no sistema; PDF escaneado continua sem suporte e o aviso diz isso. |
| Preços da API opcionais no `.env` | Tabela de preços no código | Os preços mudam e eu não consigo confirmá-los; sem eles, só os tokens aparecem. |
| `service.py` compartilhado por CLI e web | Duplicar a lógica na web | Uma única regra de privacidade e de análise; a web não vira um segundo caminho sem as proteções. |
| Flask + HTML/CSS/JS puros, sem build | FastAPI, React | Uma dependência nova e nenhuma etapa de build; é uma ferramenta local de uma pessoa. |
| Cabeçalho `X-JobAssist` em toda requisição que altera algo | Token CSRF por sessão | Sem sessão nem login, o cabeçalho próprio basta: navegadores não o enviam entre origens sem preflight. |
| Front-end monta o DOM com nós de texto | Renderizar Markdown com biblioteca | O relatório vem de um LLM; não usar `innerHTML` elimina uma classe inteira de problemas (há teste). |
| Upload bloqueado no material de exemplo | Permitir | A pasta `data/sample` é versionada; um upload ali poderia ir parar no Git. |
