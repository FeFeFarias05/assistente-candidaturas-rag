# Benchmark de escala da busca (gerado por `eval/bench_scale.py`)

Dados sintéticos DE PIOR CASO (isotrópicos, vizinhos quase empatados), 384 dimensões (como o modelo local), top-10. Consultas: 1 (isolada) e 20 (os requisitos de uma vaga). Tempos em milissegundos (mediana). Máquina: a de quem rodou; compare as proporções, não os valores absolutos.

## Tempo por análise: carregar o índice + buscar

| Trechos (N) | Matriz | Carga antiga | Carga nova, a frio | Carga em cache | Busca exata, 1 consulta | Busca exata, 20 consultas | Total antes | Total agora, a frio | Total agora, em cache |
|---|---|---|---|---|---|---|---|---|---|
| 1 000 | 2 MB | 2.3 | 1.5 | 0.010 | 0.03 | 0.13 | **2.4** | **1.6** | **0.14** |
| 5 000 | 8 MB | 12.1 | 7.7 | 0.010 | 0.06 | 1.05 | **13.2** | **8.7** | **1.06** |
| 20 000 | 31 MB | 96.1 | 35.7 | 0.010 | 0.71 | 6.75 | **102.8** | **42.5** | **6.76** |
| 50 000 | 77 MB | 158.2 | 99.1 | 0.010 | 1.96 | 16.00 | **174.2** | **115.1** | **16.01** |
| 100 000 | 154 MB | 318.6 | 194.8 | 0.010 | 3.78 | 34.58 | **353.1** | **229.3** | **34.58** |

## Busca aproximada (HNSW) × exata

| N | Exata, 20 consultas | hnswlib: consulta / recall@10 / razão de nota / construção | FAISS HNSW: consulta / recall@10 / razão de nota / construção | FAISS exata |
|---|---|---|---|---|
| 1 000 | 0.13 | 2.65 / 1.00 / 1.000 / 0.0 s | 0.29 / 1.00 / 1.000 / 0.1 s | 0.24 |
| 5 000 | 1.05 | 2.87 / 0.93 / 0.994 / 0.3 s | 0.39 / 0.97 / 1.000 / 0.7 s | 0.85 |
| 20 000 | 6.75 | 5.74 / 0.74 / 0.928 / 2.5 s | 0.64 / 0.79 / 0.944 / 1.4 s | 5.72 |
| 50 000 | 16.00 | 5.72 / 0.77 / 0.966 / 8.3 s | 0.97 / 0.70 / 0.964 / 5.8 s | 12.21 |
| 100 000 | 34.58 | 6.17 / 0.26 / 0.844 / 18.1 s | 1.10 / 0.47 / 0.894 / 14.5 s | 42.16 |
Orçamento de referência: 100 ms só pela busca.
- Antes (laço em Python, relendo o SQLite a cada análise): estoura o orçamento a partir de **20 000** trechos.
- Agora, a frio (carregador novo, primeira análise ou CLI): estoura o orçamento a partir de **50 000** trechos.
- Agora, em cache (servidor web de pé): dentro do orçamento até 100 000 trechos.
