from crewai import Agent, Task, Crew, Process
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import os
from fastmcp import FastMCP
from langchain_openai import ChatOpenAI
from crewai.memory import EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from dotenv import load_dotenv

load_dotenv()

# Inicializa o servidor MCP
mcp = FastMCP(name='agent-server')

# Função para obter memória por usuário
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

# Ferramenta registrada no servidor MCP
@mcp.tool(name="multi_analyst")
async def multi_analyst(filepath: str, user_id: str, question: str):
    print("Cheguei aqui")
    print(f"Filepath: {filepath}")
    print(f"User ID: {user_id}")
    print(f"Question: {question}")
    
    # Caminho absoluto
    absolute_filepath = os.path.abspath(filepath)
    print(f"Caminho absoluto: {absolute_filepath}")

    # Configuração do servidor do Excel (MCP Adapter)
    excel_params = StdioServerParameters(
        command='uvx',
        args=["excel-mcp-server", "stdio"],
        env=os.environ
    )
    print("Cheguei aqui2")

    llm_excel = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    memory = get_user_memory(user_id)

    try:
        print("Cheguei aqui no try")

        with MCPServerAdapter(excel_params) as excel_tools:
            # Define o agente
            Agent_excel = Agent(
                role="Analista de Excel",
                goal="Efetuar análises precisas com base nos dados de planilhas Excel para apoiar a tomada de decisões estratégicas.",
                backstory="Sou um especialista em análise de planilhas com experiência em transformar dados brutos em insights claros e acionáveis. Sei usar ferramentas avançadas de Excel como leitura de dados, criação de gráficos, tabelas dinâmicas e análises estatísticas.",
                tools=excel_tools,
                llm=llm_excel,
                verbose=True,
                memory=memory,
            )

            # Prompt mais claro e acionável para forçar o uso das ferramentas
            prompt_description = (
                f"Acesse o arquivo Excel localizado em '{absolute_filepath}', leia as primeiras abas e "
                f"liste os nomes das colunas e exemplos de dados (as 10 primeiras linhas). Em seguida, responda à pergunta: '{question}'. "
                f"Se necessário, utilize ferramentas como 'read_data_from_excel', 'get_metadata', 'create_pivot_table', etc. "
                f"Retorne uma análise clara e focada para apoiar a tomada de decisão."
            )

            # Define a tarefa
            excel_Task = Task(
                description=prompt_description,
                expected_output="Análise detalhada baseada nos dados reais da planilha, com colunas analisadas, padrões observados e possíveis recomendações.",
                agent=Agent_excel,
                memory=memory,
            )

            # Define o processo de execução
            crew = Crew(
                agents=[Agent_excel],
                tasks=[excel_Task],
                process=Process.sequential,
                verbose=True,
                max_iterations=1,
                memory=True,
                entity_memory=memory,
            )

            # Executa a tarefa
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
