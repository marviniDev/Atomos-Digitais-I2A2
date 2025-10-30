"""
Serviço de análise de dados com IA
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from config.settings import config

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """
    Serviço de análise de dados com IA usando CrewAI
    
    Responsabilidades:
    - Gerenciar agentes de IA
    - Gerar consultas SQL
    - Analisar resultados de dados
    - Gerar respostas em linguagem natural
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa o analisador de dados
        
        Args:
            api_key: Chave da API OpenAI
        """
        self.api_key = api_key
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Configurações do LLM
        openai_config = config.get_openai_config()
        self.llm = ChatOpenAI(**openai_config)
        
        logger.info("DataAnalyzer inicializado com sucesso")
    
    def create_sql_analyst_agent(self) -> Agent:
        """Cria agente especializado em análise SQL"""
        return Agent(
            role='SQL Analyst',
            goal='Generate accurate SQL queries based on user questions and database schema',
            backstory="""You are an expert SQL analyst with years of experience in database management and query optimization.
            Your specialty is understanding user questions and translating them into precise SQL queries.""",
            llm=self.llm,
            verbose=True,
            tools=[],
        )
    
    def create_data_analyst_agent(self) -> Agent:
        """Cria agente especializado em análise de dados"""
        return Agent(
            role='Data Analyst',
            goal='Generate clear and insightful analysis from SQL query results',
            backstory="""You are a skilled data analyst who excels at interpreting data and communicating insights.
            You have a talent for making complex data understandable and actionable.""",
            llm=self.llm,
            verbose=True,
            tools=[],
        )
    
    async def generate_sql_query(self, question: str, schema_info: Dict[str, Any], max_results: int = 100) -> str:
        """
        Gera consulta SQL baseada na pergunta e schema
        
        Args:
            question: Pergunta do usuário
            schema_info: Informações do schema do banco
            
        Returns:
            Consulta SQL gerada
        """
        try:
            logger.info(f"Gerando consulta SQL para: {question}")
            
            # Criar agente SQL
            sql_analyst = self.create_sql_analyst_agent()
            
            # Criar descrição do schema
            schema_description = self._build_schema_description(schema_info)
            
            # Criar descrição da tarefa
            task_description = self._build_sql_task_description(question, schema_description, max_results)
            
            # Criar tarefa
            sql_task = Task(
                description=task_description,
                agent=sql_analyst,
                verbose=True,
                expected_output="Uma consulta SQL válida e otimizada",
            )
            
            # Executar crew
            crew = Crew(
                agents=[sql_analyst],
                tasks=[sql_task],
                process=Process.sequential,
                verbose=True,
            )
            
            result = await crew.kickoff_async()
            sql_query = result.raw.strip()
            
            # Validar e aplicar LIMIT se necessário
            sql_query = self._validate_and_apply_limit(sql_query, max_results)
            
            logger.info(f"Consulta SQL gerada: {sql_query}")
            return sql_query
            
        except Exception as e:
            error_msg = f"Erro ao gerar consulta SQL: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def generate_answer(self, question: str, sql: str, results: List[Dict[str, Any]]) -> str:
        """
        Gera resposta em linguagem natural baseada nos resultados
        
        Args:
            question: Pergunta original
            sql: Consulta SQL executada
            results: Resultados da consulta
            
        Returns:
            Resposta em linguagem natural
        """
        try:
            logger.info(f"Gerando resposta para: {question}")
            
            # Criar agente de análise
            data_analyst = self.create_data_analyst_agent()
            
            # Criar descrição da tarefa
            task_description = self._build_analysis_task_description(question, sql, results)
            
            # Criar tarefa
            analysis_task = Task(
                description=task_description,
                agent=data_analyst,
                verbose=True,
                expected_output="Uma resposta clara e objetiva em português",
            )
            
            # Executar crew
            crew = Crew(
                agents=[data_analyst],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=True,
            )
            
            result = await crew.kickoff_async()
            answer = result.raw.strip()
            
            logger.info(f"Resposta gerada: {answer[:100]}...")
            return answer
            
        except Exception as e:
            error_msg = f"Erro ao gerar resposta: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _build_schema_description(self, schema_info: Dict[str, Any]) -> str:
        """Constrói descrição do schema do banco"""
        schema_description = "Estrutura do banco de dados:\n"
        for table_name, info in schema_info.items():
            schema_description += f"\nTabela: {table_name}\n"
            schema_description += f"Colunas: {', '.join(info['columns'])}\n"
        return schema_description
    
    def _build_sql_task_description(self, question: str, schema_description: str, max_results: int = 100) -> str:
        """Constrói descrição da tarefa de geração SQL"""
        return f"""
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

            4. LIMITAÇÃO DE RESULTADOS (CRÍTICO):
            - SEMPRE adicione LIMIT {max_results} no final da consulta
            - Isso evita retornar milhares de registros e sobrecarregar o sistema
            - Para consultas de contagem (COUNT), não use LIMIT
            - Para consultas de agregação (SUM, AVG, etc.), não use LIMIT
            - Para consultas que listam registros, SEMPRE use LIMIT {max_results}

            5. CONVERSÃO DE TIPOS DE DADOS (IMPORTANTE):
            - Colunas numéricas podem estar armazenadas como TEXT (ex: "10,00", "28,50")
            - SEMPRE use CAST(coluna AS REAL) para comparações numéricas
            - Exemplos corretos:
              * WHERE CAST("quantidade" AS REAL) > 10
              * WHERE CAST("valor_total" AS REAL) > 100.50
              * WHERE CAST("data_emissão" AS DATE) > '2025-01-01'
            - Isso garante comparações numéricas corretas

            COLUNAS QUE PRECISAM DE CAST PARA COMPARAÇÕES NUMÉRICAS:
            - "quantidade" -> CAST("quantidade" AS REAL)
            - "valor_total" -> CAST("valor_total" AS REAL)
            - "valor_unitário" -> CAST("valor_unitário" AS REAL)
            - "valor_nota_fiscal" -> CAST("valor_nota_fiscal" AS REAL)
            - "icms_valor" -> CAST("icms_valor" AS REAL)
            - "ipi_valor" -> CAST("ipi_valor" AS REAL)
            - "pis_valor" -> CAST("pis_valor" AS REAL)
            - "cofins_valor" -> CAST("cofins_valor" AS REAL)

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
    
    def _build_analysis_task_description(self, question: str, sql: str, results: List[Dict[str, Any]]) -> str:
        """Constrói descrição da tarefa de análise"""
        return f"""Analise os dados e forneça uma resposta simples e clara em português.

            Dados:
            - Pergunta: {question}
            - SQL: {sql}
            - Resultados: {json.dumps(results, indent=2, ensure_ascii=False)}

            Instruções:
            - Forneça uma resposta direta e objetiva
            - Use linguagem clara e acessível
            - Destaque os principais insights dos dados
            - Se houver muitos resultados, resuma os principais pontos
            - Use formatação adequada para números e valores

            Retorne apenas a resposta final, sem explicações adicionais."""
    
    def _validate_and_apply_limit(self, sql_query: str, max_results: int = 100) -> str:
        """
        Valida e aplica LIMIT na consulta SQL se necessário
        
        Args:
            sql_query: Consulta SQL original
            
        Returns:
            Consulta SQL com LIMIT aplicado se necessário
        """
        try:
            # Normalizar a consulta
            sql_upper = sql_query.upper().strip()
            
            # Verificar se já tem LIMIT
            if 'LIMIT' in sql_upper:
                logger.info("Consulta já possui LIMIT")
                return sql_query
            
            # Verificar se é uma consulta que precisa de LIMIT
            # Consultas que NÃO precisam de LIMIT:
            no_limit_keywords = [
                'COUNT(', 'SUM(', 'AVG(', 'MIN(', 'MAX(', 'GROUP BY',
                'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER'
            ]
            
            needs_limit = True
            for keyword in no_limit_keywords:
                if keyword in sql_upper:
                    needs_limit = False
                    break
            
            if needs_limit:
                # Adicionar LIMIT com valor configurado
                if sql_query.strip().endswith(';'):
                    sql_query = sql_query.rstrip(';') + f' LIMIT {max_results};'
                else:
                    sql_query = sql_query + f' LIMIT {max_results}'
                
                logger.info(f"LIMIT {max_results} aplicado à consulta")
            else:
                logger.info("Consulta não precisa de LIMIT (agregação ou comando)")
            
            return sql_query
            
        except Exception as e:
            logger.warning(f"Erro ao validar LIMIT: {str(e)}")
            return sql_query
