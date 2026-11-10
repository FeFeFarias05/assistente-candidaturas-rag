# Jogo com Canvas

## Visão geral

Este foi um projeto de fim de semana para praticar JavaScript. A ideia era criar um jogo simples, jogável no navegador, usando apenas uma área de desenho e lógica escrita por mim. Eu queria revisar conceitos básicos como eventos, atualização de estado e renderização em tempo real, sem depender de uma estrutura pronta.

Criei um jogo com JavaScript e Canvas. Nele, o jogador controla um personagem que se move pela tela para desviar de obstáculos e coletar pontos. O objetivo principal era manter a mecânica direta, mas ainda assim construir algo completo o bastante para ter começo, meio e fim em poucas horas de trabalho.

## O que eu fiz

Eu organizei o projeto em partes menores para conseguir avançar no sábado à tarde e terminar no domingo. Primeiro defini a movimentação do personagem e o ciclo principal do jogo. Depois ajustei a lógica de surgimento dos obstáculos e a atualização da tela em intervalos regulares.

Implementei a detecção de colisão e a pontuação. Também criei uma condição de fim de jogo e um botão simples para reiniciar a partida sem recarregar a página. Durante o desenvolvimento, deixei o código separado em funções curtas para facilitar testes e ajustes rápidos.

Além disso, revisei valores como velocidade, tamanho dos objetos e frequência de aparecimento. Fiz alguns testes com sessões de 5 a 10 minutos para verificar se o jogo ficava jogável e se a dificuldade aumentava de forma gradual.

## Resultados

No final do fim de semana, consegui uma versão funcional e estável para uso local. O jogo respondia bem aos comandos, atualizava a pontuação corretamente e encerrava a partida quando havia colisão. Também consegui reduzir um problema de movimento “travado” que aparecia quando eu pressionava teclas em sequência.

O resultado final foi um projeto pequeno, mas completo o bastante para mostrar o fluxo principal de um jogo simples. Para mim, o mais importante foi ver que eu consegui sair de uma ideia inicial e chegar a uma versão utilizável em cerca de dois dias.

## Desafios e aprendizados

O maior desafio foi lidar com a sincronização entre movimento, colisão e atualização visual. Em alguns momentos, a colisão acontecia com atraso de um quadro, o que exigiu ajustes na ordem das verificações. Eu também precisei testar várias configurações para que a pontuação não subisse rápido demais.

Aprendi que dividir o problema em etapas curtas me ajudou a manter o foco e a corrigir erros com mais rapidez. Também percebi que projetos pequenos são úteis para reforçar fundamentos, porque exigem decisões simples, mas bem executadas.
