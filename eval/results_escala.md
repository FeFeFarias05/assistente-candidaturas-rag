# Benchmark de escala da busca (gerado por `eval/bench_scale.py`)

Dados sintéticos com clusters, 384 dimensões (como o modelo local), top-10. Consultas: 1 (isolada) e 20 (os requisitos de uma vaga). Tempos em milissegundos (mediana). Máquina: a de quem rodou; compare as proporções, não os valores absolutos.

## Tempo por análise: carregar o índice + buscar

| Trechos (N) | Matriz | Carga antiga | Carga nova, a frio | Carga em cache | Busca exata, 1 consulta | Busca exata, 20 consultas | Total antes | Total agora, a frio | Total agora, em cache |
|---|---|---|---|---|---|---|---|---|---|
| 1 000 | 2 MB | 2.3 | 1.9 | 0.010 | 0.03 | 0.25 | **2.6** | **2.1** | **0.26** |
| 5 000 | 8 MB | 12.5 | 7.6 | 0.010 | 0.05 | 1.22 | **13.7** | **8.8** | **1.23** |
| 20 000 | 31 MB | 55.0 | 32.4 | 0.010 | 0.56 | 5.69 | **60.6** | **38.1** | **5.70** |
| 50 000 | 77 MB | 142.4 | 82.6 | 0.010 | 1.39 | 16.19 | **158.6** | **98.8** | **16.20** |
| 100 000 | 154 MB | 308.9 | 180.5 | 0.010 | 3.57 | 31.90 | **340.8** | **212.4** | **31.91** |
| 200 000 | 307 MB | 765.8 | 351.7 | 0.010 | 7.29 | 56.12 | **821.9** | **407.8** | **56.13** |

## Busca aproximada (HNSW) × exata

| N | Exata, 20 consultas | hnswlib: consulta / recall@10 / razão de nota / construção | FAISS HNSW: consulta / recall@10 / razão de nota / construção | FAISS exata |
|---|---|---|---|---|
| 1 000 | 0.25 | 2.89 / 1.00 / 1.000 / 0.1 s | 0.29 / 1.00 / 1.000 / 0.1 s | 0.41 |
| 5 000 | 1.22 | 3.01 / 1.00 / 1.000 / 0.3 s | 0.33 / 1.00 / 1.000 / 0.8 s | 1.41 |
| 20 000 | 5.69 | 5.08 / 1.00 / 1.000 / 2.9 s | 0.51 / 1.00 / 1.000 / 1.6 s | 3.49 |
| 50 000 | 16.19 | 6.13 / 1.00 / 1.000 / 8.4 s | 1.22 / 1.00 / 1.000 / 8.2 s | 21.82 |
| 100 000 | 31.90 | 6.41 / 1.00 / 1.000 / 23.5 s | 1.48 / 1.00 / 1.000 / 28.4 s | 45.59 |
| 200 000 | 56.12 | 6.12 / 1.00 / 1.000 / 54.0 s | 1.63 / 1.00 / 1.000 / 56.1 s | 120.92 |
Orçamento de referência: 100 ms só pela busca.
- Antes (laço em Python, relendo o SQLite a cada análise): estoura o orçamento a partir de **50 000** trechos.
- Agora, a frio (carregador novo, primeira análise ou CLI): estoura o orçamento a partir de **100 000** trechos.
- Agora, em cache (servidor web de pé): dentro do orçamento até 200 000 trechos.
