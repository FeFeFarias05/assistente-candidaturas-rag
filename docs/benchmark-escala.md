# Benchmark de escala da busca

Pergunta: a partir de quantos trechos a busca por força bruta (NumPy + SQLite) deixa de bastar e um banco vetorial passa a valer a pena?
Como rodar: `pip install -r requirements-bench.txt && python eval/bench_scale.py` (e `--dificil` para o pior caso).
Números completos: [eval/results_escala.md](../eval/results_escala.md) e [eval/results_escala_dificil.md](../eval/results_escala_dificil.md).

## Método
- Vetores **sintéticos** de 384 dimensões (o tamanho do modelo local), de 1 mil a 200 mil, e consultas vizinhas de itens que existem (como um requisito que tem evidência no material). Lote de **20 consultas**, que é o que uma vaga gera.
- Mede o que uma análise paga: **carregar** o índice do SQLite (com o `load_index()` do próprio projeto) + **buscar** (produto escalar com todos os vetores, top-10).
- Compara com busca aproximada **HNSW** (`hnswlib` e FAISS) e com a busca exata do FAISS. Recall@10 contra a busca exata e **razão de nota** (a nota média dos vizinhos devolvidos dividida pela dos exatos; justa quando há quase-empates).
- Orçamento de referência: **100 ms** só pela busca, para a análise continuar interativa.

## Resultados (dados bem estruturados)

| Trechos | Matriz | Total antes | Total agora, a frio | Total agora, em cache |
|---|---|---|---|---|
| 1 000 | 2 MB | 2,6 ms | 2,1 ms | 0,26 ms |
| 20 000 | 31 MB | 61 ms | 38 ms | 5,7 ms |
| 50 000 | 77 MB | 159 ms | 99 ms | 16 ms |
| 100 000 | 154 MB | 341 ms | 212 ms | 32 ms |
| 200 000 | 307 MB | **822 ms** | 408 ms | **56 ms** |

"Antes" é o projeto como estava (laço em Python relendo o SQLite a cada análise). "A frio" é o carregador novo na primeira análise ou na CLI. "Em cache" é o servidor web já de pé.

## O que isso diz

1. **A busca em si nunca foi o problema.** A busca exata em 200 mil trechos, para as 20 consultas de uma vaga inteira, leva **56 ms**.
2. **O gargalo era reler o SQLite a cada análise:** 766 ms em 200 mil trechos, 14 vezes mais que a busca. Corrigi de duas formas: o carregador novo (sem laço em Python) é 2,2 vezes mais rápido a frio, e o índice agora **fica em memória** e só é relido se o arquivo mudar. Em 200 mil trechos, uma análise com o servidor web de pé foi de 822 ms para 56 ms (14,7 vezes).
3. **Ponto de virada, com o orçamento de 100 ms:** antes, 50 mil trechos; agora, 100 mil a frio, e mais de 200 mil em cache.
4. **Para este projeto, um banco vetorial não se justifica.** Um material pessoal tem de dezenas a poucos milhares de trechos (o corpus de avaliação, com 25 documentos, tem 183). A margem é de **100 vezes ou mais** antes de a busca exata incomodar. Ele passaria a valer com centenas de milhares de trechos, ou com muitos usuários, cada um com o seu índice em memória.

## Busca aproximada: rápida, mas só vale medindo com dados reais

| | hnswlib | FAISS HNSW | Exata (NumPy) |
|---|---|---|---|
| Consulta, 200 mil trechos | 6,1 ms | **1,6 ms** | 56 ms |
| Construção, 200 mil trechos | 54 s | 56 s | 0 |

O HNSW é de 9 a 35 vezes mais rápido na consulta, mas custa **uns 55 segundos para construir** em 200 mil trechos e adiciona uma estrutura a manter e a reconstruir quando o material muda.

**A qualidade depende dos dados, e os dois extremos que medi são muito diferentes:**

| Recall@10 do HNSW (ef=64, sem ajuste) | 20 mil | 100 mil |
|---|---|---|
| Dados bem estruturados (baixa dimensão intrínseca) | 1,00 | 1,00 |
| **Pior caso** (vizinhos quase empatados) | 0,74 a 0,79 | **0,26 a 0,47** (razão de nota 0,84 a 0,89) |

Embeddings reais ficam entre os dois. Por isso **eu não adotaria a busca aproximada sem medir o recall com embeddings reais do material**, e sem ajustar `ef` e `M`, que aqui ficaram nos valores de partida.

## Um erro do meu benchmark, e por que conto
A primeira versão usava dados sem estrutura (grupos isotrópicos nas 384 dimensões) e consultas com ruído de norma ~5 sobre vetores de norma 1. O recall do HNSW saiu **0,33 a 0,83**, o que contradiz a experiência com HNSW. Eram duas falhas minhas: os vizinhos eram quase empatados (diferença de 0,02 entre o 1º e o 10º), então "os 10 mais próximos" era quase um sorteio, e as consultas eram quase aleatórias. Se eu tivesse publicado aquilo, a conclusão sobre HNSW estaria errada. Corrigi os dados, adicionei a razão de nota e mantive a versão antiga como `--dificil`, para os dois extremos ficarem reproduzíveis. Há testes que garantem a diferença entre eles.

## Limitações
- **Dados sintéticos e uma única máquina.** Compare as proporções, não os tempos absolutos. Os tempos variam entre execuções (o "antes" estourou o orçamento em 50 mil trechos numa rodada e em 20 mil na do pior caso).
- A memória do índice HNSW e o custo de reconstruí-lo ao adicionar material **não foram medidos**.
- Mede só a busca: não conta o tempo de embutir as consultas nem de chamar o LLM, que dominam o tempo total de uma análise.
- A busca exata do FAISS foi mais lenta que a do NumPy para lotes de 20 consultas (121 ms contra 56 ms em 200 mil), provavelmente pelo BLAS do NumPy. Não investiguei.
