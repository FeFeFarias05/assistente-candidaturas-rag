# Segurança em aplicações web

## Visão geral

Eu desenvolvi este projeto como parte de um estudo guiado sobre vulnerabilidades comuns em aplicações web, com foco em entender como falhas simples podem expor dados e comprometer ações do usuário. O trabalho foi feito em 2 semanas, com revisões curtas ao fim de cada sessão para registrar o que eu tinha observado e corrigido. O objetivo principal foi identificar pontos frágeis em formulários e exibição de conteúdo, testar cenários de ataque controlados e documentar as medidas adotadas para reduzir o risco.

## O que eu fiz

Durante o estudo, eu analisei fluxos de cadastro, login e pesquisa, simulando entradas maliciosas e verificando o comportamento da aplicação. Estudei XSS e SQL injection e apliquei validação de entrada. Em seguida, revisei trechos de saída renderizada para impedir que conteúdo enviado pelo usuário fosse interpretado como código. Escapei a saída para evitar injeção de HTML. Também criei uma lista de checagem com 8 itens para repetir os testes de forma consistente, incluindo campos obrigatórios, tamanho máximo, caracteres especiais e mensagens de erro.

## Resultados

Ao final, consegui reproduzir 3 cenários de vulnerabilidade e corrigi-los com regras objetivas de validação e tratamento de saída. O principal resultado foi reduzir a exposição a entradas não confiáveis e deixar mais claro onde o sistema precisava de proteção extra. Além disso, organizei um resumo com os casos testados, o efeito esperado e a correção aplicada, o que facilitou a revisão posterior.

## Desafios e aprendizados

O maior desafio foi diferenciar correções que apenas ocultavam o problema daquelas que realmente impediam a falha. Em alguns testes, uma validação parcial ainda permitia variações do mesmo ataque, então precisei refazer o cenário 4 vezes até chegar a uma regra mais consistente. Aprendi que segurança web não depende só de bloquear caracteres específicos, mas de tratar entrada e saída de forma separada e previsível. Também percebi que documentar cada teste me ajudou a não repetir erros e a entender melhor o impacto de decisões simples no comportamento da aplicação.
