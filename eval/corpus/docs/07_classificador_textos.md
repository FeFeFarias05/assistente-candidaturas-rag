# Classificador de textos

## Visão geral

Eu desenvolvi este projeto como parte de um trabalho de introdução a aprendizado de máquina na graduação em Engenharia de Software. A proposta foi criar um classificador de textos capaz de separar mensagens curtas em categorias pré-definidas, usando um conjunto pequeno de exemplos rotulados. Eu quis entender o fluxo completo, desde a preparação dos dados até a avaliação do modelo, sem depender de uma solução pronta.

O trabalho foi feito em cerca de duas semanas, com foco em experimentar métodos simples e interpretar os resultados. Meu objetivo principal era comparar abordagens básicas e verificar como a escolha dos parâmetros afetava o desempenho.

## O que eu fiz

Primeiro, limpei os textos removendo pontuação, normalizando letras maiúsculas e minúsculas e descartando exemplos muito curtos. Depois, separei os dados em treino e teste para evitar que o modelo fosse avaliado com exemplos que já tinha visto.

- Treinei um classificador de textos com scikit-learn
- Usei validação cruzada para comparar os modelos
- Ajustei a representação dos textos e testei configurações diferentes

Também revisei manualmente uma amostra dos erros para entender se o problema vinha do vocabulário, de classes parecidas ou de textos ambíguos. Isso me ajudou a decidir quais configurações valiam a pena manter.

## Resultados

No conjunto de teste separado, o modelo final ficou com precisão de 0,81 e recall de 0,78. O resultado foi melhor do que a primeira versão, que tinha desempenho instável quando eu mudava a divisão dos dados. A validação cruzada mostrou que uma configuração mais simples era mais consistente do que uma versão com muitos ajustes.

- precisão e recall ficaram equilibrados para a maioria das classes
- os erros aumentaram em textos curtos
- classes com poucas amostras tiveram pior desempenho

Medi precisão e recall em um conjunto de teste separado

## Desafios e aprendizados

O maior desafio foi lidar com a quantidade limitada de exemplos. Como o conjunto era pequeno, qualquer decisão errada na preparação dos dados influenciava bastante o resultado. Eu também percebi que algumas classes tinham linguagem muito parecida, o que confundia o classificador.

Aprendi que, em aprendizado de máquina, a qualidade dos dados pesa tanto quanto o modelo escolhido. Também entendi melhor a importância de separar treino e teste com cuidado e de analisar métricas além da acurácia. No fim, esse projeto me deu prática com experimentação, leitura de resultados e revisão de erros de forma objetiva.
