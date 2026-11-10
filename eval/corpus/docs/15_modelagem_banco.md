# Modelagem e desempenho de banco de dados

## Visão geral

Este trabalho foi feito na disciplina de Banco de Dados, com foco em modelagem e desempenho. Eu, Ana, estudante de Engenharia de Software, escolhi um cenário acadêmico simples para conseguir analisar as decisões de estrutura e o impacto delas nas consultas. O objetivo foi organizar os dados de forma consistente, reduzir redundâncias e verificar se ajustes na modelagem e nos acessos melhoravam o tempo de resposta.

## O que eu fiz

Eu comecei definindo as entidades principais e seus relacionamentos, com base nos requisitos do enunciado. Depois, implementei a estrutura no PostgreSQL e conectei a aplicação ao esquema criado. Usei SQLAlchemy para mapear as tabelas do PostgreSQL. Em seguida, inseri um conjunto de dados de teste com volume suficiente para comparar consultas em diferentes cenários.

Para medir o efeito das mudanças, montei consultas com filtros por data, identificação e status, que eram as mais representativas do caso. Criei índices e medi o tempo das consultas antes e depois. Também revisei o desenho das chaves e verifiquei se havia campos repetidos que poderiam gerar inconsistência ou custo desnecessário de armazenamento.

## Resultados

Os testes mostraram diferença perceptível nas consultas mais frequentes. Antes dos ajustes, algumas buscas demoravam mais quando filtravam por campos sem apoio adequado. Depois da criação dos índices, o tempo caiu de forma consistente nas execuções repetidas. Em média, uma consulta que levava cerca de 180 ms passou para algo em torno de 40 ms nos testes locais. Em outra consulta mais simples, a redução foi menor, mas ainda relevante, saindo de aproximadamente 70 ms para 25 ms.

Além do ganho de desempenho, a modelagem ficou mais clara para manutenção. A estrutura final evitou duplicação de informação e facilitou a leitura das relações entre as tabelas.

## Desafios e aprendizados

O maior desafio foi equilibrar normalização com praticidade de consulta. Em alguns momentos, eu precisei revisar o modelo para não criar separações desnecessárias que deixassem as consultas mais complexas. Outro ponto foi entender que índice não melhora tudo: em colunas com pouca variação, o ganho foi pequeno, então precisei escolher com cuidado onde aplicá-los.

Com esse trabalho, eu aprendi a avaliar banco de dados de forma mais objetiva, usando medidas e não só suposições. Também percebi que pequenas decisões de modelagem podem influenciar diretamente o desempenho e a organização do projeto.
