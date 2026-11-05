# Resultados da avaliação (gerado por `eval/run_eval.py`)

Material: `data/sample` (fictício). Cada vaga roda nos dois modos com o mesmo prompt.

## Por vaga

| Vaga | Modo | Fortes | Lacunas | Iscas na vaga | Iscas em Lacunas | Ausentes afirmados como forte | Citações inválidas | Avisos |
|---|---|---|---|---|---|---|---|---|
| 01_backend_python_jr_pt | sem RAG | 11 | 7 | AWS, Docker | AWS, Docker | - | 0 | 0 |
| 01_backend_python_jr_pt | RAG | 11 | 3 | AWS, Docker | AWS, Docker | - | 0 | 0 |
| 02_react_pleno_en | sem RAG | 1 | 6 | Redux, Jest, GraphQL | Redux, Jest, GraphQL | - | 0 | 0 |
| 02_react_pleno_en | RAG | 1 | 6 | Redux, Jest, GraphQL | Redux, Jest, GraphQL | - | 0 | 0 |
| 03_fullstack_dotnet_pt | sem RAG | 4 | 10 | C#, .NET, ASP.NET, SQL Server, Azure | C#, ASP.NET, SQL Server, Azure | - | 0 | 0 |
| 03_fullstack_dotnet_pt | RAG | 6 | 12 | C#, .NET, ASP.NET, SQL Server, Azure | C#, ASP.NET, SQL Server, Azure | - | 0 | 0 |
| 04_devops_jr_pt | sem RAG | 7 | 10 | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | - | 0 | 0 |
| 04_devops_jr_pt | RAG | 3 | 10 | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | - | 0 | 1 |
| 05_frontend_jr_pt | sem RAG | 11 | 2 | - | - | - | 0 | 0 |
| 05_frontend_jr_pt | RAG | 11 | 3 | - | - | - | 0 | 0 |
| 06_data_analyst_jr_pt | sem RAG | 3 | 7 | Power BI, Excel | Power BI, Excel | - | 0 | 0 |
| 06_data_analyst_jr_pt | RAG | 5 | 6 | Power BI, Excel | Power BI, Excel | - | 0 | 2 |
| 07_web_intern_en | sem RAG | 9 | 3 | - | - | - | 0 | 0 |
| 07_web_intern_en | RAG | 7 | 7 | - | - | - | 0 | 0 |

## Resumo por modo

| Modo | Iscas detectadas | Ausentes afirmados como forte | Citações inválidas | Relatórios com avisos |
|---|---|---|---|---|
| sem RAG | 17/18 | 0 | 0 | 0/7 |
| RAG | 17/18 | 0 | 0 | 2/7 |

## Avisos de validação

- 04_devops_jr_pt (RAG): Pontos fortes contém item sem evidência: - Docker: o trecho do projeto de gerenciador de tarefas info
- 06_data_analyst_jr_pt (RAG): Pontos fortes contém item sem evidência: - Apoio ao time de BI na criação de relatórios e análises: s
- 06_data_analyst_jr_pt (RAG): Pontos fortes contém item sem evidência: - Apresentar resultados para as áreas de negócio: sem evidên
