# Resultados da avaliação (gerado por `eval/run_eval.py`)

Material: `data/sample` (fictício). Cada vaga roda nos dois modos com o mesmo prompt.

## Por vaga

| Vaga | Modo | Fortes | Lacunas | Iscas na vaga | Iscas em Lacunas | Ausentes afirmados como forte | Citações inválidas | Avisos |
|---|---|---|---|---|---|---|---|---|
| 01_backend_python_jr_pt | sem RAG | 11 | 4 | AWS, Docker | AWS, Docker | - | 0 | 0 |
| 01_backend_python_jr_pt | RAG | 10 | 8 | AWS, Docker | AWS, Docker | - | 0 | 1 |
| 02_react_pleno_en | sem RAG | 3 | 6 | Redux, Jest, GraphQL | Redux, Jest, GraphQL | - | 0 | 0 |
| 02_react_pleno_en | RAG | 1 | 6 | Redux, Jest, GraphQL | Redux, Jest, GraphQL | - | 0 | 0 |
| 03_fullstack_dotnet_pt | sem RAG | 4 | 10 | C#, .NET, ASP.NET, SQL Server, Azure | C#, ASP.NET, SQL Server, Azure | - | 0 | 0 |
| 03_fullstack_dotnet_pt | RAG | 4 | 11 | C#, .NET, ASP.NET, SQL Server, Azure | C#, ASP.NET, SQL Server, Azure | SQL Server | 0 | 0 |
| 04_devops_jr_pt | sem RAG | 1 | 10 | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | - | 0 | 0 |
| 04_devops_jr_pt | RAG | 1 | 21 | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | AWS, Docker, Kubernetes, Terraform, Linux, CI/CD | - | 0 | 1 |
| 05_frontend_jr_pt | sem RAG | 11 | 2 | - | - | - | 0 | 0 |
| 05_frontend_jr_pt | RAG | 11 | 4 | - | - | - | 0 | 0 |
| 06_data_analyst_jr_pt | sem RAG | 3 | 7 | Power BI, Excel | Power BI, Excel | - | 0 | 0 |
| 06_data_analyst_jr_pt | RAG | 5 | 5 | Power BI, Excel | Power BI, Excel | - | 0 | 0 |
| 07_web_intern_en | sem RAG | 8 | 3 | - | - | - | 0 | 0 |
| 07_web_intern_en | RAG | 8 | 7 | - | - | - | 0 | 0 |

## Resumo por modo

| Modo | Iscas detectadas | Ausentes afirmados como forte | Citações inválidas | Relatórios com avisos |
|---|---|---|---|---|
| sem RAG | 17/18 | 0 | 0 | 0/7 |
| RAG | 17/18 | 1 | 0 | 2/7 |

## Avisos de validação

- 01_backend_python_jr_pt (RAG): a validação moveu de Pontos fortes para Lacunas: Desenvolver e manter APIs REST em Python
- 04_devops_jr_pt (RAG): a validação moveu de Pontos fortes para Lacunas: Atuação em automação de infraestrutura e entrega contínua, Criar e manter pipelines de CI/CD, Provisionar infraestrutura com Terraform, Operar clusters Kubernetes e containers Docker, Monitorar serviços na AWS, Docker, Kubernetes, Terraform, AWS, Linux
