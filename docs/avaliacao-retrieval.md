# Avaliação de retrieval

Pergunta: dado um requisito de vaga, o sistema encontra o trecho do material que o comprova, e sabe dizer quando não existe nenhum?
Como rodar: `python eval/retrieval_eval.py --openai --mpnet` (só busca, sem LLM; `--openai` gasta centavos).
Números completos: [eval/results_retrieval.md](../eval/results_retrieval.md).

## Método

- **Corpus fictício de 25 documentos** (183 trechos, 62 mil caracteres), gerado por LLM a partir de **fatos plantados palavra por palavra** e de uma lista de termos proibidos. Um validador confere por código, para cada documento, que os fatos estão lá e que nenhum termo proibido apareceu; Docker, Redux e GraphQL só existem como negação, nos documentos certos (`tests/test_corpus.py`). Assim o gabarito é correto por construção.
- **108 consultas** escritas como os requisitos de uma vaga: **64 com evidência** no corpus (tecnologias e responsabilidades), **4 negadas** ("Não usei Docker") e **44 sem evidência nenhuma** (C#, Kubernetes, banco vetorial, fine-tuning...).
- **Relevância por texto, não por id:** um trecho é relevante se contém alguma frase de evidência do gabarito. Assim o gabarito sobrevive a mudanças no chunking.
- **Métricas:** Hit@K (existe um relevante entre os K primeiros), Precisão@K, Recall@K, MRR, e **AUC de abstenção** (o quanto a nota do melhor trecho separa uma consulta com evidência de uma sem). Intervalos de confiança de 95% por bootstrap, e **comparações pareadas**, consulta a consulta.
- **Estratégias:** `dense` (só semântica), `bm25` (só palavras-chave, implementado sem dependências), `sistema` (o que o projeto faz: semântica + bônus de termo literal e de idioma), `rrf` (fusão por posição de dense + bm25), e variantes com um modelo local maior (`mpnet`, ~1 GB) e com embeddings da OpenAI.

## Resultados

| Estratégia | Hit@3 (IC 95%) | MRR | AUC | Abstenção a 90% |
|---|---|---|---|---|
| dense (MiniLM local) | 70% (59 a 81) | 0,63 | 0,89 | 73% |
| bm25 | 80% (69 a 89) | 0,76 | 0,97 | 89% |
| **sistema** (híbrido, MiniLM) | 78% (69 a 88) | 0,74 | 0,96 | 93% |
| rrf | 80% (69 a 89) | 0,75 | 0,88 | 57% |
| sistema com mpnet (local, maior) | 81% (72 a 91) | 0,74 | 0,97 | 95% |
| sistema com OpenAI | 86% (77 a 94) | 0,76 | 0,98 | 100% |

"Abstenção a 90%": com o limiar que mantém 90% das consultas com evidência, quantas das sem evidência ficam de fora.

### O que as comparações pareadas permitem afirmar

| A contra B | ΔHit@3 (IC 95%) | Conclusão |
|---|---|---|
| sistema contra dense | **+8 pp (+2 a +14)** | **A híbrida é melhor, com diferença real** (MRR +0,11) |
| sistema contra bm25 | −2 pp (−11 a +9) | inconclusivo |
| rrf contra sistema | +2 pp (−3 a +6) | inconclusivo |
| sistema_mpnet contra sistema | +3 pp (−3 a +11) | inconclusivo |
| sistema_openai contra sistema | +8 pp (−2 a +17) | inconclusivo (tendência positiva) |

**A única conclusão firme é que a busca híbrida supera a busca só semântica.** O bônus de termo literal elevou o acerto em tecnologias de 83% para 100%.
Todo o resto é inconclusivo com 64 consultas: não posso dizer que embeddings da OpenAI ou um modelo local maior sejam melhores, só que a tendência aponta para cima e que seriam necessárias mais consultas para decidir.

### Por tipo de requisito (Hit@3)

| Estratégia | Tecnologias | Responsabilidades e outros |
|---|---|---|
| dense | 83% | 60% |
| bm25 | 100% | 63% |
| sistema | 100% | 60% |
| sistema com mpnet | 100% | 66% |
| sistema com OpenAI | 97% | 77% |

Tecnologias estão resolvidas pela busca por termo. **O ponto fraco de todas as estratégias locais são os requisitos que não são nome de tecnologia** (60 a 66%), por exemplo "Construção de pipelines RAG" ou "Visualização de dados". A OpenAI chegou a 77%, mas pela comparação pareada isso ainda é tendência.

## O que eu mudei por causa da avaliação

1. **Defeito de chunking, achado na auditoria das falhas.** 18 trechos (9%) eram só um título (`# Open source contribution ## Overview`) e 79 (39%) terminavam com um título pendurado. Títulos soltos ganhavam notas altas só por dividirem palavras com a consulta. Corrigi: o título agora acompanha o texto que vem depois. O índice passou a guardar a versão do chunking e se refaz sozinho quando ela muda, para um índice antigo não ficar com trechos velhos sem aviso.
   **Efeito medido: pequeno e inconclusivo.** Hit@3 do sistema 80% para 78% (dentro do ruído); Hit@1 da busca semântica de 45% para 53%; abstenção de 64% para 73%. O mecanismo é correto, mas eu não consigo afirmar um ganho.
2. **Tamanho do trecho:** com 250 caracteres o Hit@3 do sistema foi 72%; com 450 e com 700, 78% nos dois. Fica em 450: não pior que 700, com mais trechos e menos risco de truncar no limite de ~128 tokens do modelo local.

## O que **não** mudei, e por quê
- **Não adotei a fusão por posição (RRF).** Ela não melhorou o Hit@3 e **destrói a escala absoluta da nota**: o AUC caiu de 0,96 para 0,88 e a abstenção de 93% para 57%. Para dizer "não há evidência" é preciso uma nota com significado absoluto, e a fusão por posição joga isso fora.
- **Não troquei os embeddings locais pelos da OpenAI.** O ganho não é conclusivo, e o ganho em privacidade dos embeddings locais é certo.

## Auditoria das falhas
Das 13 consultas com evidência em que o sistema errou o Hit@3, li uma a uma:
- **3 a 5 são acertos semânticos que o meu gabarito estrito não reconhece:** a busca trouxe trechos do **documento certo** (ex.: "Inglês avançado" devolveu três trechos do documento sobre inglês), só não o trecho exato com a frase. Isso significa que o Hit@3 real é um pouco maior que o medido.
- **Cerca de 8 são falhas reais:** o modelo local não liga "pipelines RAG" ao documento sobre embeddings e busca semântica, e confunde "APIs de LLM (OpenAI)" com o documento de autenticação de APIs.

## Limitações (importantes)
- **O corpus é fictício e gerado por LLM, e as consultas e os fatos foram escritos por mim.** Há viés de autor: as frases plantadas têm vocabulário distintivo, o que favorece a busca por palavras-chave. É provável que o empate do BM25 com a híbrida seja efeito disso, e **não permite concluir que BM25 bastaria com material real**, onde as vagas parafraseiam.
- **64 consultas com evidência:** os intervalos de confiança são largos, e por isso quase todas as comparações saíram inconclusivas.
- **Gabarito por frase é estrito:** subestima as estratégias semânticas (ver auditoria).
- **Mede se a busca funciona, não se funciona bem no seu currículo.** Para isso seria preciso rotular consultas sobre o seu material real.
- **Uma execução.** A busca é determinística, mas o corpus foi gerado uma vez.
