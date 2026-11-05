# Avaliação (Dia 6, atualizada depois de testar com um currículo real)

Como rodar: `python eval/run_eval.py` (usa a API de verdade, sempre com o material fictício `data/sample`).
Dados brutos: [eval/results.md](../eval/results.md) (rodada 3, a final) e [eval/results_rodada1.md](../eval/results_rodada1.md) (rodada 1, antes das correções).

## Método
- 7 vagas de teste em `eval/jobs/` (5 em português, 2 em inglês). Cada uma foi desenhada contra o perfil fictício: duas casam bem (05, 07), três quase não casam (02, 03, 04) e duas casam em parte (01, 06).
- "Iscas": 18 tecnologias que o perfil **não tem** (C#, ASP.NET, Azure, AWS, Docker, Redux, Jest, GraphQL, Power BI, Excel, Kubernetes, Terraform, Linux, CI/CD...). Docker e Redux aparecem no material só como "não usei", o que testa se o modelo entende a negação.
- Cada vaga roda nos dois modos (sem RAG e com RAG) com o mesmo prompt e o mesmo modelo (`gpt-5.4-mini`).
- Métricas automáticas: isca que foi para **Lacunas**; tecnologia ausente afirmada como **ponto forte**; citação inexistente; avisos da validação.
- Relevância da busca: nota 0 a 2 por requisito (ver abaixo).

## Três rodadas

| | Rodada 1 | Rodada 2 | Rodada 3 (final) |
|---|---|---|---|
| O que mudou | versão inicial | validação com nova tentativa para tecnologia sem suporte; prompt mais estrito | busca por versão e idioma; **a validação move para Lacunas** o que o modelo não corrige |
| Sem RAG: ausentes afirmados como forte | 0 | 0 | 0 |
| **RAG: ausentes afirmados como forte** | **5** | **0** | **1** (SQL Server, ver abaixo) |
| Citações inexistentes (sem RAG / RAG) | 0 / 0 | 0 / 0 | 0 / 0 |
| Iscas em Lacunas (sem RAG / RAG) | 18/18 / 17/18 | 17/18 / 17/18 | 17/18 / 17/18 |
| Relatórios com aviso (sem RAG / RAG) | 1/7 / 6/7 | 0/7 / 2/7 | 0/7 / 2/7 |

**Rodada 1.** O RAG inventou mais que o modo sem RAG. Dois casos eram invenção de fato, com citação real apontando para um trecho que não dizia aquilo: "AWS: a candidata lista AWS no perfil" e "GraphQL: tem projeto com GraphQL". Conferir só se o id da citação existe não pega isso; a checagem do termo no trecho citado pegou, mas só avisava.

**Rodada 2.** Tecnologia sem suporte e item contraditório passaram a disparar uma nova tentativa. O casamento de termos tolerou sufixo de versão (HTML ≈ HTML5). O prompt ganhou regras: os trechos do mapa foram achados por similaridade e podem ser irrelevantes; tecnologias são específicas (SQL não é SQL Server).

**Entre as rodadas 2 e 3** testei com um currículo real e achei falsas lacunas (HTML5 sem trecho mesmo com "HTML" no currículo; "English" sem trecho mesmo com "Inglês"). Corrigi a busca. Numa execução intermediária o RAG voltou a afirmar "AWS" como ponto forte: **o modelo varia entre execuções**, e a nova tentativa não bastou.

**Rodada 3.** Se depois da nova tentativa ainda sobrar, o código move o item de Pontos fortes para Lacunas e registra isso nos avisos. Resultado: nenhuma tecnologia de uma palavra ausente chega aos Pontos fortes.

**O caso que sobrou (1 no RAG): "SQL Server" na vaga 03.** O item diz "Escrever consultas em SQL Server: a candidata escreveu consultas em SQL" e infla SQL para SQL Server. A validação só confere tecnologias de uma palavra (termos como "web development" dariam falso alarme), então não pega. É um limite conhecido e agora tem um exemplo concreto.

**Sobre a isca "perdida" (17/18).** É a `.NET` da vaga 03 ("Full Stack .NET"). Os dois modos cobrem o assunto com "C# e ASP.NET Core", e a métrica procurava o texto `.NET` solto. Não é falha do modelo, e mantive o número como saiu em vez de ajustar a métrica depois de ver o resultado.

**Efeito colateral e correção.** Na vaga 04 o RAG escreveu 8 itens "sem evidência" dentro de Pontos fortes; ao movê-los, Lacunas ficou duplicada (10 → 21 itens). Depois dessa rodada, o código passou a não duplicar lacuna que já existe. **Não rodei a avaliação de novo** depois dessa correção, então `eval/results.md` ainda mostra os 21.

## Relevância da busca (nota 0 a 2)

**Atenção: as notas foram atribuídas por mim (Claude), não por você. Revise antes de citá-las.** Critério:
- **2:** a busca trouxe o trecho que responde. Para requisito que o perfil não tem: nenhum trecho, ou o trecho que diz "não usei".
- **1:** só trechos parcialmente relacionados.
- **0:** trouxe trecho irrelevante para algo que o perfil não tem, ou deixou passar evidência que existe.

| Vaga | Requisitos | Média |
|---|---|---|
| 01 backend Python | 13 | 1,77 |
| 02 React pleno | 6 | 1,67 |
| 03 full stack .NET | 12 | 1,42 |
| 04 DevOps | 11 | 1,45 |
| 05 front-end | 12 | 1,83 |
| 06 analista de dados | 10 | 1,30 |
| 07 estágio web | 12 | 1,92 |
| **Total** | **76** | **1,63** (meta: ≥ 1,5) |

As notas da rodada 1 eram 1,58 no total. Subiram porque a busca de idioma passou a achar "Inglês B2" para "Fluent English" e "Good written English" (os dois únicos zeros por evidência perdida). Só reavaliei os requisitos que mudaram.

**Onde a busca ainda erra (11 notas 0 em 76):** todas são lixo para requisito que o perfil não tem. Para "C#", "Azure", "AWS", "GraphQL" ou "Excel", a busca devolve o trecho "menos diferente" (similaridade 0,30 a 0,54) em vez de nada. O limiar fixo não separa bem o que existe do que não existe.

**Por que mantive o limiar em 0,30.** Subir para ~0,45 cortaria boa parte do lixo, mas também evidências reais com nota baixa (Flask 0,30; PostgreSQL 0,39). Um falso "sem evidência" tira do relatório algo que a candidata tem, e é mais difícil de notar que um trecho irrelevante. Como o LLM e a validação filtram o lixo, preferi manter a revocação.

## Conclusões (RAG × sem RAG, CA10)
- **Qualidade:** com o material pequeno deste teste (4 arquivos), o modo sem RAG ficou igual ou melhor em todas as rodadas. O RAG chegou perto só depois de duas correções de validação. **Não há ganho de qualidade medido a favor do RAG.**
- **Onde o RAG deve compensar** (não medido aqui): material grande demais para caber no prompt, custo por chamada e privacidade, já que só os trechos recuperados saem da máquina, em vez do material inteiro.
- **Limites desta avaliação:** 7 vagas, um modelo, um perfil fictício pequeno, relevância avaliada por mim, cada número é de uma execução (o modelo varia). A comparação com um modelo maior, prevista no plano, não foi feita.
