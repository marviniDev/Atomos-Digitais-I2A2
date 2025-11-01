"""
Servidor MCP para consultas de IA no Sistema VR/VA
Baseado no padrão do agent_csv_analyzer
"""
import json
import logging
import os
import sys
from typing import Any, Dict, List

import pysqlite3
# Substitui o módulo padrão sqlite3 por pysqlite3
sys.modules["sqlite3"] = pysqlite3
sys.modules["sqlite"] = pysqlite3

from crewai import Agent, Task, Crew, Process
from fastmcp import FastMCP
from langchain_openai import ChatOpenAI

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
    """Create an agent specialized in SQL analysis for VR data"""
    logger.info("Creating SQL Analyst agent...")
    return Agent(
        role='SQL Analyst for VR/VA System',
        goal='Generate accurate SQL queries based on user questions and VR database schema',
        backstory="""You are an expert SQL analyst specialized in VR/VA (Vale Refeição/Vale Alimentação) 
        systems with years of experience in database management and query optimization.
        Your specialty is understanding user questions about VR data and translating them into precise SQL queries.""",
        llm=client,
        verbose=True,
        tools=[],
    )

def create_data_analyst_agent() -> Agent:
    """Create an agent specialized in VR data analysis and interpretation"""
    logger.info("Creating Data Analyst agent...")
    return Agent(
        role='VR Data Analyst',
        goal='Generate clear and insightful analysis from VR SQL query results',
        backstory="""You are a skilled data analyst who excels at interpreting VR/VA data and communicating insights.
        You have deep knowledge of Brazilian labor laws, VR calculations, and corporate benefits management.
        You have a talent for making complex VR data understandable and actionable.""",
        llm=client,
        verbose=True,
        tools=[],
    )

async def multi_analyst(question: str, schema_info: Dict[str, Any], api_key: str) -> str:
    """Analyze the question and generate SQL query based on VR database schema"""
    try:
        logger.info(f"Starting SQL analysis for VR question: {question}")
        
        # Initialize OpenAI client if not already initialized
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            initialize_openai(api_key)
            logger.info("OpenAI client initialized")
        
        # Create SQL Analyst agent
        sql_analyst = create_sql_analyst_agent()
        
        # Create task for SQL generation
        logger.info("Creating SQL generation task...")

        schema_description = "Estrutura do banco de dados VR/VA:\n"
        for table_name, info in schema_info.items():
            schema_description += f"\nTabela: {table_name}\n"
            schema_description += f"Colunas: {', '.join(info['columns'])}\n"

        task_description = f"""
            {schema_description}

            Pergunta do usuário sobre dados VR/VA: {question}

            Contexto: Você é um especialista em SQL com profundo conhecimento em SQLite e sistemas de VR/VA.
            Sua tarefa é gerar uma consulta SQL otimizada e precisa para dados de Vale Refeição/Vale Alimentação.

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

            4. Contexto VR/VA:
            - Considere que 'funcionarios_ativos' contém dados de funcionários elegíveis
            - 'sindicatos' contém valores por dia de VR por sindicato
            - 'dias_uteis' contém dias úteis por sindicato
            - 'ferias', 'afastados', 'desligados' contêm exclusões
            - 'admissoes' contém novas admissões
            - 'estagio', 'aprendiz', 'exterior' contêm exclusões específicas

            Sempre que possível, traga colunas adicionais que ajudem a identificar melhor o resultado:
            - Matrícula do funcionário
            - Nome do sindicato
            - Cargo do funcionário
            - Empresa
            - Valores de VR calculados
            - Status de exclusão

            Formato de Resposta: Retorne APENAS a consulta SQL, sem texto adicional.
        """
        sql_task = Task(
            description=task_description,
            agent=sql_analyst,
            verbose=True,
            expected_output="Uma consulta SQL válida para dados VR/VA",
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
    """Generate a natural language answer based on VR SQL results"""
    try:
        logger.info(f"Starting VR answer generation for question: {question}")
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            initialize_openai(api_key)
            logger.info("OpenAI client initialized")

        # Create Data Analyst agent
        data_analyst = create_data_analyst_agent()
        
        # Create task for answer generation
        logger.info("Creating answer generation task...")
        analysis_task = Task(
            description=f"""Analise os dados de VR/VA e forneça uma resposta clara e objetiva em português.

            Dados:
            - Pergunta: {question}
            - SQL: {sql}
            - Resultados: {json.dumps(results, indent=2, default=str)}

            Contexto VR/VA:
            - Sistema de Vale Refeição/Vale Alimentação
            - Dados de funcionários, sindicatos, exclusões e cálculos
            - Análise de custos empresa vs colaborador
            - Regras de negócio brasileiras

            Retorne uma resposta direta, objetiva e útil para gestão de VR/VA.
            Inclua insights relevantes sobre os dados quando apropriado.""",
            agent=data_analyst,
            verbose=True,
            expected_output="Uma resposta clara e objetiva em português sobre dados VR/VA",
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
    logger.info("Starting VR MCP server...")
    
    # Create MCP server
    mcp = FastMCP("Analista de VR/VA 🏢✨")
    
    # Register tools
    @mcp.tool
    async def multi_analyst_tool(question: str, schema_info: Dict[str, Any], api_key: str) -> str:
        """Analyze questions and generate SQL queries for VR data"""
        return await multi_analyst(question, schema_info, api_key)
    
    @mcp.tool
    async def generate_answer_tool(question: str, sql: str, results: List[Dict[str, Any]], api_key: str) -> str:
        """Generate natural language answers from SQL results"""
        return await generate_answer(question, sql, results, api_key)
    
    # Start server with SSE transport
    logger.info("Starting server with SSE transport on port 8006...")
    logger.info("Available tools:")
    logger.info("- multi_analyst_tool: SQL query generation")
    logger.info("- generate_answer_tool: Natural language answers")
    
    mcp.run(transport="sse", host="127.0.0.1", port=8006)

# Executa o servidor MCP
if __name__ == "__main__":
    main()
