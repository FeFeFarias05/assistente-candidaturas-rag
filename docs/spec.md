# Especificação: Assistente de Candidaturas (LLM + RAG)

Status: **v2, atualizada com as respostas; aguardando aprovação**

## 1. Objetivo
Dada a descrição de uma vaga, o sistema extrai os requisitos, busca no meu material pessoal os trechos relevantes (RAG) e devolve uma análise de aderência com rascunhos. Também registra a candidatura. É um projeto de portfólio para vaga de AI Engineer e uma ferramenta de uso real.

## 2. Usuária
Uma só pessoa (eu), estudante de Engenharia de Software, que se candidata a várias vagas e quer respostas consistentes, fundamentadas no que de fato fez. Não há multiusuário, login nem deploy.

## 3. Decisões já tomadas
- Python, interface de terminal (CLI). A interface web fica para depois, fora desta spec.
- LLM e embeddings via API da OpenAI.
- Prazo: 7 dias, ~2h/dia.
- Idioma: material e vagas em português e inglês (misturados). Relatório em português, mantendo termos técnicos em inglês.
- Formato do material: PDF (currículo e demais documentos) e também `.md`/`.txt`. Extração de PDF com uma biblioteca leve (ex.: `pypdf`).
- Material no repositório e na demo: **fictício**. O material real fica só local e fora do Git.
- Privacidade e embeddings: a escolha de embeddings via API é **provisória**. Como o material real é sensível, os embeddings devem poder ser trocados por um modelo local sem mudar o resto do código. A decisão final e o trade-off ficam para o `plan.md`. O LLM continua sendo a API da OpenAI.
- Registro de candidaturas: SQLite (stdlib).
- Idioma do relatório: rascunhos de mensagem/resposta seguem o idioma da vaga (detectado); o restante fica em português. Opção `--lang` força outro idioma.
- Embeddings: **locais por padrão** (aprovado), OpenAI como alternativa via `.env`. Material fictício obrigatório na versão sem RAG (Dia 2), que envia o currículo inteiro à API.

## 4. Requisitos funcionais
| ID | Requisito |
|----|-----------|
| RF1 | Receber o texto de uma vaga (colado no terminal ou lido de arquivo `.txt`). |
| RF2 | Extrair da vaga, em JSON estruturado: título, empresa (se houver), tecnologias, responsabilidades, nível/senioridade, requisitos obrigatórios vs. desejáveis. Campo ausente na vaga = `null`, nunca chutado. |
| RF3 | Indexar meu material pessoal (arquivos `.pdf`, `.md`, `.txt` em uma pasta, em português ou inglês): currículo, projetos, experiências, respostas anteriores. |
| RF4 | Para cada requisito da vaga, recuperar os trechos mais relevantes do material (top-k) com a fonte (arquivo + trecho). |
| RF5 | Gerar o relatório: resumo da vaga, pontos fortes, lacunas, sugestões de destaque no currículo, rascunho de mensagem/resposta. |
| RF6 | Toda afirmação sobre meu perfil no relatório cita a fonte (arquivo e trecho). |
| RF7 | Quando o material não cobre um requisito, o relatório diz explicitamente "sem evidência no material" e o lista em lacunas. |
| RF8 | Registrar candidatura: vaga, empresa, data, status (`interessada`, `candidatei`, `entrevista`, `recusada`, `oferta`). Listar e atualizar status. |
| RF9 | Salvar cada relatório gerado em arquivo local para eu revisar e editar. |

## 5. Requisitos não funcionais
- **RNF1 Honestidade:** o sistema nunca afirma experiência, tecnologia ou resultado ausente do material.
- **RNF2 Autoria:** todo rascunho sai marcado como "RASCUNHO, revisar antes de usar". O sistema não envia nada a ninguém.
- **RNF3 Privacidade:** dados pessoais e chaves ficam fora do repositório. `.env` e a pasta de material no `.gitignore`; `.env.example` e um material de exemplo fictício versionados.
- **RNF4 Simplicidade:** poucas dependências, código legível, sem framework de agentes e sem banco vetorial pesado.
- **RNF5 Reprodutibilidade:** temperatura baixa nas etapas de extração; qualquer pessoa roda o projeto com `.env.example` + material de exemplo.
- **RNF6 Desempenho:** uma análise completa em menos de ~60s (uma vaga, material de até ~50 páginas).
- **RNF7 Custo:** uma análise custa centavos; o índice só é recalculado quando o material muda.

## 6. Critérios de aceite (testáveis)
1. **CA1:** colar 3 vagas reais de teste produz JSON válido nos campos de RF2, e cada tecnologia listada aparece literalmente no texto da vaga.
2. **CA2:** uma vaga sem salário/senioridade/empresa devolve `null` nesses campos, não valores inventados.
3. **CA3:** em 100% das afirmações sobre meu perfil no relatório há uma citação `[arquivo#trecho]` que existe de fato no material (checagem automática: a citação aponta para um chunk real).
4. **CA4:** teste "isca": uma vaga que exige uma tecnologia que sei que **não** está no meu material (ex.: Kubernetes) deve aparecer em lacunas e **não** em pontos fortes.
5. **CA5:** teste "isca 2": nenhuma tecnologia citada como ponto forte existe fora do material (checagem por busca de texto).
6. **CA6:** com material vazio ou irrelevante, o sistema diz que não há informação suficiente em vez de gerar o relatório.
7. **CA7:** avaliação com 5 a 10 vagas: relatório manual de relevância dos trechos (nota 0 a 2 por requisito) e contagem de invenções. Meta: **0 invenções** e relevância média ≥ 1,5.
8. **CA8:** registrar uma candidatura, reiniciar o programa e listá-la; atualizar o status persiste.
9. **CA9:** `git status` num clone limpo após rodar tudo não mostra `.env`, material pessoal nem índice.
10. **CA10:** versão sem RAG (currículo inteiro no prompt) e versão com RAG rodam sobre as mesmas vagas, e a comparação fica documentada no README.

## 7. Fora de escopo
- Interface web (fase posterior, depois do MVP em terminal).
- Envio automático de candidaturas ou mensagens.
- Scraping de sites de vagas; a vaga é sempre colada por mim.
- Geração de currículo final em PDF, multiusuário, autenticação, deploy.
- Fine-tuning, agentes autônomos, re-ranking com modelos extras.
- DOCX e PDFs escaneados (imagem, exigem OCR). Só PDF com texto selecionável.

## 8. Riscos
| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| LLM inventa experiência | Quebra a regra principal | Prompt restritivo, citação obrigatória, validação automática das citações (CA3), testes isca (CA4/CA5) |
| Material pessoal enviado à API da OpenAI (embeddings e LLM) | Privacidade | Embeddings trocáveis por modelo local (decisão no plan.md); não indexar dados sensíveis (CPF, endereço, telefone); documentar no README o que sai da máquina (os trechos recuperados ainda vão no prompt do LLM) |
| PDF com extração ruim (colunas, tabelas, texto fora de ordem) | Chunks ruins | Testar com o PDF real cedo (Dia 3); fallback: converter para `.md` |
| Chunking ruim, busca irrelevante | Relatório fraco | Chunking por seção/título, avaliação no Dia 6, comparação com a versão sem RAG |
| Material pessoal pequeno demais para o RAG fazer diferença | Comparação RAG × sem RAG pouco conclusiva | Criar material de exemplo maior; ser honesta no README sobre o limite |
| Estouro de prazo | Projeto incompleto | Dia 5 (registro de candidaturas) é o primeiro a cortar; MVP funciona sem ele |
| Vazamento de chave ou dados no Git | Segurança | `.gitignore` desde o primeiro commit, `.env.example`, checagem CA9 |
| Vagas em idiomas diferentes do material | Busca pior | Embeddings multilíngues da OpenAI lidam bem; testar vaga em inglês na avaliação |
| Custo da API | Baixo | Cache do índice, modelos pequenos |

## 9. Perguntas resolvidas
1. Idioma: português e inglês. Relatório em português.
2. Formato: PDF (com texto selecionável) além de `.md`/`.txt`.
3. Material de exemplo: fictício no repositório, real só local.
4. Privacidade: embeddings locais devem ser uma opção; decisão no `plan.md`.
5. Registro de candidaturas: SQLite.

## 10. Pergunta em aberto
- Nenhuma bloqueante. Confirmando a spec, abordo a escolha embeddings local × API no plano, com opções e recomendação.

---
Próximo passo, depois da sua aprovação: `plan.md`.
