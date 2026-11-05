# Avaliação (Dia 6)

Como rodar: `python eval/run_eval.py` (usa a API de verdade, sempre com o material fictício `data/sample`).
Dados brutos: [eval/results.md](../eval/results.md) (rodada final) e [eval/results_rodada1.md](../eval/results_rodada1.md) (antes das correções).

## Método
- 7 vagas de teste em `eval/jobs/` (5 em português, 2 em inglês). Cada uma foi desenhada contra o perfil fictício: duas casam bem (05, 07), três quase não casam (02, 03, 04) e duas casam em parte (01, 06).
- "Iscas": 18 tecnologias que o perfil **não tem** (C#, ASP.NET, Azure, AWS, Docker, Redux, Jest, GraphQL, Power BI, Excel, Kubernetes, Terraform, Linux, CI/CD...). Docker e Redux aparecem no material só como "não usei", o que testa se o modelo entende a negação.
- Cada vaga roda nos dois modos (sem RAG e com RAG) com o mesmo prompt e o mesmo modelo (`gpt-5.4-mini`).
- Métricas automáticas: isca que foi para **Lacunas**; tecnologia ausente afirmada como **ponto forte**; citação inexistente; avisos da validação.
- Relevância da busca: nota 0 a 2 por requisito (ver abaixo).

## Resultados: antes e depois das correções

| | Rodada 1 | Rodada 2 (final) |
|---|---|---|
| Sem RAG: ausentes afirmados como forte | 0 | 0 |
| **RAG: ausentes afirmados como forte** | **5** (GraphQL, C#, ASP.NET, SQL Server, AWS) | **0** |
| Citações inexistentes (sem RAG / RAG) | 0 / 0 | 0 / 0 |
| Iscas em Lacunas (sem RAG / RAG) | 18/18 / 17/18 | 17/18 / 17/18 |
| Relatórios com avisos (sem RAG / RAG) | 1/7 / 6/7 | 0/7 / 2/7 |

**O que a rodada 1 mostrou.** O RAG inventou mais que o modo sem RAG. Dois casos eram invenção de fato, com citação real apontando para um trecho que não dizia aquilo: "AWS: a candidata lista AWS no perfil" e "GraphQL: tem projeto com GraphQL". Uma validação que só confere se o id existe não pega isso; a checagem do termo no trecho citado pegou, mas só avisava.

**O que mudou na rodada 2:**
1. Tecnologia sem suporte no trecho citado e item contraditório passaram a disparar uma nova tentativa (antes era só aviso).
2. O casamento de termos tolera sufixo de versão (HTML casa com HTML5), o que eliminou um falso alarme.
3. O prompt ganhou duas regras: os trechos do mapa foram achados por similaridade e podem ser irrelevantes; tecnologias são específicas (SQL não é SQL Server, Python não é C#).

Resultado final: **0 invenções** nos dois modos, **0 citações inexistentes**.

**Sobre a isca "perdida" (17/18).** É a `.NET` da vaga 03 ("Full Stack .NET"). Os dois modos cobrem o assunto no relatório com "C# e ASP.NET Core", e a métrica procurava o texto `.NET` solto. Não é uma falha do modelo, e mantive o número como saiu em vez de ajustar a métrica depois de ver o resultado.

**Avisos que restaram (2 no RAG).** O modelo colocou em Pontos fortes um item que ele mesmo escreveu como "sem evidência" (ex.: "Docker: não usou Docker; sem evidência"). A validação não esconde: o aviso aparece no topo do relatório, e quem revisa vê.

## Relevância da busca (nota 0 a 2)

**Atenção: as notas foram atribuídas por mim (Claude), não por você. Revise antes de citá-las.** Critério:
- **2:** a busca trouxe o trecho que responde. Para requisito que o perfil não tem: nenhum trecho, ou o trecho que diz "não usei".
- **1:** só trechos parcialmente relacionados.
- **0:** trouxe trecho irrelevante para algo que o perfil não tem, ou deixou passar evidência que existe.

| Vaga | Requisitos | Média |
|---|---|---|
| 01 backend Python | 13 | 1,77 |
| 02 React pleno | 6 | 1,33 |
| 03 full stack .NET | 12 | 1,42 |
| 04 DevOps | 11 | 1,45 |
| 05 front-end | 12 | 1,83 |
| 06 analista de dados | 10 | 1,30 |
| 07 estágio web | 12 | 1,75 |
| **Total** | **76** | **1,58** (meta: ≥ 1,5) |

**Onde a busca erra (13 notas 0 em 76):**
- **11 casos: lixo para requisito que o perfil não tem.** Para "C#", "Azure", "AWS", "GraphQL" ou "Excel", a busca devolve o trecho "menos diferente" (similaridade 0,30 a 0,54) em vez de nada. O limiar fixo não separa bem o que existe do que não existe.
- **2 casos: evidência que existe e passou despercebida.** "Fluent English" e "Good written English" voltaram sem trechos, embora o currículo diga "Inglês B2" e "escrevo e-mails profissionais". Frases genéricas sobre soft skills são o ponto fraco do modelo de embeddings pequeno.

**Por que mantive o limiar em 0,30.** Subir para ~0,45 cortaria boa parte do lixo, mas também evidências reais com nota baixa (Flask 0,30; PostgreSQL 0,39). Um falso "sem evidência" tira do relatório algo que a candidata tem, e é mais difícil de notar que um trecho irrelevante. Como o LLM e a validação filtram o lixo (0 invenções no final), preferi manter a revocação.

## Conclusões (RAG × sem RAG, CA10)
- **Qualidade:** com o material pequeno deste teste (4 arquivos), os dois modos chegaram ao mesmo resultado final. **Não há ganho de qualidade medido a favor do RAG.** Na rodada 1 ele foi pior, e só igualou depois das correções.
- **Onde o RAG deve compensar** (não medido aqui): material grande demais para caber no prompt, custo por chamada e privacidade, já que só os trechos recuperados saem da máquina, em vez do material inteiro.
- **Limites desta avaliação:** 7 vagas, um modelo, um perfil fictício pequeno, relevância avaliada por mim. A comparação com um modelo maior (previsto no plano) não foi feita.
