# Assistente de candidaturas (LLM + RAG)

Você cola o texto de uma vaga. O sistema extrai os requisitos, busca no **seu** material (currículo, projetos, respostas anteriores) os trechos relevantes e devolve: resumo da vaga, pontos fortes, lacunas, o que destacar no currículo e um rascunho de mensagem. Cada afirmação cita o trecho de onde veio. Depois, registra a candidatura.

Projeto de portfólio feito em 7 dias com Spec-Driven Development: [especificação](docs/spec.md), [plano](docs/plan.md), [tarefas](docs/tasks.md).

## O problema e as regras

Assistentes de IA tendem a "melhorar" o currículo: inventam uma tecnologia, arredondam 6 meses para 1 ano. Numa candidatura isso é pior que não ajudar. As regras do projeto:

1. **Nunca inventar** experiência, tecnologia ou resultado. Sem informação, o relatório diz "sem evidência no material".
2. **Toda sugestão cita o trecho de origem** (`[curriculo.pdf#p1c2]`), e o código confere se a citação existe e se a tecnologia citada está escrita no trecho.
3. **O texto final é seu.** Tudo sai como rascunho; o sistema não envia nada a ninguém.
4. **Dados pessoais e chaves ficam fora do repositório** (`.env`, `data/private/`, `*.db` no `.gitignore`).

Veja um [relatório de exemplo](docs/exemplo-relatorio.md) (saída real, sem edição, com material fictício).

## Como rodar

Requer Python 3.10+ e uma chave da API da OpenAI com crédito.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
cp .env.example .env        # preencha OPENAI_API_KEY (e confira OPENAI_MODEL)
jobassist analyze eval/jobs/05_frontend_jr_pt.txt
```

Na primeira execução o modelo de embeddings (~220 MB) é baixado para `.cache/`. O material padrão é o **fictício** de `data/sample/`.

| Comando | O que faz |
|---|---|
| `jobassist analyze vaga.txt` | Relatório com RAG. Sem o arquivo, cola a vaga no terminal. Salva em `reports/`. Pergunta se registra a candidatura. |
| `jobassist analyze vaga.txt --lang en` | Força o idioma do rascunho (padrão: o da vaga). |
| `jobassist analyze vaga.txt --register candidatei` | Registra sem perguntar. |
| `jobassist analyze vaga.txt --no-rag` | Linha de base: manda o material inteiro no prompt. |
| `jobassist extract vaga.txt` | Só extrai os requisitos (JSON). |
| `jobassist ingest [--rebuild]` | Indexa o material. O `analyze` já faz isso, só do que mudou. |
| `jobassist add EMPRESA TITULO` / `list` / `status ID NOVO` | Registro de candidaturas (SQLite). Status: interessada, candidatei, entrevista, recusada, oferta. |

**Usar o seu material real:** coloque PDF (com texto selecionável), `.md` ou `.txt` em `data/private/` e ponha `MATERIAL_DIR=data/private` no `.env`. Essa pasta é ignorada pelo Git. Guarde as **vagas** em `data/vagas/` (também ignorada), nunca dentro de `data/private/`: tudo que está na pasta de material é lido como experiência sua.

**Dados pessoais:** antes de indexar ou enviar qualquer coisa, o sistema remove as linhas com endereço, data de nascimento, telefone, CPF e e-mail (Linkedin e GitHub ficam) e avisa quantas removeu. É uma heurística por linha: dados pessoais no meio de um parágrafo não são pegos.

## Como funciona

```
vaga → extração (LLM, JSON) → requisitos
material → trechos (~450 caracteres) → embeddings locais → index.db
cada requisito → busca por similaridade (+ termo literal p/ tecnologias) → trechos
vaga + trechos → LLM → relatório → validação por código → reports/*.md → applications.db
```

## Decisões (e por quê)

- **Primeiro a versão sem RAG (Dia 2).** Com o currículo inteiro no prompt, o sistema já era útil e deu uma **linha de base**. Sem ela eu não saberia se o RAG ajuda. É o que a avaliação mostrou: com material pequeno, os dois modos chegam ao mesmo resultado (ver abaixo). O modo continua disponível em `--no-rag`.
- **Embeddings locais por padrão.** O material completo não sai da máquina. Só a vaga e os trechos recuperados vão ao LLM. Não é "100% privado", e o modo `--no-rag` só roda com material fictício, a menos que você confirme com `--yes-send-all`. `EMBEDDINGS=openai` troca o provedor; o índice recusa misturar provedores (`ingest --rebuild`).
- **Busca híbrida.** O modelo local (MiniLM multilíngue) é bom com frases e fraco com nomes soltos: "JavaScript" teve nota 0,24 num currículo que o cita. Para requisitos de tecnologia, o trecho que contém o termo literalmente ganha bônus no ranking (HTML5 casa com "HTML" e vice-versa). Idiomas têm uma tabela pequena nos dois sentidos, porque o modelo não liga "English" a "Inglês" (vaga em um idioma, currículo em outro). Os dois ajustes vieram de falsas lacunas encontradas ao testar com um currículo real.
- **Uma consulta por requisito**, em vez de uma consulta com a vaga inteira. É mais precisa e dá o mapa "requisito → trechos".
- **Validação em código, não só no prompt.** O prompt reduz as invenções, mas só o código garante: (1) toda citação `[id]` existe; (2) tecnologia em "Pontos fortes" aparece no trecho que o item cita; (3) item em "Pontos fortes" não diz "sem evidência". Se algo falha, o sistema pede uma correção uma vez. Se o item de Pontos fortes persistir, o código o move para Lacunas. Citação inexistente que persistir fica como aviso no topo do relatório.
- **Sem framework** (LangChain etc.) e **sem banco vetorial**: força bruta em NumPy, suficiente até ~10 mil trechos. São 5 passos que o projeto prefere mostrar a esconder.
- **Dois arquivos SQLite**: o índice (`index.db`) é descartável; as candidaturas (`applications.db`) não.
- **Sem `temperature`**: os modelos GPT-5 só aceitam o padrão. A previsibilidade da extração vem do JSON Schema estrito.

## Avaliação

`python eval/run_eval.py` roda 7 vagas de teste (PT e EN) nos dois modos, com o material fictício, e confere invenções, iscas e citações. Detalhes, antes e depois, e limites em [docs/avaliacao.md](docs/avaliacao.md).

| | Sem RAG | RAG |
|---|---|---|
| Tecnologia ausente afirmada como forte | 0 | 1** |
| Citações inexistentes | 0 | 0 |
| Iscas em "Lacunas" (18 tecnologias que o perfil não tem) | 17/18* | 17/18* |
| Relatórios com aviso de validação | 0/7 | 2/7 |
| Relevância da busca (0 a 2, 76 requisitos) | | 1,63 |

\* A "perdida" é um artefato da métrica (`.NET`, coberta no texto por "ASP.NET Core").
\*\* "SQL Server" inflado a partir de "SQL": a validação só confere tecnologias de uma palavra.

O que a avaliação ensinou:
- Na **primeira rodada o RAG inventou mais** (5 casos, como "AWS" e "GraphQL" que o perfil não tem, com citação real apontando para um trecho que não dizia isso). Reforcei a validação e o prompt. Como o modelo varia entre execuções, a nova tentativa não bastou: hoje, se o modelo não corrige, **o código move o item de Pontos fortes para Lacunas** e avisa no relatório.
- **O RAG não melhorou a qualidade** com este material pequeno (4 arquivos). Onde ele deve compensar, e não foi medido, é em material grande, custo e privacidade.
- A busca devolve trecho irrelevante para requisitos que o perfil não tem (11 de 76). Mantive o limiar de similaridade em 0,30 para não criar falsas lacunas; o LLM e a validação filtram o resto.
- A nota de relevância foi atribuída por mim, não por quem usa o sistema. Revise antes de citá-la.

## Limites

- 7 vagas, um modelo (`gpt-5.4-mini`), um perfil fictício pequeno. Não comparei com um modelo maior.
- O LLM varia entre execuções: a mesma vaga pode classificar um item como ponto forte numa rodada e como lacuna na outra (visto em teste). Os números da avaliação são de uma execução, não uma média.
- A validação pega invenção de **tecnologia de uma palavra** e citação falsa, mas não pega toda inflação (ex.: "SQL" tratado como "SQL Server"; "projeto em dupla" tratado como "trabalho com designers"). O texto precisa de revisão humana.
- A ordem do texto extraído de PDFs com caixas e barras laterais pode vir embaralhada (títulos fora do lugar); o conteúdo vem inteiro, mas a busca fica um pouco pior. O modo `layout` do `pypdf` não extraiu nada do PDF testado.
- Só PDF com texto selecionável (sem OCR) e só tecnologias de uma palavra são conferidas no trecho citado (termos como "web development" dariam falso alarme).
- Interface só no terminal.

## Estrutura

```
docs/        especificação, plano, tarefas, avaliação, linha de base, exemplo
src/jobassist/  extract · material · chunking · embed · ingest · retrieve · analyze · tracker · llm · cli
prompts/     extract.md, analyze.md (editáveis sem tocar no código)
data/sample/ material fictício (versionado) · data/private/ material real e data/vagas/ vagas (ignorados)
eval/        vagas de teste, run_eval.py, resultados
tests/       83 testes (pytest), sem chamar a API
```

Testes: `pytest`. A avaliação (`eval/run_eval.py`) chama a API de verdade e fica fora do `pytest`.
