# Avaliação de fundamentação (gerada por `eval/grounding_eval.py`)

Relatórios gerados com `gpt-5.4-mini`; afirmações julgadas por `gpt-5.5`. Corpus fictício de 25 documentos; 6 vagas. Uma afirmação é um item de Pontos fortes, de O que destacar, ou uma linha do rascunho. As taxas valem para as afirmações **com citação**; as sem citação aparecem à parte.

## Resultado

| Modo | Citadas | Sustentada (IC 95%) | Parcial | Não sustentada | Linhas sem citação |
|---|---|---|---|---|---|
| Material inteiro (sem busca) | 109 de 114 | 83% (75% a 89%) | 17% (11% a 25%) | 0% (0% a 3%) | 4% |
| RAG (só os trechos recuperados) | 108 de 108 | 80% (71% a 86%) | 20% (14% a 29%) | 0% (0% a 3%) | 0% |

Diferença na taxa sustentada, RAG menos material inteiro: **-4 pp** (IC 95%: -14 a +6). O intervalo inclui zero: inconclusivo.

## Por seção

| Modo | Seção | Citadas | Sustentada | Parcial | Não sustentada | Sem citação |
|---|---|---|---|---|---|---|
| full | Pontos fortes | 60 de 60 | 80% | 20% | 0% | 0% |
| full | O que destacar no currículo | 37 de 37 | 97% | 3% | 0% | 0% |
| full | Rascunho de mensagem | 12 de 17 | 58% | 42% | 0% | 29% |
| rag | Pontos fortes | 56 de 56 | 79% | 21% | 0% | 0% |
| rag | O que destacar no currículo | 36 de 36 | 94% | 6% | 0% | 0% |
| rag | Rascunho de mensagem | 16 de 16 | 50% | 50% | 0% | 0% |

## Checagem cruzada com a regra determinística

Em 138 afirmações que citam uma tecnologia da vaga, o juiz concordou com a regra "o termo aparece na evidência" em 99% dos casos (juiz aprovou sem o termo na evidência: 2; juiz reprovou com o termo presente: 0).

## Afirmações não sustentadas

Nenhuma afirmação com citação foi considerada não sustentada.

## Exemplos de afirmações parciais

- (rag, 01_ai_intern_pt) Avaliar a qualidade das respostas com conjuntos de perguntas e métricas: a candidata organizou um conjunto de teste com perguntas reais, ava: _Sustenta perguntas, 30 rotuladas e revisão manual, mas não menciona métricas._
- (rag, 01_ai_intern_pt) Documentar os experimentos e os resultados: a candidata registrou o trabalho “desde a preparação dos documentos até a avaliação dos resultad: _Descreve resultados com 30 perguntas, mas não afirma claramente que documentou/registrou o trabalho._
- (rag, 01_ai_intern_pt) Formação em Engenharia de Software e monitoria voluntária em Algoritmos e Estruturas de Dados por dois semestres.: _Confirma estudante e monitoria por dois semestres, mas não formação concluída._
- (rag, 01_ai_intern_pt) Olá, estou me candidatando à vaga de Estagiário(a) em IA Generativa. Tenho experiência em projetos com Python, incluindo uma API REST com Fl: _Confirma projetos Python, mas não candidatura à vaga de Estagiário em IA Generativa._
- (rag, 01_ai_intern_pt) Além disso, avaliei esse sistema com 30 perguntas rotuladas à mão e organizei a revisão manual das respostas.: _Confirma avaliação com 30 perguntas, mas não revisão manual nesta evidência._
- (rag, 02_ml_engineer_jr_en) Python: a candidata desenvolveu uma API REST em Python com Flask e também escreveu um scraper em Python.: _A evidência apoia API REST em Python/Flask, mas não menciona scraper._
