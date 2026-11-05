# Tarefas: Assistente de Candidaturas

Status: **rascunho, aguardando aprovação**. Base: [spec.md](spec.md) e [plan.md](plan.md).
Orçamento: 7 dias × ~2h = 14h. A soma das estimativas abaixo é ~12h, deixando ~2h de folga para imprevistos.
Regra: uma tarefa por vez; ao final de cada uma resumo o que mudou e como validar, e só avanço com o seu OK.

---

## Dia 1: chamada ao LLM e extração de requisitos

| # | Tarefa | Critério de pronto | Est. |
|---|--------|--------------------|------|
| 1.1 | Esqueleto do projeto: `.gitignore` (primeiro arquivo), `.env.example`, `requirements.txt`, `config.py`, pastas, `git init` | `.env`, `data/private/`, `*.db` e `reports/` ignorados (verificado com `git status` após criar um `.env` de teste); config lê `.env`; commit inicial sem coautor | 30 min |
| 1.2 | `llm.py`: uma função que chama a OpenAI e devolve texto ou JSON. Escolher o modelo (ver lista atual, registrar o motivo) | Chamada de teste responde; sem chave, mostra erro claro; modelo vem do `.env` | 30 min |
| 1.3 | `extract.py` + `prompts/extract.md`: vaga → JSON de requisitos (schema do plano) | CA1 e CA2: 3 vagas reais de teste (PT e EN) geram JSON válido; tecnologias aparecem literalmente na vaga; campos ausentes ficam `null`. Teste de pytest com saída do LLM simulada | 45 min |
| 1.4 | CLI mínimo: `extract vaga.txt` imprime o JSON | Roda ponta a ponta no terminal | 15 min |

**Marco do Dia 1:** colar uma vaga e ver os requisitos extraídos.

---

## Dia 2: versão simples sem RAG (currículo inteiro no prompt)

| # | Tarefa | Critério de pronto | Est. |
|---|--------|--------------------|------|
| 2.1 | Criar material **fictício** em `data/sample/` (currículo em PDF, 2 projetos em `.md`, 1 arquivo de respostas anteriores; mistura PT/EN; contém coisas que o perfil fictício claramente NÃO tem, para servir de isca) | Arquivos existem; nenhum dado real; README curto na pasta explica que é fictício | 40 min |
| 2.2 | Leitura de material: `.pdf` com `pypdf`, `.md`, `.txt` → texto único | Lê os 3 formatos; avisa se um PDF vier quase vazio | 25 min |
| 2.3 | `analyze.py` + `prompts/analyze.md` em modo `--no-rag`: vaga extraída + material inteiro → relatório com as 5 seções, no idioma certo (`--lang` força outro) | Relatório gerado e salvo em `reports/`; rascunho em idioma da vaga marcado como RASCUNHO; funciona só com material fictício | 50 min |
| 2.4 | Teste de bom senso nas iscas | CA4 (versão sem RAG): requisito que o perfil fictício não tem aparece em Lacunas, não em Pontos fortes. Resultado anotado (será a linha de base) | 25 min |

**Marco do Dia 2:** ferramenta que já é útil, e uma linha de base para comparar com o RAG. Aviso explícito no terminal de que o material inteiro está sendo enviado à API.

---

## Dia 3: organização do material e embeddings

| # | Tarefa | Critério de pronto | Est. |
|---|--------|--------------------|------|
| 3.1 | `ingest.py`: chunking por parágrafo/título (~700 caracteres, sobreposição ~100), ids `arquivo#pXcY` | Teste pytest: tamanhos dentro do limite, ids únicos, página correta no PDF | 45 min |
| 3.2 | `embed.py`: embeddings locais com `fastembed` (prefixos `passage:`/`query:`), opção `openai` via `.env` | Gera vetores para 2 textos; dimensão correta; trocar `EMBEDDINGS` funciona; índice recusa misturar provedores | 40 min |
| 3.3 | Gravar chunks e embeddings em `index.db`; reindexação incremental por hash | `ingest` roda 2×: a segunda não recalcula nada; alterar um arquivo reindexa só ele | 30 min |
| 3.4 | Testar com um PDF real seu (só local, sem enviar nada) | Texto sai em ordem legível; se não, anotar o problema e o fallback (converter para `.md`) | 15 min |

**Marco do Dia 3:** `python -m jobassist ingest` cria o índice a partir do material.

---

## Dia 4: busca RAG com citação das fontes

| # | Tarefa | Critério de pronto | Est. |
|---|--------|--------------------|------|
| 4.1 | `retrieve.py`: uma consulta por requisito, cosseno em NumPy, top-3, sem duplicatas, limite ~12, limiar mínimo | Teste pytest com embeddings falsos e determinísticos; requisito sem trecho acima do limiar fica "sem evidência" | 45 min |
| 4.2 | `analyze.py` em modo RAG: envia só os trechos recuperados, cada um com seu id | Relatório gera com citações `[arquivo#pXcY]` | 40 min |
| 4.3 | Validação por código: toda citação existe no índice; tecnologia em Pontos fortes aparece nos trechos; uma nova tentativa se falhar, depois aviso visível | CA3 e CA5: teste pytest com citação inventada é detectada | 35 min |

**Marco do Dia 4:** o relatório completo com RAG, com fontes verificáveis.

---

## Dia 5: registro de candidaturas (primeira tarefa a cortar se faltar tempo)

| # | Tarefa | Critério de pronto | Est. |
|---|--------|--------------------|------|
| 5.1 | `tracker.py` com SQLite: adicionar, listar, atualizar status | CA8: adicionar, reiniciar o programa, listar; status atualiza e persiste. Teste pytest | 45 min |
| 5.2 | Comandos de CLI e integração: `analyze` pergunta se deseja registrar; `list`, `status <id> <novo>` | Fluxo completo: analisar → registrar → listar | 30 min |

**Se o tempo apertar:** corte o Dia 5 inteiro. O restante do projeto não depende dele, e ele vira "próximos passos" no README.

---

## Dia 6: avaliação

| # | Tarefa | Critério de pronto | Est. |
|---|--------|--------------------|------|
| 6.1 | Reunir 5 a 10 vagas de teste em `eval/jobs/` (PT e EN, incluindo pelo menos 2 iscas com requisitos ausentes no material) | Arquivos prontos; vagas reais públicas ou resumos delas | 30 min |
| 6.2 | `run_eval.py`: roda cada vaga em `--no-rag` e RAG; confere citações e tecnologias; salva os resultados | Gera tabela com: citações inválidas, tecnologias fora do material, iscas detectadas | 45 min |
| 6.3 | Avaliação manual: nota 0 a 2 de relevância dos trechos por requisito; contar invenções | CA7 e CA10: `eval/results.md` com os números e a comparação RAG × sem RAG. Meta: 0 invenções, relevância média ≥ 1,5 | 30 min |
| 6.4 | Calibrar limiar, top-k e, se preciso, subir o modelo do LLM | Mudanças registradas no resultado, com antes e depois | 15 min |

**Marco do Dia 6:** números que sustentam o projeto, inclusive onde ele falha.

---

## Dia 7: README, demo e acabamento

| # | Tarefa | Critério de pronto | Est. |
|---|--------|--------------------|------|
| 7.1 | README: problema, decisões (inclusive por que a versão sem RAG veio primeiro e por que embeddings locais), como rodar, como a avaliação foi feita, limites e privacidade | Alguém consegue rodar com `.env.example` e o material fictício seguindo só o README | 60 min |
| 7.2 | Demo: terminal gravado ou passo a passo com o material fictício | Demo reproduzível | 20 min |
| 7.3 | Acabamento e checagem final | CA9: clone limpo não contém `.env`, material real nem `*.db`; testes passam; sem arquivos mortos | 20 min |

---

## Resumo de estimativas

| Dia | Foco | Estimativa |
|-----|------|-----------|
| 1 | LLM + extração | 2h00 |
| 2 | Versão sem RAG | 2h20 |
| 3 | Material + embeddings | 2h10 |
| 4 | Busca RAG + citações | 2h00 |
| 5 | Registro de candidaturas (cortável) | 1h15 |
| 6 | Avaliação | 2h00 |
| 7 | README e demo | 1h40 |
| **Total** | | **~13h25** |

O Dia 2 passa um pouco de 2h e o Dia 5 sobra. A folga de um dia compensa a de outro. Se o Dia 5 for cortado, ganho 1h15 para a avaliação ou o acabamento.

---
Próximo passo, depois da sua aprovação: **Passo 4, implementação**, começando pela tarefa 1.1.
