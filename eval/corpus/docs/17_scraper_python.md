# Coleta automática de dados

## Visão geral
Desenvolvi este projeto pessoal para acompanhar preços de produtos que eu consultava com frequência e perceber variações ao longo do tempo sem depender de checagens manuais. Como estudante de Engenharia de Software, eu queria praticar automação, organização de dados e tratamento de falhas em uma rotina simples, mas útil no dia a dia. O foco foi montar um fluxo que coletasse informações de forma recorrente, guardasse o histórico e me mostrasse quando havia mudança relevante.

## O que eu fiz
Escrevi um scraper em Python com requests e BeautifulSoup. Primeiro, mapeei quais páginas tinham o preço mais estável e quais elementos eu precisava extrair. Depois, deixei o script preparado para lidar com três cenários básicos:
- produto disponível com preço visível;
- produto indisponível no momento;
- página retornando conteúdo incompleto.

Para evitar coletas manuais, Agendei a coleta diária com cron. O script roda uma vez por dia, salva o resultado em arquivos de texto separados por data e registra apenas os campos que eu precisava: nome do item, preço, data da coleta e observação quando o preço não aparece. Também incluí uma verificação simples para comparar a coleta atual com a anterior e destacar mudanças de valor.

## Resultados
Em cerca de duas semanas, consegui juntar um histórico diário suficiente para identificar padrões de queda e aumento em alguns itens. Isso me ajudou a tomar decisões com mais calma e a entender que nem toda variação diária era relevante.

Os principais resultados foram:
- redução do tempo gasto com checagem manual;
- histórico contínuo para comparar preços;
- detecção de variações acima de um valor que eu defini como relevante.

O projeto também me mostrou onde o processo ainda era frágil, especialmente quando a estrutura da página mudava.

## Desafios e aprendizados
O maior desafio foi lidar com inconsistências no conteúdo extraído. Em alguns dias, o preço vinha com formatação diferente ou o texto aparecia em outra parte da página. Eu precisei revisar o seletor algumas vezes e aceitar que a automação precisava de manutenção.

Também aprendi a validar melhor os dados antes de salvar. Houve casos em que o script registrava valores vazios e eu só percebi depois de analisar o histórico. A partir disso, passei a adicionar checagens simples e a testar o fluxo com páginas reais antes de confiar no agendamento diário.
