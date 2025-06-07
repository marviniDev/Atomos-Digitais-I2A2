from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import os
from fastmcp import FastMCP
from langchain_openai import ChatOpenAI
from crewai.memory import EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
import pandas as pd
import json


from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP(name='agent-server')  # nome para o servidor

# Function for per-user memory
def get_user_memory(user_id: str):
    return EntityMemory(
        storage=RAGStorage(
            embedder_config={
                "provider": "openai",
                "config": {"model": "text-embedding-3-small"},
            },
            type="short_term",
            path=f"./memory_store/{user_id}/",
        )
    )


@mcp.tool(name="multi_analyst")
async def multi_analyst(data: dict, user_id: str, question: str):
    llm_excel = ChatOpenAI(temperature=0.3, model_name="gpt-3.5-turbo")
    memory = get_user_memory(user_id)

    try:
        Agent_csv = Agent(
            role="Analista de Dados CSV",
            goal="Efetuar análise de dados CSV para tomada de decisão",
            backstory="Sou especialista em análise de arquivos CSV.",
            tools=[],  # Nenhuma ferramenta externa, só LLM
            llm=llm_excel,
            verbose=True,
            memory=memory,
        )

        arquivos = ', '.join(list(data.keys()))
        colunas_info = ""
        contagens = ""
        dados_json = ""

        # Inclui todas as colunas, contagem e TODOS os dados em JSON (atenção ao tamanho!)
        for nome, linhas in data.items():
            df = pd.DataFrame(linhas)
            colunas_info += f"\nArquivo: {nome}\nColunas: {list(df.columns)}"
            contagens += f"\nO arquivo {nome} possui {df.shape[0]} linhas."
            # Envia todos os dados do arquivo em JSON
            dados_json += f"\nArquivo: {nome}\nDados completos (JSON):\n{json.dumps(linhas, ensure_ascii=False)}\n"

        descricao_dados = (
            f"Você recebeu os seguintes arquivos CSV: {arquivos}.\n"
            f"{colunas_info}\n"
            f"{contagens}\n"
            f"{dados_json}\n"
            f"Pergunta do usuário: {question}\n"
            "Utilize os dados completos fornecidos acima para responder de forma clara, objetiva e quantitativa sempre que possível. "
            "Se a pergunta envolver busca, contagem, soma, média, cruzamento de informações entre arquivos ou outras operações, utilize os dados completos fornecidos. "
            "Se não for possível responder com os dados apresentados, explique o motivo."
        )

        excel_Task = Task(
            description=descricao_dados,
            expected_output="retorne a análise de dados para tomada de decisão",
            agent=Agent_csv,
            memory=memory,
        )

        crew = Crew(
            agents=[Agent_csv],
            tasks=[excel_Task],
            process=Process.sequential,
            verbose=True,
            max_iterations=1,
            memory=True,
            entity_memory=memory,
        )

        result = await crew.kickoff_async()
        return result  # Retorna o resultado da análise
    finally:
        pass  # Não há excel_tools para parar


if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8005)
