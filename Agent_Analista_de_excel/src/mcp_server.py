from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import os
from fastmcp import FastMCP
from langchain_openai import ChatOpenAI
import agentops
from crewai.memory import EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage


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
async def multi_analyst(filepath: str, user_id: str, question: str):
    print("Cheguei aqui")
    # Configuração para o servidor de parâmetros do Excel
    excel_params = StdioServerParameters(
        command='uvx',
        args=["excel-mcp-server", "stdio"],
        env=os.environ
    )
    
    llm_excel = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    memory = get_user_memory(user_id)

    try:
        # Adaptador do MCP
        with MCPServerAdapter(excel_params) as excel_tools:
            # Criação do agente Excel
            Agent_excel = Agent(
                role="Analista de Excel",
                goal="Objetivo é efetuar analise de dados para tomada de decisão",  
                backstory="Eu sou Analista de Excel e tenho como objetivo efetuar analise de dados para tomada de decisão",
                tools=excel_tools,
                llm=llm_excel,
                verbose=True,
                memory=memory,
            )

            # Tarefa de análise
            excel_Task = Task(
                description=f"De acordo com a pergunta {question}, efetue uma análise de dados para tomada de decisão desse excel: {filepath}",
                expected_output=("retorne a analise de dados para tomada de decisão",),
                agent=Agent_excel,
                memory=memory,
            )

            # Crew para execução da tarefa
            crew = Crew(
                agents=[Agent_excel],
                tasks=[excel_Task],
                process=Process.sequential,
                verbose=True,
                max_iterations=1,
                memory=True,
                entity_memory=memory,
            )

            # Executa a tarefa do Crew
            result = await crew.kickoff_async()
            return result  # Retorna o resultado da análise
    finally:
        # Garante que o adaptador seja parado corretamente
        for adapter in excel_tools:
            try:
                adapter.stop()
            except Exception:
                pass


if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8005)
