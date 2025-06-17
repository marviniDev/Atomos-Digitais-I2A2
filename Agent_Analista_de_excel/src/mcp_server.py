from fastmcp import FastMCP
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any
import json
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = None

def initialize_openai(api_key: str):
    global client
    client = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1
    )

def create_sql_analyst_agent() -> Agent:
    """Create an agent specialized in SQL analysis"""
    logger.info("Creating SQL Analyst agent...")
    return Agent(
        role='SQL Analyst',
        goal='Generate accurate SQL queries based on user questions and database schema',
        backstory="""You are an expert SQL analyst with years of experience in database management and query optimization.
        Your specialty is understanding user questions and translating them into precise SQL queries.""",
        llm=client,
        verbose=True,
        tools=[],
    )

def create_data_analyst_agent() -> Agent:
    """Create an agent specialized in data analysis and interpretation"""
    logger.info("Creating Data Analyst agent...")
    return Agent(
        role='Data Analyst',
        goal='Generate clear and insightful analysis from SQL query results',
        backstory="""You are a skilled data analyst who excels at interpreting data and communicating insights.
        You have a talent for making complex data understandable and actionable.""",
        llm=client,
        verbose=True,
        tools=[],
    )

async def multi_analyst(question: str, schema_info: Dict[str, Any], api_key: str) -> str:
    """Analyze the question and generate SQL query based on schema information"""
    try:
        logger.info(f"Starting SQL analysis for question: {question}")
        
        # Initialize OpenAI client if not already initialized
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            logger.info("OpenAI client initialized")
        
        # Create SQL Analyst agent
        sql_analyst = create_sql_analyst_agent()
        
        # Create task for SQL generation
        logger.info("Creating SQL generation task...")

        schema_description = "Estrutura do banco de dados:\n"
        for table_name, info in schema_info.items():
            schema_description += f"\nTabela: {table_name}\n"
            schema_description += f"Colunas: {', '.join(info['columns'])}\n"

        task_description = f"""
            {schema_description}

            Pergunta do usuário: {question}

            Contexto: Você é um especialista em SQL com profundo conhecimento em SQLite. 
            Sua tarefa é gerar uma consulta SQL otimizada e precisa.

            Objetivo: Gerar uma consulta SQL que responda à pergunta do usuário utilizando 
            apenas as tabelas e colunas disponíveis no schema fornecido.

            Restrições e Requisitos:
            1. Sintaxe e Formatação:
            - Use aspas duplas para nomes de tabelas e colunas
            - Retorne a consulta em uma única linha
            - Não inclua explicações ou comentários

            2. Compatibilidade:
            - Garanta compatibilidade total com SQLite
            - Use apenas tabelas e colunas do schema fornecido

            3. Otimização:
            - Otimize a consulta para melhor performance
            - Use aliases apropriados para legibilidade
            - Analise as relações entre tabelas e colunas

            Sempre que possível, traga colunas adicionais que ajudem a identificar melhor o resultado. Por exemplo:
            - Razão social do emitente
            - Nome do destinatário
            - Data de emissão
            - UF de origem e destino
            - Natureza da operação
            - Valor da nota ou dos itens
            - Descrição do(s) produto(s)

            Formato de Resposta: Retorne APENAS a consulta SQL, sem texto adicional.
        """
        sql_task = Task(
            description=task_description,
            agent=sql_analyst,
            verbose=True,
            expected_output="Uma consulta SQL válida",
        )
        
        # Create and run the crew
        logger.info("Creating and running SQL analysis crew...")
        crew = Crew(
            agents=[sql_analyst],
            tasks=[sql_task],
            process=Process.sequential,
            verbose=True,
        )
        
        logger.info("Executing SQL analysis task...")
        result = await crew.kickoff_async()
        sql_query = result.raw
        
        # Log the generated SQL query
        logger.info("Generated SQL Query:")
        logger.info("-" * 80)
        logger.info(sql_query)
        logger.info("-" * 80)
        
        return sql_query
        
    except Exception as e:
        error_msg = f"Error in multi_analyst: {str(e)}"
        logger.error(error_msg)
        return error_msg

async def generate_answer(question: str, sql: str, results: List[Dict[str, Any]], api_key: str) -> str:
    """Generate a natural language answer based on SQL results"""
    try:
        logger.info(f"Starting answer generation for question: {question}")
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            logger.info("OpenAI client initialized")

        # Create Data Analyst agent
        data_analyst = create_data_analyst_agent()
        
        # Create task for answer generation
        logger.info("Creating answer generation task...")
        analysis_task = Task(
            description=f"""Analise os dados e forneça uma resposta simples em português.

            Dados:
            - Pergunta: {question}
            - SQL: {sql}s
            - Resultados: {json.dumps(results, indent=2)}

            Retorne apenas uma resposta direta e objetiva.""",
            agent=data_analyst,
            verbose=True,
            expected_output="Uma resposta simples em português",
        )
        
        # Create and run the crew
        logger.info("Creating and running answer generation crew...")
        crew = Crew(
            agents=[data_analyst],
            tasks=[analysis_task],
            process=Process.sequential,
            verbose=True,
        )
        
        logger.info("Executing answer generation task...")
        result = await crew.kickoff_async()
        answer = result.raw
        
        # Log the generated answer
        logger.info("Generated Answer:")
        logger.info("-" * 80)
        logger.info(answer)
        logger.info("-" * 80)
        
        return answer
        
    except Exception as e:
        error_msg = f"Error in generate_answer: {str(e)}"
        logger.error(error_msg)
        return error_msg

def main():
    logger.info("Starting MCP server...")
    
    # Create MCP server
    mcp = FastMCP("Analista de Excel 📊")
    
    # Register tools using decorators
    @mcp.tool
    async def multi_analyst_tool(question: str, schema_info: Dict[str, Any], api_key: str) -> str:
        return await multi_analyst(question, schema_info, api_key)
    
    @mcp.tool
    async def generate_answer_tool(question: str, sql: str, results: List[Dict[str, Any]], api_key: str) -> str:
        return await generate_answer(question, sql, results, api_key)
    
    # Start server with SSE transport
    logger.info("Starting server with SSE transport on port 8005...")
    mcp.run(transport="sse", host="127.0.0.1", port=8005)

# Executa o servidor MCP
if __name__ == "__main__":
    main()
