# Avaliação de retrieval (gerada por `eval/retrieval_eval.py`)

Corpus fictício: 25 documentos, 183 trechos. Consultas: 108 (64 com evidência no corpus, 44 sem). Só busca, sem LLM.

## Estratégias

| Estratégia | Hit@1 | Hit@3 (IC 95%) | Hit@5 | Precisão@3 | Recall@3 | MRR (IC 95%) | AUC | Abstenção a 90% |
|---|---|---|---|---|---|---|---|---|
| dense | 53% | 70% (59–81%) | 77% | 29% | 62% | 0.63 (0.52–0.73) | 0.89 | 73% |
| bm25 | 70% | 80% (69–89%) | 83% | 36% | 75% | 0.76 (0.65–0.85) | 0.97 | 89% |
| sistema | 67% | 78% (69–88%) | 84% | 34% | 71% | 0.74 (0.64–0.83) | 0.96 | 93% |
| rrf | 66% | 80% (69–89%) | 89% | 35% | 74% | 0.75 (0.65–0.83) | 0.88 | 57% |
| dense_mpnet | 52% | 73% (62–84%) | 80% | 30% | 64% | 0.64 (0.54–0.73) | 0.92 | 84% |
| sistema_mpnet | 64% | 81% (72–91%) | 88% | 35% | 73% | 0.74 (0.65–0.83) | 0.97 | 95% |
| dense_openai | 61% | 84% (75–92%) | 91% | 38% | 79% | 0.73 (0.64–0.81) | 0.91 | 73% |
| sistema_openai | 66% | 86% (77–94%) | 92% | 40% | 82% | 0.76 (0.68–0.85) | 0.98 | 100% |
| rrf_openai | 67% | 84% (75–92%) | 89% | 38% | 79% | 0.77 (0.67–0.85) | 0.90 | 45% |

## Comparações pareadas (consulta a consulta)

| A contra B | ΔHit@3 (IC 95%) | ΔMRR (IC 95%) | Conclusão |
|---|---|---|---|
| sistema contra dense | +8 pp (+2 a +14) | +0.11 (+0.05 a +0.18) | A melhor |
| sistema contra bm25 | -2 pp (-11 a +9) | -0.02 (-0.12 a +0.08) | inconclusivo |
| rrf contra sistema | +2 pp (-3 a +6) | +0.01 (-0.07 a +0.09) | inconclusivo |
| sistema_mpnet contra sistema | +3 pp (-3 a +11) | +0.00 (-0.06 a +0.06) | inconclusivo |
| sistema_openai contra sistema | +8 pp (-2 a +17) | +0.03 (-0.07 a +0.12) | inconclusivo |
| sistema_openai contra sistema_mpnet | +5 pp (-6 a +16) | +0.03 (-0.05 a +0.11) | inconclusivo |

## Hit@3 por tipo de requisito

| Estratégia | Tecnologias | Responsabilidades e outros |
|---|---|---|
| dense | 83% | 60% |
| bm25 | 100% | 63% |
| sistema | 100% | 60% |
| rrf | 100% | 63% |
| dense_mpnet | 83% | 66% |
| sistema_mpnet | 100% | 66% |
| dense_openai | 93% | 77% |
| sistema_openai | 97% | 77% |
| rrf_openai | 100% | 71% |

## Tamanho do trecho (caracteres)

| Tamanho | Estratégia | Trechos | Hit@3 | Precisão@3 | MRR | AUC |
|---|---|---|---|---|---|---|
| 250 | dense | 309 | 62% | 26% | 0.57 | 0.90 |
| 250 | sistema | 309 | 72% | 32% | 0.69 | 0.96 |
| 450 | dense | 183 | 70% | 29% | 0.63 | 0.89 |
| 450 | sistema | 183 | 78% | 34% | 0.73 | 0.96 |
| 700 | dense | 115 | 70% | 27% | 0.60 | 0.88 |
| 700 | sistema | 115 | 78% | 33% | 0.72 | 0.95 |

Como ler:
- **Hit@K**: em quantas consultas com evidência existe ao menos um trecho relevante entre os K primeiros.
- **Precisão@K / Recall@K**: fração dos K primeiros que é relevante / fração dos relevantes que foi recuperada. O Recall@K fica baixo por definição quando há muitos trechos relevantes (ex.: "Git" aparece em vários).
- **MRR**: média de 1/posição do primeiro trecho relevante.
- **AUC**: chance de a nota do melhor trecho de uma consulta COM evidência superar a de uma consulta SEM. 0,5 = não separa; 1,0 = separa perfeitamente. Mede se dá para escolher um limiar de "sem evidência".
- **Abstenção a 90%**: com o limiar que mantém 90% das consultas com evidência, quantas das sem evidência ficam de fora.
- IC 95%: bootstrap sobre as consultas (2000 reamostragens). Comparar dois ICs lado a lado é conservador demais: por isso as comparações pareadas olham a diferença consulta a consulta. "inconclusivo" = o IC da diferença inclui zero.
