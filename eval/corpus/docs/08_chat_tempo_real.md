# Chat em tempo real

## Visão geral

Este projeto foi desenvolvido na disciplina de Redes, em grupo, com o objetivo de criar um chat em tempo real para troca de mensagens entre usuários. A proposta nasceu da necessidade de aplicar, na prática, conceitos de comunicação em rede, conexão persistente e envio de mensagens com baixa latência. Eu participei desde o planejamento até os testes finais, junto com outras colegas do grupo, em um trabalho realizado ao longo de quatro semanas.

## O que eu fiz

Implementei o chat em tempo real com WebSockets e JavaScript. Também cuidei da parte do cliente e da estrutura das mensagens exibidas na interface. Usei TypeScript no cliente para tipar as mensagens. No meu trabalho, eu fiquei responsável por:

- organizar o formato das mensagens enviadas e recebidas;
- tratar eventos de entrada e saída de usuários;
- ajustar a atualização da tela sem recarregar a página;
- revisar casos de erro, como conexão interrompida e mensagem vazia.

Além disso, ajudei a integrar as partes feitas pelo grupo, alinhando os nomes dos campos e o comportamento esperado em cada etapa da comunicação.

## Resultados

Ao final, entregamos um chat funcional, com troca de mensagens em tempo real entre vários participantes. O sistema permitia visualizar novas mensagens na hora e identificar quando alguém entrava na conversa. Nos testes feitos pela equipe, conseguimos manter a comunicação estável com até 8 usuários simulados na mesma sala. Também validamos o envio de mensagens curtas e longas, além de testar reconexão após queda de conexão.

## Desafios e aprendizados

O maior desafio foi lidar com o sincronismo entre o envio e a exibição das mensagens, principalmente quando duas pessoas enviavam texto quase ao mesmo tempo. Em alguns testes, a ordem das mensagens aparecia diferente da esperada, então precisei revisar a lógica de atualização do cliente. Outro ponto importante foi aprender a pensar em estado de conexão, algo que eu não tinha praticado com esse nível de detalhe.

Com esse projeto, eu aprendi a:

- trabalhar com comunicação em tempo real de forma mais concreta;
- organizar mensagens com mais cuidado para evitar inconsistências;
- colaborar em grupo dividindo responsabilidades sem perder o padrão do projeto.
