# Agent csv Analyzer
![image](https://github.com/user-attachments/assets/73071ae1-c1f1-4519-8a66-71d2703d9fd8)

## Descrição do Projeto

O **Agent csv Analyzer** é uma solução inovadora para análise inteligente de arquivos CSV compactados em ZIP, utilizando inteligência artificial para facilitar a tomada de decisões baseada em dados. O sistema permite que usuários façam upload de múltiplos arquivos CSV, façam perguntas em linguagem natural e recebam respostas detalhadas, quantitativas e explicativas, tudo por meio de uma interface web intuitiva.

A arquitetura do projeto integra um servidor MCP (Multi-Crew Protocol) para orquestração de agentes de IA, e um front-end desenvolvido em Streamlit, proporcionando uma experiência fluida e interativa. O backend utiliza modelos de linguagem natural para interpretar perguntas e analisar os dados enviados, retornando insights relevantes de forma automatizada.

## Funcionalidades

- Upload de arquivos ZIP contendo múltiplos CSVs.
- Visualização prévia dos dados enviados.
- Perguntas em linguagem natural sobre os dados.
- Respostas automáticas, quantitativas e explicativas via IA.
- Histórico de interações entre usuário e assistente.
- Processamento seguro e segregado por usuário.

## Como Executar

1. **Clone o repositório:**
   ```sh
   git clone https://github.com/seu-usuario/Atomos-Digitais-I2A2.git
   cd Atomos-Digitais-I2A2
   cd agent_csv_analyzer
   ```

2. **Crie e ative um ambiente virtual:**
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. **Instale as dependências:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Execute o projeto:**
   ```sh
   streamlit run src/app.py
   ```
   O sistema irá iniciar o servidor MCP e a interface Streamlit automaticamente.

## Estrutura do Projeto

```
```plaintext
agent_csv_analyzer/
│
├── requirements.txt    # Dependências do projeto
├── pyproject.toml      # Configuração do projeto Python
├── app.py              # Interface web (Streamlit)
├── db_utils.py         # Utilitários para acesso ao banco de dados
├── mcp_server.py       # Servidor MCP e lógica dos agentes
└── README.md           # Documentação do projeto
```

## Tecnologias Utilizadas

- [Python 3.10+](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [CrewAI](https://github.com/joaomdmoura/crewAI)
- [FastMCP](https://github.com/joaomdmoura/fastmcp)
- [LangChain OpenAI](https://github.com/langchain-ai/langchain)
- Pandas

## Licença

Este projeto está licenciado sob a Licença MIT.

---

> Projeto desenvolvido para o desafio I2A2, promovendo inovação e colaboração em análise de dados com IA.

