# API de autenticação

## Visão geral

Este projeto foi um estudo prático sobre segurança de APIs, feito por mim para entender como proteger rotas, controlar acesso e tratar credenciais de forma mais segura. Eu quis sair da teoria e montar uma API pequena, mas completa o suficiente para testar cadastro, login e acesso a recursos protegidos. O foco foi aprender o fluxo de autenticação e enxergar onde erros simples podem comprometer toda a aplicação.

## O que eu fiz

Implementei autenticação com tokens JWT em Node.js com Express. Guardei os usuários em MongoDB. Documentei cada endpoint com exemplos de requisição e resposta. No total, construí três rotas principais para cadastro, login e consulta de perfil, além de rotas protegidas que só respondem quando o token é enviado corretamente.

Também organizei regras básicas de validação para nome, e-mail e senha, evitando entradas vazias e duplicadas. No login, conferi as credenciais antes de gerar o token e defini tempo de expiração para reduzir o risco de uso indevido. Durante a implementação, testei os fluxos com diferentes combinações de dados para confirmar os retornos esperados.

## Resultados

O projeto ficou funcional em cerca de duas semanas de estudo e prática, com testes manuais em todos os endpoints. Consegui validar três cenários principais:

- cadastro com novo usuário e retorno de confirmação;
- login com emissão de token válido;
- acesso negado quando o token está ausente ou expirado.

A documentação também ajudou a simular chamadas corretas e incorretas sem depender de tentativa e erro. No fim, fiquei com uma base reutilizável para futuros projetos que precisem de controle de acesso.

## Desafios e aprendizados

O maior desafio foi entender como lidar com autenticação sem expor informações sensíveis. No início, eu cometi erros na validação do token e nas mensagens de resposta, o que me fez revisar o fluxo inteiro. Outro ponto foi pensar na experiência de quem consome a API, porque uma resposta vaga dificulta a integração.

Aprendi que segurança não depende só de gerar token, mas de definir regras claras para entrada, saída e tratamento de falhas. Também percebi que documentação curta e objetiva reduz retrabalho. Esse projeto me ajudou a consolidar conceitos de autenticação, organização de rotas e cuidado com dados de usuários.
