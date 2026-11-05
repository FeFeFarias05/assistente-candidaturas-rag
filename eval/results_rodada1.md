# Rodada 1 (antes das correções do Dia 6): resultados da avaliação

Material: `data/sample` (fictício). Cada vaga roda nos dois modos com o mesmo prompt.

## Por vaga

| Vaga | Modo | Fortes | Lacunas | Iscas na vaga | Iscas em Lacunas | Ausentes afirmados como forte | Citações inválidas | Avisos |
|---|---|---|---|---|---|---|---|---|
| 01_backend_python_jr_pt | sem RAG | 11 | 4 | AWS, Docker | AWS, Docker | - | 0 | 0 |
| 01_backend_python_jr_pt | RAG | 11 | 2 | AWS, Docker | AWS, Docker | - | 0 | 1 |
| 02_react_pleno_en | sem RAG | 2 | 5 | Redux, Jest, GraphQL | Redux, Jest, GraphQL | - | 0 | 0 |
| 02_react_pleno_en | RAG | 2 | 6 | Redux, Jest, GraphQL | Redux, Jest, GraphQL | GraphQL | 0 | 1 |
| 03_fullstack_dotnet_pt | sem RAG | 5 | 12 | C#, .NET, ASP.NET, SQL Server, Azure | C#, .NET, ASP.NET, SQL Server, Azure | - | 0 | 0 |
| 03_fullstack_dotnet_pt | RAG | 6 | 10 | C#, .NET, ASP.NET, SQL Server, Azure | C#, ASP.NET, SQL Server, Azure | C#, ASP.NET, SQL Server | 0 | 1 |
| 04_devops_jr_pt | sem RAG | 1 | 10 | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | - | 0 | 0 |
| 04_devops_jr_pt | RAG | 5 | 8 | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | AWS | 0 | 2 |
| 05_frontend_jr_pt | sem RAG | 10 | 2 | - | - | - | 0 | 0 |
| 05_frontend_jr_pt | RAG | 12 | 2 | - | - | - | 0 | 0 |
| 06_data_analyst_jr_pt | sem RAG | 3 | 7 | Power BI, Excel | Power BI, Excel | - | 0 | 0 |
| 06_data_analyst_jr_pt | RAG | 6 | 6 | Power BI, Excel | Power BI, Excel | - | 0 | 1 |
| 07_web_intern_en | sem RAG | 8 | 6 | - | - | - | 0 | 1 |
| 07_web_intern_en | RAG | 7 | 2 | - | - | - | 0 | 1 |

## Resumo por modo

| Modo | Iscas detectadas | Ausentes afirmados como forte | Citações inválidas | Relatórios com avisos |
|---|---|---|---|---|
| sem RAG | 18/18 | 0 | 0 | 1/7 |
| RAG | 17/18 | 5 | 0 | 6/7 |

## Avisos de validação

- 01_backend_python_jr_pt (RAG): Python: citada em Pontos fortes sem aparecer no trecho citado
- 02_react_pleno_en (RAG): GraphQL: citada em Pontos fortes sem aparecer no trecho citado
- 03_fullstack_dotnet_pt (RAG): C#: citada em Pontos fortes sem aparecer no trecho citado
- 04_devops_jr_pt (RAG): AWS: citada em Pontos fortes sem aparecer no trecho citado
- 04_devops_jr_pt (RAG): Pontos fortes contém item sem evidência: - Atuação em automação de infraestrutura e entrega contínua:
- 06_data_analyst_jr_pt (RAG): Pontos fortes contém item sem evidência: - Excel avançado: sem evidência no material. [projeto_gerenc
- 07_web_intern_en (sem RAG): HTML: citada em Pontos fortes sem aparecer no trecho citado
- 07_web_intern_en (RAG): HTML: citada em Pontos fortes sem aparecer no trecho citado
