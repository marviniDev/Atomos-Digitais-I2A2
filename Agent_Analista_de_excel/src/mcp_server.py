from crewai import Agent, Task, Crew, Process
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import os
from fastmcp import FastMCP
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# Inicializa o servidor MCP
mcp = FastMCP(name='agent-server')


@mcp.tool(name="multi_analyst")
async def multi_analyst(filepath: str, user_id: str, question: str):
    print("Iniciando análise")
    absolute_filepath = os.path.abspath(filepath)
    print(f"Arquivo: {absolute_filepath}")
    print(f"Usuário: {user_id}")
    print(f"Pergunta: {question}")

    ext = os.path.splitext(filepath)[1].lower()
    sheet_info = []
    preview_info = ""

    try:
        if ext == ".csv":
            df = pd.read_csv(filepath, nrows=20)
            preview_info = f"Colunas: {df.columns.tolist()}. Linhas de exemplo: {df.head(2).to_dict(orient='records')}"
            sheet_info = ["CSV"]
        elif ext in [".xlsx", ".xls"]:
            xls = pd.ExcelFile(filepath, engine="openpyxl")
            first_sheet = xls.sheet_names[0]
            df = xls.parse(first_sheet, nrows=20)
            preview_info = f"Aba: {first_sheet}, Colunas: {df.columns.tolist()}. Linhas: {df.head(2).to_dict(orient='records')}"
            sheet_info = xls.sheet_names
        else:
            raise Exception("Formato de arquivo não suportado.")
    except Exception as e:
        print(f"[Erro ao ler arquivo]: {e}")
        raise

    # Configuração do servidor MCP
    excel_params = StdioServerParameters(
        command='uvx',
        args=["excel-mcp-server", "stdio"],
        env=os.environ
    )

    llm_excel = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

    try:
        with MCPServerAdapter(excel_params) as excel_tools:
            agent = Agent(
                role="Analista de Dados",
                goal="Analisar dados de forma objetiva e precisa",
                backstory="Sou um analista especializado em dados tabulares, com foco em CSV e Excel. Respondo perguntas com base nos dados.",
                tools=excel_tools,
                llm=llm_excel,
                verbose=False,
            )

            prompt = (
                f"Acesse o arquivo '{os.path.basename(filepath)}', localizado em '{absolute_filepath}'. "
                f"Tipo: {ext}, Abas disponíveis: {sheet_info}. "
                f"Preview dos dados: {preview_info}. "
                f"Pergunta do usuário: '{question}'. "
                f"Responda com base nos dados, de forma clara, sem repetir o conteúdo completo do arquivo."
            )

            task = Task(
                description=prompt,
                expected_output="Resposta concisa baseada nos dados reais, com foco em colunas e padrões relevantes.",
                agent=agent,
            )

            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False,
                max_iterations=1,
                memory=False,
            )

            result = await crew.kickoff_async()
            return result

    except Exception as e:
        print(f"[Erro ao executar análise]: {e}")
        raise

    finally:
        for adapter in excel_tools:
            try:
                adapter.stop()
            except Exception:
                pass


# Executa o servidor MCP
if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8005)
