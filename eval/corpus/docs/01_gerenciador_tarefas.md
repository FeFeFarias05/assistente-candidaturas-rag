# Gerenciador de tarefas

## Visão geral

Em 2024, desenvolvi este projeto na disciplina de Engenharia de Software II, em dupla, com foco em um gerenciador de tarefas para uso local. A ideia foi criar uma aplicação simples, mas completa o suficiente para praticar requisitos, modelagem e implementação de ponta a ponta. O sistema permitia cadastrar tarefas, alterar status, listar pendências e acompanhar o que já tinha sido concluído.

Trabalhamos com entregas semanais ao longo do semestre, o que me ajudou a organizar melhor o escopo e a dividir o desenvolvimento em etapas curtas. Também defini desde o início que o projeto seria mantido de forma enxuta, sem dependências desnecessárias, para facilitar os testes e a apresentação final.

## O que eu fiz

Fiquei responsável pela maior parte da implementação técnica e pela organização do repositório. Desenvolvi a API REST em Python com Flask. Modelei as tabelas no SQLite e escrevi as consultas em SQL. Também implementei as rotas para criar, listar, atualizar e excluir tarefas, além de validar campos obrigatórios como título e status.

Na parte de qualidade, Escrevi testes automatizados com pytest e cheguei a 85% de cobertura. Esses testes verificavam cenários de criação, atualização, busca e tratamento de erros, o que reduziu falhas durante as últimas entregas. Usei Git com branches por funcionalidade. Não usei Docker, porque a aplicação rodou apenas localmente

Além disso, revisei a estrutura do código para deixar os arquivos separados por responsabilidade e facilitar a leitura da dupla. Eu também fiquei responsável por juntar as alterações antes de cada apresentação parcial.

## Resultados

No fim do semestre, entregamos uma versão funcional do gerenciador com fluxo básico completo. A aplicação permitia acompanhar tarefas em aberto e concluídas sem depender de configuração complexa. O projeto foi apresentado dentro do prazo e recebeu retorno positivo pela clareza da modelagem e pela estabilidade nas execuções locais.

Um resultado importante foi ter chegado a uma base de testes que cobria os casos mais relevantes. Isso me deu segurança para alterar partes da API sem quebrar o comportamento principal. Também consegui mostrar, na prática, como pequenos incrementos semanais ajudam a evitar retrabalho perto da entrega final.

## Desafios e aprendizados

O principal desafio foi conciliar o tempo da disciplina com a divisão de tarefas entre duas pessoas. Em algumas semanas, precisei ajustar a implementação depois de feedback do professor e adaptar o escopo para manter o que era essencial. Outro ponto foi lidar com erros de validação e consistência entre API e consultas, principalmente nas primeiras versões.

Aprendi a documentar melhor as decisões técnicas, a testar antes de integrar mudanças e a manter o projeto mais previsível. Também entendi a importância de limitar o escopo quando o prazo é curto. Para mim, esse projeto foi importante porque me fez praticar organização, revisão de código e entrega contínua em um contexto realista de faculdade.
