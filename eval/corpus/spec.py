"""Especificação do corpus de avaliação (FICTÍCIO) e do gabarito.

O corpus simula o material de "Ana Exemplo" (o mesmo perfil de data/sample), em escala maior: ~25 documentos.
Cada documento é gerado por um LLM a partir de FATOS plantados palavra por palavra (PROJECTS) e de uma lista
de termos PROIBIDOS. O gabarito (QUERIES) diz, para cada requisito, quais frases provam que o perfil o tem.

Relevância é definida por TEXTO, não por id de trecho: um trecho é relevante para uma consulta se contém
alguma das frases de evidência. Assim o gabarito sobrevive a mudanças no chunking.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Query:
    text: str  # como o requisito apareceria na vaga
    kind: str  # tech | responsibility | soft | other (mesmo vocabulário do extrator)
    category: str  # present | negated | absent
    evidence: tuple  # present/negated: frases que provam; absent: termos que NÃO podem existir no corpus

    def as_requirement(self) -> dict:
        return {"text": self.text, "kind": self.kind, "required": True}


def Q(text, kind, category, *evidence):
    return Query(text, kind, category, tuple(evidence))


# ---------------------------------------------------------------------------------------------
# Documentos: cada fato é uma frase que DEVE aparecer literalmente no texto gerado.
# ---------------------------------------------------------------------------------------------
PROJECTS = [
    dict(file="01_gerenciador_tarefas.md", lang="pt", title="Gerenciador de tarefas",
         context="projeto da disciplina de Engenharia de Software II, feito em dupla, em 2024",
         facts=["Desenvolvi a API REST em Python com Flask",
                "Escrevi testes automatizados com pytest e cheguei a 85% de cobertura",
                "Modelei as tabelas no SQLite e escrevi as consultas em SQL",
                "Usei Git com branches por funcionalidade",
                "Não usei Docker, porque a aplicação rodou apenas localmente"]),
    dict(file="02_dashboard_gastos.md", lang="en", title="Expense Dashboard",
         context="personal project to learn React, about six months of part-time work in 2025",
         facts=["I built the interface with React using function components and hooks",
                "I consumed the REST API with fetch and handled loading and error states",
                "I did not use Redux; I managed state with hooks only",
                "I did not write automated tests for the React components",
                "I published the code on GitHub with a README in English"]),
    dict(file="03_landing_pages_estagio.md", lang="pt", title="Estágio em desenvolvimento web",
         context="estágio de oito meses na Padaria Digital Ltda, empresa fictícia",
         facts=["Mantive as landing pages da empresa com HTML5, CSS3 e Bootstrap",
                "Reduzi o tempo de carregamento da página inicial de 4,2s para 2,1s",
                "Corrigi bugs reportados pelo time e documentei o passo a passo de cada correção",
                "Abri pull requests no GitHub que foram revisados por outra pessoa"]),
    dict(file="04_assistente_llm.md", lang="pt", title="Assistente de perguntas sobre documentos",
         context="projeto pessoal de perguntas e respostas sobre documentos, em 2026",
         facts=["Integrei a API da OpenAI para gerar respostas a partir de trechos de documentos",
                "Gerei embeddings e implementei busca semântica por similaridade de cosseno",
                "Avaliei as respostas com um conjunto de 30 perguntas rotuladas à mão",
                "Dividi os documentos em trechos de cerca de 500 caracteres"]),
    dict(file="05_analise_vendas.md", lang="pt", title="Análise de dados de vendas",
         context="trabalho conjunto das disciplinas de Banco de Dados e Estatística",
         facts=["Analisei os dados de vendas com pandas em notebooks Jupyter",
                "Criei gráficos com matplotlib para mostrar a sazonalidade",
                "Guardei os dados em PostgreSQL e consultei com SQL",
                "Apresentei os resultados para a turma e para o professor"]),
    dict(file="06_api_autenticacao.md", lang="pt", title="API de autenticação",
         context="projeto de estudo sobre segurança de APIs",
         facts=["Implementei autenticação com tokens JWT em Node.js com Express",
                "Guardei os usuários em MongoDB",
                "Documentei cada endpoint com exemplos de requisição e resposta"]),
    dict(file="07_classificador_textos.md", lang="pt", title="Classificador de textos",
         context="trabalho de introdução a aprendizado de máquina",
         facts=["Treinei um classificador de textos com scikit-learn",
                "Medi precisão e recall em um conjunto de teste separado",
                "Usei validação cruzada para comparar os modelos"]),
    dict(file="08_chat_tempo_real.md", lang="pt", title="Chat em tempo real",
         context="projeto da disciplina de Redes, feito em grupo",
         facts=["Implementei o chat em tempo real com WebSockets e JavaScript",
                "Usei TypeScript no cliente para tipar as mensagens"]),
    dict(file="09_integracao_continua.md", lang="pt", title="Integração contínua",
         context="melhoria de automação em um projeto da faculdade",
         facts=["Configurei GitHub Actions para rodar os testes a cada pull request",
                "Usei Linux no terminal para automatizar tarefas com scripts"]),
    dict(file="10_prototipos_figma.md", lang="pt", title="Protótipos e guia de estilos",
         context="projeto de interface de um app de estudos",
         facts=["Prototipei as telas no Figma antes de implementar",
                "Criei componentes reutilizáveis e um guia de estilos"]),
    dict(file="11_equipe_scrum.md", lang="pt", title="Trabalho em equipe com Scrum",
         context="projeto integrador do semestre",
         facts=["Trabalhei em uma equipe de cinco pessoas usando Scrum, com sprints de duas semanas",
                "Participei das revisões de código e das reuniões de planejamento"]),
    dict(file="12_monitoria.md", lang="pt", title="Monitoria de programação",
         context="monitoria voluntária na faculdade",
         facts=["Fui monitora de Algoritmos e Estruturas de Dados por dois semestres",
                "Expliquei listas, pilhas, filas e árvores para os colegas"]),
    dict(file="13_ingles.md", lang="pt", title="Inglês técnico",
         context="relato sobre o uso do inglês nos estudos e nos projetos",
         facts=["Meu inglês é intermediário (B2): leio documentação técnica e escrevo e-mails profissionais",
                "Fiz uma apresentação em inglês sobre o projeto para a turma"]),
    dict(file="14_hackathon.md", lang="pt", title="Hackathon",
         context="evento de fim de semana organizado pela universidade",
         facts=["Participei de um hackathon de 48 horas e entreguei um protótipo funcional",
                "Dividi as tarefas com o grupo e apresentei o protótipo em cinco minutos"]),
    dict(file="15_modelagem_banco.md", lang="pt", title="Modelagem e desempenho de banco de dados",
         context="trabalho da disciplina de Banco de Dados",
         facts=["Usei SQLAlchemy para mapear as tabelas do PostgreSQL",
                "Criei índices e medi o tempo das consultas antes e depois"]),
    dict(file="16_acessibilidade.md", lang="pt", title="Acessibilidade web",
         context="revisão de acessibilidade de um site de curso",
         facts=["Revisei a acessibilidade com navegação por teclado e contraste de cores",
                "Ajustei os formulários para funcionarem com leitores de tela"]),
    dict(file="17_scraper_python.md", lang="pt", title="Coleta automática de dados",
         context="projeto pessoal para acompanhar preços",
         facts=["Escrevi um scraper em Python com requests e BeautifulSoup",
                "Agendei a coleta diária com cron"]),
    dict(file="18_site_portfolio.md", lang="en", title="Portfolio site",
         context="personal portfolio built in 2025",
         facts=["I built my portfolio site with Vite, React and TypeScript",
                "I deployed the site on Vercel"]),
    dict(file="19_jogo_canvas.md", lang="pt", title="Jogo com Canvas",
         context="projeto de fim de semana para praticar JavaScript",
         facts=["Criei um jogo com JavaScript e Canvas",
                "Implementei a detecção de colisão e a pontuação"]),
    dict(file="20_open_source.md", lang="en", title="Open source contribution",
         context="first contribution to a public repository",
         facts=["I contributed a documentation fix to an open source project on GitHub"]),
    dict(file="21_documentacao.md", lang="pt", title="Documentação de projetos",
         context="hábito de documentar os projetos pessoais",
         facts=["Escrevi o README com instruções de instalação e exemplos de uso",
                "Documentei as decisões de arquitetura em um arquivo separado"]),
    dict(file="22_seguranca_web.md", lang="pt", title="Segurança em aplicações web",
         context="estudo guiado de vulnerabilidades comuns",
         facts=["Estudei XSS e SQL injection e apliquei validação de entrada",
                "Escapei a saída para evitar injeção de HTML"]),
    dict(file="23_estudo_graphql.md", lang="pt", title="Estudo de GraphQL",
         context="curso online de fim de semana",
         facts=["Estudei GraphQL em um curso, mas não usei em nenhum projeto"]),
    dict(file="24_tratamento_erros.md", lang="pt", title="Tratamento de erros e logs",
         context="melhorias de robustez em um projeto da faculdade",
         facts=["Tratei erros de rede e de entrada com mensagens claras para o usuário",
                "Escrevi logs para facilitar a depuração"]),
    dict(file="25_trabalho_remoto.md", lang="en", title="Remote teamwork",
         context="group project with teammates in other cities",
         facts=["I worked remotely with a team in another city, using chat and weekly video calls"]),
]

# Termos que só podem aparecer como negação, e só no documento indicado.
NEGATION_ONLY = {"Docker": "01_gerenciador_tarefas.md", "Redux": "02_dashboard_gastos.md",
                 "GraphQL": "23_estudo_graphql.md"}

# ---------------------------------------------------------------------------------------------
# Gabarito. present: o perfil tem (evidência = frases). negated: o material diz que NÃO tem.
# absent: não existe em lugar nenhum do corpus.
# ---------------------------------------------------------------------------------------------
QUERIES = [
    # --- present ---
    Q("Desenvolver e manter APIs REST em Python", "responsibility", "present", "API REST em Python com Flask"),
    Q("Flask", "tech", "present", "Flask"),
    Q("Testes automatizados com pytest", "tech", "present", "pytest"),
    Q("Cobertura de testes", "other", "present", "85% de cobertura"),
    Q("SQL", "tech", "present", "SQL"),
    Q("Modelagem de banco de dados relacional", "responsibility", "present", "Modelei as tabelas", "mapear as tabelas"),
    Q("PostgreSQL", "tech", "present", "PostgreSQL"),
    Q("SQLite", "tech", "present", "SQLite"),
    Q("Git e GitHub", "tech", "present", "Git com branches", "GitHub"),
    Q("Pull requests e revisão de código", "responsibility", "present", "pull requests", "revisões de código"),
    Q("React", "tech", "present", "React"),
    Q("Componentes funcionais e hooks do React", "responsibility", "present", "function components and hooks"),
    Q("Consumo de APIs REST no front-end", "responsibility", "present", "consumed the REST API with fetch"),
    Q("Tratamento de estados de carregamento e erro na interface", "responsibility", "present", "loading and error states"),
    Q("TypeScript", "tech", "present", "TypeScript"),
    Q("JavaScript", "tech", "present", "JavaScript"),
    Q("HTML5 e CSS3", "tech", "present", "HTML5", "CSS3"),
    Q("Bootstrap", "tech", "present", "Bootstrap"),
    Q("Otimização de desempenho de páginas web", "responsibility", "present", "4,2s para 2,1s"),
    Q("Correção de bugs", "responsibility", "present", "Corrigi bugs"),
    Q("Integração com APIs de LLM (OpenAI)", "responsibility", "present", "API da OpenAI"),
    Q("Embeddings e busca semântica", "tech", "present", "embeddings", "busca semântica"),
    Q("Avaliação da qualidade das respostas de um modelo", "responsibility", "present", "conjunto de 30 perguntas"),
    Q("Construção de pipelines RAG", "responsibility", "present", "trechos de documentos", "similaridade de cosseno"),
    Q("Divisão de documentos em trechos (chunking)", "responsibility", "present", "trechos de cerca de 500 caracteres"),
    Q("pandas e análise de dados", "tech", "present", "pandas"),
    Q("Visualização de dados", "responsibility", "present", "matplotlib"),
    Q("Jupyter Notebooks", "tech", "present", "Jupyter"),
    Q("Apresentar resultados para o time", "soft", "present", "Apresentei os resultados", "apresentei o protótipo"),
    Q("Node.js", "tech", "present", "Node.js"),
    Q("Autenticação com JWT", "tech", "present", "JWT"),
    Q("MongoDB", "tech", "present", "MongoDB"),
    Q("Documentação de APIs", "responsibility", "present", "exemplos de requisição e resposta"),
    Q("scikit-learn", "tech", "present", "scikit-learn"),
    Q("Métricas de avaliação de modelos (precisão e recall)", "responsibility", "present", "precisão e recall"),
    Q("Validação cruzada", "tech", "present", "validação cruzada"),
    Q("WebSockets", "tech", "present", "WebSockets"),
    Q("CI/CD com GitHub Actions", "tech", "present", "GitHub Actions"),
    Q("Linux e scripts de automação", "tech", "present", "Linux"),
    Q("Figma e prototipação", "tech", "present", "Figma"),
    Q("Componentes reutilizáveis e design system", "responsibility", "present", "componentes reutilizáveis"),
    Q("Metodologias ágeis (Scrum)", "other", "present", "Scrum"),
    Q("Algoritmos e estruturas de dados", "other", "present", "Algoritmos e Estruturas de Dados"),
    Q("Inglês avançado", "soft", "present", "inglês é intermediário"),
    Q("Leitura de documentação técnica em inglês", "soft", "present", "leio documentação técnica"),
    Q("Participação em hackathons", "other", "present", "hackathon"),
    Q("ORM (SQLAlchemy)", "tech", "present", "SQLAlchemy"),
    Q("Otimização de consultas com índices", "responsibility", "present", "Criei índices"),
    Q("Acessibilidade web", "other", "present", "acessibilidade"),
    Q("Web scraping com Python", "tech", "present", "scraper"),
    Q("Deploy de aplicações web", "responsibility", "present", "Vercel"),
    Q("Vite", "tech", "present", "Vite"),
    Q("Contribuições em projetos open source", "other", "present", "open source"),
    Q("Documentação técnica (README)", "responsibility", "present", "README"),
    Q("Segurança web (XSS e injeção)", "other", "present", "XSS"),
    Q("Tratamento de erros", "responsibility", "present", "Tratei erros"),
    Q("Logs e depuração", "responsibility", "present", "logs"),
    Q("Trabalho remoto", "other", "present", "remotely"),
    Q("Trabalho em equipe", "soft", "present", "equipe de cinco pessoas"),
    Q("Monitoria e ensino de programação", "other", "present", "monitora"),
    # --- negated: o material diz que NÃO tem ---
    Q("Docker", "tech", "negated", "Não usei Docker"),
    Q("Redux", "tech", "negated", "did not use Redux"),
    Q("GraphQL", "tech", "negated", "GraphQL"),
    Q("Testes de componentes React", "responsibility", "negated", "did not write automated tests for the React components"),
    # --- absent: nada no corpus ---
    *[Q(t, "tech", "absent", *ev) for t, *ev in [
        ("C#", "C#"), ("ASP.NET Core", "ASP.NET"), (".NET", ".NET"), ("Azure", "Azure"), ("AWS", "AWS"),
        ("Terraform", "Terraform"), ("Kubernetes", "Kubernetes"), ("Java", "Java"), ("Spring Boot", "Spring Boot"),
        ("Angular", "Angular"), ("Vue.js", "Vue"), ("PHP", "PHP"), ("Laravel", "Laravel"),
        ("Ruby on Rails", "Rails"), ("Power BI", "Power BI"), ("Excel avançado", "Excel"), ("Tableau", "Tableau"),
        ("Apache Spark", "Spark"), ("Kafka", "Kafka"), ("SQL Server", "SQL Server"), ("Oracle", "Oracle"),
        ("MySQL", "MySQL"), ("Swift", "Swift"), ("Kotlin", "Kotlin"), ("Flutter", "Flutter"),
        ("React Native", "React Native"), ("GitLab", "GitLab"), ("Jenkins", "Jenkins"), ("Sass", "Sass"),
        ("Next.js", "Next.js"), ("gRPC", "gRPC"), ("JUnit", "JUnit"), ("Selenium", "Selenium"),
        ("Redis", "Redis"), ("RabbitMQ", "RabbitMQ"), ("Elasticsearch", "Elasticsearch"),
        ("TensorFlow", "TensorFlow"), ("PyTorch", "PyTorch"), ("LangChain", "LangChain"),
        ("Hugging Face", "Hugging Face"), ("Django", "Django"), ("FastAPI", "FastAPI"),
        ("Fine-tuning de modelos de linguagem", "fine-tuning", "fine tuning"),
        ("Banco de dados vetorial (FAISS, Pinecone, pgvector)", "FAISS", "Pinecone", "pgvector", "Chroma",
         "banco de dados vetorial", "banco vetorial", "vector database"),
    ]],
]

# Termos proibidos em TODO o corpus (a lista de ausentes) e, fora do documento indicado, os de NEGATION_ONLY.
FORBIDDEN = sorted({e for q in QUERIES if q.category == "absent" for e in q.evidence})
