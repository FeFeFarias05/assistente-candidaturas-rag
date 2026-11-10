# Integração contínua

## Visão geral

Eu desenvolvi este projeto pessoal na faculdade para melhorar a automação de um trabalho em grupo que estava crescendo rápido e já começava a ter erros repetidos a cada entrega. A meta foi reduzir falhas manuais, encurtar o tempo de validação e deixar o fluxo de colaboração mais previsível para todos. Como o código era revisado várias vezes por semana, eu senti que precisava de um processo que desse retorno imediato quando algo quebrasse.

O foco do projeto foi criar uma rotina simples, mas confiável, para que cada mudança enviada por pull request fosse validada antes da aprovação. Isso ajudou a organizar melhor o trabalho e a diminuir retrabalho nas últimas semanas do semestre.

## O que eu fiz

Primeiro, eu revisei o fluxo atual do repositório e identifiquei os pontos em que a equipe mais esquecia de testar antes de subir alterações. Depois, implementei a automação principal e documentei o uso para o grupo.

- Configurei GitHub Actions para rodar os testes a cada pull request
- Usei Linux no terminal para automatizar tarefas com scripts
- Ajustei a organização dos arquivos para facilitar a execução automática
- Incluí instruções curtas no projeto para orientar quem fosse colaborar

Também acompanhei a execução em diferentes envios durante duas semanas, observando quando havia falhas e o que precisava ser corrigido no processo.

## Resultados

Depois da automação, os erros simples passaram a aparecer antes da revisão humana, o que evitou retrabalho na etapa final. Em cerca de 15 pull requests acompanhados, consegui identificar problemas cedo em quase todos os casos em que havia inconsistência nos testes ou esquecimentos de validação.

Com isso, o grupo passou a gastar menos tempo conferindo o básico manualmente. O processo ficou mais claro e a aprovação das alterações ficou mais organizada. Eu também percebi que as entregas ficaram menos dependentes de alguém lembrar de executar tudo na mão.

## Desafios e aprendizados

O maior desafio foi ajustar a automação para funcionar sem atrapalhar o ritmo do grupo. No começo, alguns scripts falhavam por causa de caminhos errados e por diferenças de ambiente entre as máquinas. Eu precisei revisar cada etapa e testar várias vezes até estabilizar o fluxo.

Os principais aprendizados foram:

- automatização precisa começar pelo processo real, não pelo ideal
- documentação curta evita confusão na equipe
- validar cedo reduz correções no fim
- pequenos ajustes no terminal economizam tempo ao longo do semestre

No fim, esse projeto me ajudou a entender melhor como integrar automação ao desenvolvimento cotidiano sem complicar a rotina de quem participa do trabalho.
