# Análise de dados de vendas

## Visão geral

Este projeto foi feito em conjunto nas disciplinas de Banco de Dados e Estatística, com foco em analisar um conjunto de vendas de uma pequena loja ao longo de um semestre. Eu, Ana, organizei o trabalho para responder perguntas simples e úteis, como quais meses venderam mais, quais categorias tiveram maior saída e se havia padrões semanais. O objetivo não era só calcular números, mas transformar os dados em conclusões que ajudassem a turma a entender o comportamento das vendas.

## O que eu fiz

Comecei limpando os registros repetidos, corrigindo datas com formato inconsistente e removendo linhas incompletas que atrapalhavam a análise. Depois disso, trabalhei com as etapas principais do projeto:
- Analisei os dados de vendas com pandas em notebooks Jupyter
- Guardei os dados em PostgreSQL e consultei com SQL
- Criei gráficos com matplotlib para mostrar a sazonalidade

Também criei agregações por mês, dia da semana e categoria de produto. Usei consultas para comparar períodos de maior e menor movimento e conferir se os totais batendo entre as etapas. Em seguida, consolidei os resultados em um relatório curto para a apresentação em sala.

## Resultados

No conjunto analisado, identifiquei 1.248 vendas válidas distribuídas em 6 meses. Os dados mostraram aumento de vendas nos dois últimos meses do semestre, com pico na última quinzena, quando houve 18% mais pedidos do que na média do período. Também notei queda nas segundas-feiras e concentração maior de compras no fim da tarde.

Os gráficos ajudaram a visualizar esses padrões com clareza, e as consultas em SQL confirmaram os totais usados nas contas estatísticas. Ao final, consegui apresentar os principais achados de forma objetiva e com base em números consistentes.

## Desafios e aprendizados

O maior desafio foi lidar com inconsistências nos dados de origem, principalmente datas incompletas e registros duplicados. Também precisei revisar algumas consultas várias vezes para evitar contagens erradas. Isso me fez perceber a importância de validar os dados antes de interpretar qualquer resultado.

Aprendi, na prática, a conectar Banco de Dados e Estatística no mesmo fluxo de trabalho. Além disso, ganhei mais segurança para explicar decisões técnicas e apresentar conclusões com clareza. Apresentei os resultados para a turma e para o professor
