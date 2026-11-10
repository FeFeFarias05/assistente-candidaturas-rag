# Assistente de perguntas sobre documentos

## Visão geral

Este foi um projeto pessoal que desenvolvi em 2026 para criar um assistente de perguntas e respostas sobre documentos. A ideia surgiu quando percebi que eu perdia tempo procurando informações em textos longos de estudo e de trabalho acadêmico. Quis construir algo simples, mas útil, para localizar trechos relevantes e responder perguntas com base neles. Como estudante de Engenharia de Software, eu queria praticar etapas completas de um projeto, desde a preparação dos documentos até a avaliação dos resultados.

## O que eu fiz

Dividi os documentos em trechos de cerca de 500 caracteres para facilitar a recuperação de contexto. Depois, gerei embeddings e implementei busca semântica por similaridade de cosseno. Em seguida, integrei a API da OpenAI para gerar respostas a partir de trechos de documentos. Também organizei um conjunto de teste com perguntas reais que eu poderia fazer sobre os textos. Para controlar a qualidade do sistema, eu revisei manualmente as respostas esperadas e ajustei o fluxo quando percebi que alguns trechos estavam muito curtos ou muito parecidos entre si.

## Resultados

Avaliei as respostas com um conjunto de 30 perguntas rotuladas à mão. Em perguntas diretas, o assistente respondeu de forma consistente e encontrou o trecho correto na maior parte dos casos. O sistema funcionou melhor quando a pergunta citava um tema específico do documento e pior quando a informação estava espalhada em mais de um trecho. Nos testes, eu notei que a recuperação dos trechos foi mais importante do que a formulação da resposta em si. Depois de alguns ajustes na divisão dos documentos, consegui reduzir respostas genéricas e melhorar a precisão em consultas mais longas.

## Desafios e aprendizados

O principal desafio foi equilibrar tamanho do trecho e contexto suficiente. Quando os trechos eram grandes demais, a busca trazia resultados menos precisos; quando eram pequenos demais, faltava informação para responder bem. Outro ponto difícil foi montar perguntas de avaliação que realmente cobrissessem casos variados, e não só exemplos óbvios. Aprendi que projetos de perguntas e respostas dependem muito da qualidade da preparação dos documentos e da definição clara do teste. Também entendi melhor como pequenas decisões de pré-processamento afetam o resultado final do sistema.
