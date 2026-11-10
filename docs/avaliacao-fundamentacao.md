# Avaliação de fundamentação

Pergunta: cada afirmação do relatório é sustentada pelo trecho que ela cita? (É a regra central do projeto: nunca afirmar o que o material não diz.)
Como rodar: `python eval/grounding_eval.py --judge-model gpt-5.5` (gasta API: gera 12 relatórios e julga as afirmações).
Números completos: [eval/results_grounding.md](../eval/results_grounding.md).

## Método
- **6 vagas** (3 de IA generativa, 3 gerais) contra o **corpus fictício de 25 documentos** da avaliação de retrieval, nos dois modos: RAG e material inteiro (62 mil caracteres no prompt). Mesmo prompt, mesmo modelo gerador (`gpt-5.4-mini`).
- Uma **afirmação** é um item de "Pontos fortes", um item de "O que destacar no currículo" ou uma linha do rascunho. Foram 222 no total.
- Um **juiz LLM** recebe cada afirmação e **somente os trechos que ela cita**, e classifica: *sustentada* (a evidência diz isso por completo), *parcial* (só em parte, ou em nível menor) ou *não sustentada*. O juiz é **outro modelo** (`gpt-5.5`), porque um modelo tende a aprovar o próprio texto.
- **Afirmação sem citação não vai ao juiz** e fica numa categoria à parte. Na primeira versão eu as contava como "não sustentadas", o que fez o modo sem busca parecer pior (4%): eram todas cortesias do rascunho ("Fico à disposição para conversar"), que não são afirmações sobre a candidata. Corrigi a métrica.
- **Checagem cruzada** com a regra determinística do projeto ("a tecnologia citada aparece no trecho citado"), para testar o juiz.

## Resultados

| Modo | Citadas | Sustentada (IC 95%) | Parcial | Não sustentada | Linhas sem citação |
|---|---|---|---|---|---|
| Material inteiro | 109 de 114 | 83% (75 a 89) | 17% | 0% (0 a 3) | 4% |
| RAG | 108 de 108 | 80% (71 a 86) | 20% | 0% (0 a 3) | 0% |

**Diferença RAG menos material inteiro: −4 pp (IC 95% de −14 a +6). Inconclusivo.** Com este corpus, os dois modos têm a mesma fundamentação.

| Seção | Sustentada (RAG / material inteiro) |
|---|---|
| Pontos fortes | 79% / 80% |
| O que destacar no currículo | 94% / 97% |
| **Rascunho de mensagem** | **50% / 58%** |

## O que os resultados dizem

1. **Nenhuma afirmação com citação foi julgada falsa**, nos dois modos (limite superior do intervalo: 3%). Isso mede o relatório **final**, já depois das validações do sistema (citação existente, tecnologia presente no trecho, itens sem suporte movidos para Lacunas), e não o LLM sozinho.
2. **O problema que sobra é o "parcial" (17 a 20%)**, e os exemplos têm um padrão: a afirmação **junta dois fatos e cita um trecho que cobre só um**. Por exemplo, "Python: desenvolveu uma API REST com Flask **e também escreveu um scraper**" cita o trecho da API, e o juiz nota que ele não menciona o scraper. Outros casos: "avaliar com métricas" quando o trecho fala de perguntas rotuladas mas não de métricas; "formação em Engenharia" quando o trecho diz só que é estudante. É exagero leve e citação estreita demais, não invenção.
3. **O rascunho é a seção mais fraca** (50 a 58% sustentado): cada linha costuma juntar vários fatos num parágrafo com uma citação só no fim, e o juiz exige que cada parte esteja na evidência.
4. **O juiz concorda com a regra determinística em 99% dos casos** (138 afirmações que citam uma tecnologia da vaga). Ele aprovou 2 afirmações cujo termo não estava na evidência e nunca reprovou uma com o termo presente. É um sinal de que o juiz não é leniente de forma grosseira, mas **não substitui conferir com uma pessoa**.

## Limitações (importantes)
- **O juiz é um LLM e não foi validado por uma pessoa.** Deixei pronta uma amostra de 30 afirmações para você rotular à mão (`eval/out/grounding_amostra.csv`, com os rótulos do juiz guardados à parte para não influenciar). Depois de preencher a última coluna, `python eval/grounding_eval.py --agreement eval/out/grounding_amostra.csv` calcula a acurácia do juiz, o kappa e quantas vezes ele aprovou ou reprovou a mais. Enquanto isso não for feito, os números acima são "o que um segundo LLM achou", e é assim que devem ser citados.
- **O juiz só vê os trechos citados.** "Não sustentada" significa "não está no que foi citado", o que é a semântica certa para citação, mas não detecta uma afirmação verdadeira citada no trecho errado de forma diferente de uma falsa.
- **Não mede o que o relatório deixou de dizer** (fatos do material que ele omitiu) nem se as **lacunas** apontadas estão certas. As falsas lacunas aparecem na avaliação de retrieval, não aqui.
- **6 vagas e ~110 afirmações por modo:** os intervalos de confiança de cerca de ±7 pp explicam por que a comparação entre os modos é inconclusiva.
- **Corpus fictício, gerado por LLM e escrito pelo mesmo autor das consultas.** Mede se o sistema é fiel ao material, não se funciona bem no seu currículo real.
- Os relatórios foram gerados uma vez; o gerador varia entre execuções.

## Conclusão
Neste corpus de 62 mil caracteres, o RAG **não perde fundamentação** em relação a mandar o material inteiro (diferença inconclusiva) e envia ao LLM no máximo 12 trechos de ~450 caracteres, em vez de todo o material. O valor do RAG aqui é privacidade e custo, não qualidade da resposta, o que bate com as avaliações anteriores. O ponto a melhorar não é invenção, é **precisão da citação**: fazer cada afirmação citar o trecho de cada fato que ela contém.
