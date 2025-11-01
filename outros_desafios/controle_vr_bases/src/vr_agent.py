"""
Agente VR Refatorado - Arquitetura Limpa e Organizada com Integração ao Banco de Dados
"""
import os
import sys
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Adicionar src ao path para imports
sys.path.append(str(Path(__file__).parent))

# Importar módulos organizados
from config import config
from data_loader import ExcelLoader
from validator import DataValidator
from calculator import VRCalculator
from ai_service import OpenAIService
from report_generator import ExcelReportGenerator
from database import VRDatabaseManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VRAgentRefactored:
    """
    Agente VR refatorado com arquitetura limpa e integração ao banco de dados
    
    Responsabilidades:
    - Orquestrar o processamento completo de VR/VA
    - Coordenar os diferentes módulos
    - Gerenciar banco de dados SQLite
    - Manter a interface simples para o usuário
    """
    
    def __init__(self, openai_api_key: str, db_path: Optional[str] = None):
        """
        Inicializa o agente refatorado
        
        Args:
            openai_api_key: Chave da API OpenAI (obrigatória)
            db_path: Caminho do banco de dados SQLite (opcional)
        """
        # Validar configuração
        if not config.validate_config():
            raise ValueError("Configuração inválida")
        
        # Inicializar banco de dados
        self.db_manager = VRDatabaseManager(db_path)
        self.db_manager.initialize(db_path)
        
        # Inicializar módulos com integração ao banco
        self.data_loader = ExcelLoader(self.db_manager)
        self.validator = DataValidator()
        self.calculator = VRCalculator(self.db_manager)
        self.report_generator = ExcelReportGenerator()
        
        # Validar API key obrigatória
        if not openai_api_key:
            raise ValueError("❌ API Key da OpenAI é obrigatória!")
        
        # Inicializar IA
        try:
            self.ai_service = OpenAIService(openai_api_key)
            logger.info("✅ Serviço de IA inicializado")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar IA: {e}")
            raise ValueError(f"Erro ao inicializar IA: {e}")
        
        # Carregar dados automaticamente após inicialização
        try:
            logger.info("📁 Carregando dados automaticamente...")
            self._load_data_automatically()
            logger.info("✅ Dados carregados automaticamente com sucesso")
        except Exception as e:
            logger.warning(f"⚠️ Aviso: Não foi possível carregar dados automaticamente: {e}")
            logger.info("💡 Os dados serão carregados quando necessário")
    
    def _load_data_automatically(self) -> None:
        """
        Carrega dados automaticamente na inicialização
        
        Raises:
            Exception: Se houver erro no carregamento
        """
        try:
            # Carregar planilhas
            spreadsheets = self.data_loader.load_all_spreadsheets(load_to_db=True)
            
            # Validar planilhas obrigatórias
            missing_files = self.data_loader.validate_required_files(spreadsheets)
            if missing_files:
                raise ValueError(f"Planilhas obrigatórias ausentes: {missing_files}")
            
            logger.info(f"✅ {len(spreadsheets)} planilhas carregadas automaticamente")
            
        except Exception as e:
            logger.error(f"❌ Erro no carregamento automático: {e}")
            raise
    
    def process_vr_complete(self, ano: int, mes: int, nome_saida: str = None, use_database: bool = True) -> Dict:
        """
        Processa completamente o VR conforme todos os requisitos
        
        Args:
            ano: Ano de referência
            mes: Mês de referência
            nome_saida: nome do arquivo de saída (opcional)
            use_database: Se True, usa dados do banco de dados
            
        Returns:
            Dict: Resultado do processamento
        """
        logger.info(f"🚀 Iniciando processamento completo de VR para {mes}/{ano}...")
        
        try:
            # 1. Carregar dados para validação (banco já carregado)
            logger.info("📁 Dados já carregados automaticamente, usando banco de dados...")
            
            # 3. Validar dados diretamente do banco (sem recarregar planilhas)
            logger.info("🔍 Validando dados do banco...")
            validation_summary = self._validate_database_data()
            
            if validation_summary["total_problemas"] > 0:
                logger.warning(f"⚠️ Encontrados {validation_summary['total_problemas']} problemas nos dados")
            
            # 4. Processar com IA usando dados do banco
            insights_ia = {}
            if self.ai_service:
                logger.info("🤖 Processando com IA...")
                insights_ia = self._process_ai_with_database(ano, mes)
            
            # 5. Aplicar exclusões
            logger.info("🚫 Aplicando exclusões...")
            df_base = self._get_ativos_from_database()
            df_elegiveis, exclusoes_aplicadas = self.calculator.apply_exclusions_from_db(df_base)
            
            # 6. Calcular dias úteis
            logger.info("📊 Calculando dias úteis...")
            df_com_dias = self.calculator.calculate_working_days_from_db(df_elegiveis, ano, mes)
            
            # 7. Calcular valores de VR
            logger.info("💰 Calculando valores de VR...")
            df_final = self.calculator.calculate_vr_values_from_db(df_com_dias)
            
            # 8. Gerar resumos
            logger.info("📈 Gerando resumos...")
            df_resumo = self.calculator.generate_summary_by_sindicato(df_final)
            
            # 9. Gerar relatórios
            logger.info("📋 Gerando relatórios...")
            df_validacoes = self.report_generator.generate_validation_report(df_final)
            df_insights = self.report_generator.generate_insights_report(insights_ia)
            df_statistics = self.report_generator.generate_statistics_report(df_final, exclusoes_aplicadas)
            
            # 10. Salvar arquivo final
            if nome_saida is None:
                nome_saida = f"VR_{ano}_{mes:02d}.xlsx"
            
            logger.info("💾 Salvando arquivo final...")
            caminho_saida = self.report_generator.save_complete_report(
                df_final, df_resumo, df_validacoes, df_insights, df_statistics, nome_saida
            )
            
            # 11. Preparar resultado
            problemas = df_validacoes[df_validacoes['Problema'] != 'ok']
            
            resultado = {
                "sucesso": True,
                "arquivo_saida": caminho_saida,
                "total_funcionarios_inicial": len(df_base),
                "total_funcionarios_final": len(df_final),
                "total_vr": df_final["vr_total"].sum(),
                "total_empresa": df_final["%_empresa"].sum(),
                "total_colaborador": df_final["%_colaborador"].sum(),
                "exclusoes_aplicadas": exclusoes_aplicadas,
                "problemas_encontrados": len(problemas),
                "insights_ia": insights_ia,
                "resumo_sindicatos": df_resumo.to_dict('records'),
                "validacao_summary": validation_summary,
                "ano": ano,
                "mes": mes,
                "use_database": use_database
            }
            
            # 12. Salvar resultado no banco
            if use_database and self.db_manager:
                self.db_manager.save_processing_result(resultado)
            
            logger.info("✅ Processamento completo concluído com sucesso!")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento: {e}")
            return {
                "sucesso": False,
                "erro": str(e),
                "insights_ia": {}
            }
    
    def consult_ai(self, pergunta: str) -> str:
        """
        Agente IA dinâmico que analisa perguntas e gera SQL ou respostas genéricas
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            str: Resposta da IA com dados do banco ou resposta genérica
        """
        try:
            logger.info(f"🤖 Processando consulta IA: {pergunta}")
            
            # Usar IA para analisar a pergunta e decidir a estratégia
            analysis = self._analyze_question_with_ai(pergunta)
            
            if analysis["requires_database"]:
                return self._multi_analyst(pergunta, analysis)
            else:
                return self._consult_generic(pergunta)
                
        except Exception as e:
            logger.error(f"Erro na consulta IA: {e}")
            return f"Erro ao consultar dados: {e}"
    
    def _analyze_question_with_ai(self, pergunta: str) -> dict:
        """
        Analisa a pergunta usando IA para determinar estratégia de resposta
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            dict: Análise da pergunta com estratégia recomendada
        """
        try:
            if not self.ai_service:
                # Fallback para análise simples
                return {
                    "requires_database": self._is_database_query(pergunta),
                    "query_type": "simple",
                    "confidence": 0.5
                }
            
            # Usar IA para análise mais sofisticada
            prompt = f"""
            Analise a seguinte pergunta sobre dados de VR/VA e determine:
            1. Se requer consulta ao banco de dados (requires_database: true/false)
            2. Tipo de consulta (query_type: count/sum/group/filter/list)
            3. Confiança na análise (confidence: 0.0-1.0)
            4. Tabelas relevantes (tables: [lista])
            5. Campos relevantes (fields: [lista])
            
            Pergunta: "{pergunta}"
            
            Responda em formato JSON:
            {{
                "requires_database": boolean,
                "query_type": "string",
                "confidence": float,
                "tables": ["string"],
                "fields": ["string"]
            }}
            """
            
            response = self.ai_service.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse da resposta JSON
            import json
            analysis = json.loads(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            logger.warning(f"Erro na análise IA, usando fallback: {e}")
            return {
                "requires_database": self._is_database_query(pergunta),
                "query_type": "simple",
                "confidence": 0.5,
                "tables": [],
                "fields": []
            }
    
    def _multi_analyst(self, question: str, analysis: dict) -> str:
        """
        Analisa a pergunta e gera consulta SQL baseada no schema do banco VR
        
        Args:
            question: Pergunta do usuário
            analysis: Análise da pergunta feita pela IA
            
        Returns:
            str: Resposta com dados do banco
        """
        try:
            if not self.db_manager:
                return "❌ Banco de dados não disponível para consultas"
            
            # Obter schema do banco
            schema_info = self.db_manager.get_schema_info()
            
            # Gerar SQL usando IA
            sql_query = self._generate_sql_with_ai(question, schema_info, analysis)
            
            if sql_query:
                logger.info(f"🔍 Executando SQL: {sql_query}")
                
                # Executar consulta SQL
                result = self.db_manager.execute_query(sql_query)
                
                # Formatar resultado com IA
                if result:
                    return self._format_result_with_ai(question, result, sql_query)
                else:
                    return f"❌ Nenhum resultado encontrado para a consulta."
            else:
                logger.warning("Não foi possível gerar SQL, usando resposta genérica")
                return self._consult_generic(question)
                
        except Exception as e:
            logger.error(f"Erro no multi_analyst: {e}")
            return f"Erro ao consultar banco de dados: {e}"
    
    def _generate_sql_with_ai(self, question: str, schema_info: dict, analysis: dict) -> str:
        """
        Gera consulta SQL usando IA baseada na pergunta e schema
        
        Args:
            question: Pergunta do usuário
            schema_info: Schema do banco de dados
            analysis: Análise da pergunta
            
        Returns:
            str: Consulta SQL gerada
        """
        try:
            if not self.ai_service:
                logger.warning("IA não disponível, não é possível gerar SQL dinâmico")
                return None
            
            # Prompt para gerar SQL
            prompt = f"""
            Gere uma consulta SQL para responder à pergunta sobre dados de VR/VA.
            
            Pergunta: "{question}"
            
            Schema do banco de dados:
            {schema_info}
            
            Análise da pergunta:
            {analysis}
            
            Regras:
            1. Use apenas tabelas e campos que existem no schema
            2. Use nomes corretos para tabelas e colunas
            3. Inclua ORDER BY quando apropriado
            4. Use LIMIT para consultas que podem retornar muitos resultados
            5. Retorne apenas a consulta SQL, sem explicações
            
            SQL:
            """
            
            response = self.ai_service.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Validar se é uma consulta SQL válida
            if sql_query.upper().startswith(('SELECT', 'WITH')):
                return sql_query
            else:
                logger.warning(f"SQL gerado pela IA não é válido: {sql_query}")
                return None
                
        except Exception as e:
            logger.warning(f"Erro ao gerar SQL com IA: {e}")
            return None
    
    def _format_result_with_ai(self, question: str, result: list, sql_query: str) -> str:
        """
        Formata resultado da consulta usando IA
        
        Args:
            question: Pergunta original
            result: Resultado da consulta SQL
            sql_query: Consulta SQL executada
            
        Returns:
            str: Resultado formatado
        """
        try:
            if not self.ai_service or not result:
                return self._format_query_result(question, result, sql_query)
            
            # Converter resultado para string para IA
            result_str = str(result[:10])  # Limitar a 10 registros
            
            prompt = f"""
            Formate o resultado da consulta SQL de forma clara e útil.
            
            Pergunta: "{question}"
            Consulta SQL: {sql_query}
            Resultado: {result_str}
            
            Instruções:
            1. Responda de forma natural e conversacional
            2. Use emojis quando apropriado
            3. Destaque informações importantes
            4. Se houver muitos resultados, mencione isso
            5. Seja específico com números e dados
            
            Resposta:
            """
            
            response = self.ai_service.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"Erro ao formatar com IA, usando fallback: {e}")
            return self._format_query_result(question, result, sql_query)
    
    def _is_database_query(self, pergunta: str) -> bool:
        """
        Determina se a pergunta requer consulta ao banco de dados
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            bool: True se requer consulta ao banco
        """
        # Palavras-chave que indicam necessidade de dados específicos
        database_keywords = [
            'quantos', 'quantas', 'total', 'soma', 'média', 'máximo', 'mínimo',
            'funcionários', 'matrícula', 'cargo', 'sindicato', 'valor', 'vr',
            'excluídos', 'afastados', 'desligados', 'estagiários', 'aprendizes',
            'férias', 'admissões', 'dias úteis', 'por sindicato', 'por cargo',
            'listar', 'mostrar', 'encontrar', 'buscar', 'filtrar'
        ]
        
        pergunta_lower = pergunta.lower()
        return any(keyword in pergunta_lower for keyword in database_keywords)
    
    def _consult_generic(self, pergunta: str) -> str:
        """
        Consulta genérica quando não precisa de dados do banco
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            str: Resposta genérica
        """
        pergunta_lower = pergunta.lower()
        
        if 'vr' in pergunta_lower and ('o que é' in pergunta_lower or 'como funciona' in pergunta_lower):
            return """🍽️ **VR (Vale Refeição)** é um benefício trabalhista que permite aos funcionários adquirir refeições em estabelecimentos credenciados. No sistema, é calculado baseado nos dias úteis trabalhados e valores por sindicato."""
        
        elif 'como funciona' in pergunta_lower and 'sistema' in pergunta_lower:
            return """📋 **Como funciona o cálculo de VR:**

1. **Base:** Dias úteis por sindicato
2. **Ajustes:** Férias, admissões, desligamentos
3. **Valor:** Dias × Valor por dia do sindicato
4. **Divisão:** 80% empresa + 20% funcionário"""
        
        else:
            return """🤖 **Consulta genérica:**

Para obter dados específicos, faça perguntas como:
• 'Quantos funcionários temos?'
• 'Funcionários por sindicato'
• 'Valor total de VR'
• 'Quantos foram excluídos?'

Para informações gerais, pergunte sobre 'como funciona' ou 'o que é VR'."""
    

    def _format_query_result(self, question: str, result: list, sql_query: str) -> str:
        """
        Formata resultado da consulta (fallback)
        
        Args:
            question: Pergunta original
            result: Resultado da consulta SQL
            sql_query: Consulta SQL executada
            
        Returns:
            str: Resultado formatado
        """
        if not result:
            return f"❌ Nenhum resultado encontrado para a consulta."
        
        # Formatação básica
        if len(result) == 1:
            # Resultado único
            row = result[0]
            if len(row) == 1:
                # Uma coluna
                value = list(row.values())[0]
                return f"📊 **{question}**\n\n**Resposta:** {value:,}" if isinstance(value, (int, float)) else f"📊 **{question}**\n\n**Resposta:** {value}"
            else:
                # Múltiplas colunas
                formatted = "📊 **" + question + "**\n\n"
                for key, value in row.items():
                    formatted += f"**{key}:** {value:,}\n" if isinstance(value, (int, float)) else f"**{key}:** {value}\n"
                return formatted
        else:
            # Múltiplos resultados
            formatted = f"📊 **{question}**\n\n"
            for i, row in enumerate(result[:5]):  # Limitar a 5 resultados
                formatted += f"**{i+1}.** "
                for key, value in row.items():
                    formatted += f"{key}: {value:,} " if isinstance(value, (int, float)) else f"{key}: {value} "
                formatted += "\n"
            
            if len(result) > 5:
                formatted += f"\n... e mais {len(result) - 5} resultados"
            
            return formatted


    def get_system_status(self) -> Dict:
        """
        Retorna o status do sistema
        
        Returns:
            Dict: Status do sistema
        """
        db_status = {}
        if self.db_manager:
            try:
                schema_info = self.db_manager.get_schema_info()
                db_status = {
                    "database_available": True,
                    "database_tables": len(schema_info),
                    "database_connected": True
                }
            except:
                db_status = {
                    "database_available": False,
                    "database_tables": 0,
                    "database_connected": False
                }
        else:
            db_status = {
                "database_available": False,
                "database_tables": 0,
                "database_connected": False
            }
        
        return {
            "config_valid": config.validate_config(),
            "ai_available": self.ai_service is not None,
            "data_folder_exists": config.get_data_path().exists(),
            "output_folder_exists": config.get_output_path().exists(),
            "required_files": config.required_files,
            "excluded_positions": config.excluded_positions,
            "company_percentage": config.company_percentage,
            "employee_percentage": config.employee_percentage,
            **db_status
        }
    
    def get_processing_history(self) -> List[Dict]:
        """
        Obtém histórico de processamentos do banco de dados
        
        Returns:
            List[Dict]: Lista de processamentos realizados
        """
        if not self.db_manager:
            return []
        
        try:
            return self.db_manager.get_processing_history()
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def export_database(self) -> bytes:
        """
        Exporta o banco de dados para bytes
        
        Returns:
            bytes: Dados do banco de dados
        """
        if not self.db_manager:
            return None
        
        try:
            return self.db_manager.export_database()
        except Exception as e:
            logger.error(f"Erro ao exportar banco: {e}")
            return None



    def _validate_database_data(self):
        """Valida dados diretamente do banco de dados"""
        try:
            import pandas as pd
            ativos_query = "SELECT * FROM funcionarios_ativos"
            ativos_result = self.db_manager.execute_query(ativos_query)
            
            if not ativos_result:
                return {
                    "total_planilhas": 1,
                    "planilhas_validas": 0,
                    "planilhas_com_problemas": 1,
                    "problemas_por_planilha": {"ativos": ["Nenhum funcionário encontrado no banco"]},
                    "total_problemas": 1
                }
            
            df_ativos = pd.DataFrame(ativos_result)
            spreadsheets = {"ativos": df_ativos}
            return self.validator.get_validation_summary(spreadsheets)
            
        except Exception as e:
            logger.warning(f"Erro na validação do banco: {e}")
            return {
                "total_planilhas": 1,
                "planilhas_validas": 0,
                "planilhas_com_problemas": 1,
                "problemas_por_planilha": {"ativos": [f"Erro na validação: {e}"]},
                "total_problemas": 1
            }
    
    def _process_ai_with_database(self, ano: int, mes: int):
        """Processa dados com IA usando informações do banco de dados"""
        try:
            import pandas as pd
            dados_resumo = {}
            tabelas = ["funcionarios_ativos", "afastados", "estagio", "aprendiz", "exterior", "desligados", "ferias", "admissoes", "sindicatos", "dias_uteis"]
            
            for tabela in tabelas:
                try:
                    count_query = f"SELECT COUNT(*) as total FROM {tabela}"
                    result = self.db_manager.execute_query(count_query)
                    total = result[0]['total'] if result else 0
                    
                    sample_query = f"SELECT * FROM {tabela} LIMIT 3"
                    sample_result = self.db_manager.execute_query(sample_query)
                    
                    # Converter resultado em DataFrame para compatibilidade com IA
                    if sample_result:
                        df_sample = pd.DataFrame(sample_result)
                    else:
                        df_sample = pd.DataFrame()
                    
                    dados_resumo[tabela] = df_sample
                except Exception as e:
                    logger.warning(f"Erro ao obter dados da tabela {tabela}: {e}")
                    dados_resumo[tabela] = pd.DataFrame()
            
            return self.ai_service.process_data_with_ai(dados_resumo, ano, mes)
            
        except Exception as e:
            logger.warning(f"Erro no processamento IA com banco: {e}")
            return {}
    
    def _get_ativos_from_database(self):
        """Obtém funcionários ativos do banco de dados"""
        try:
            import pandas as pd
            ativos_query = "SELECT * FROM funcionarios_ativos"
            ativos_result = self.db_manager.execute_query(ativos_query)
            
            if not ativos_result:
                logger.warning("Nenhum funcionário ativo encontrado no banco")
                return pd.DataFrame()
            
            df_ativos = pd.DataFrame(ativos_result)
            logger.info(f"✅ {len(df_ativos)} funcionários ativos carregados do banco")
            return df_ativos
            
        except Exception as e:
            logger.error(f"Erro ao obter ativos do banco: {e}")
            return pd.DataFrame()

def main():
    """
    Função principal para teste do agente refatorado
    """
    try:
        # Solicitar API key
        api_key = input("🔑 Digite sua API Key da OpenAI: ").strip()
        if not api_key:
            print("❌ API Key é obrigatória!")
            return
        
        # Perguntar sobre banco de dados
        use_db = input("🗄️ Usar banco de dados SQLite? (s/n): ").strip().lower() == 's'
        db_path = None
        if use_db:
            db_path = input("📁 Caminho do banco (Enter para usar memória): ").strip()
            if not db_path:
                db_path = None
        
        agente = VRAgentRefactored(api_key, db_path)
        
        # Mostrar status do sistema
        status = agente.get_system_status()
        print("🤖 Agente VR Refatorado - Status do Sistema:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("\nDigite 'sair' para encerrar.")
        
        while True:
            comando = input("\nDigite um comando (ex: 'processar setembro 2025' ou 'consultar quantos funcionários temos?'): ")
            
            if comando.lower() == 'sair':
                break
            
            if 'processar' in comando.lower():
                # Extrair mês e ano
                partes = comando.lower().split()
                meses = {
                    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
                    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
                    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
                }
                
                mes_texto = next((p for p in partes if p in meses), None)
                ano = next((p for p in partes if p.isdigit() and len(p) == 4), None)
                
                if mes_texto and ano:
                    mes = meses[mes_texto]
                    ano = int(ano)
                    resultado = agente.process_vr_complete(ano, mes, use_database=use_db)
                    
                    if resultado["sucesso"]:
                        print(f"✅ Processamento completo concluído!")
                        print(f"📁 Arquivo salvo: {resultado['arquivo_saida']}")
                        print(f"👥 Funcionários inicial: {resultado['total_funcionarios_inicial']}")
                        print(f"👥 Funcionários final: {resultado['total_funcionarios_final']}")
                        print(f"💰 Total VR: R$ {resultado['total_vr']:,.2f}")
                        print(f"🏢 Total Empresa (80%): R$ {resultado['total_empresa']:,.2f}")
                        print(f"👤 Total Colaborador (20%): R$ {resultado['total_colaborador']:,.2f}")
                        print(f"⚠️ Problemas encontrados: {resultado['problemas_encontrados']}")
                        print(f"🗄️ Usou banco de dados: {resultado.get('use_database', False)}")
                    else:
                        print(f"❌ Erro: {resultado['erro']}")
                else:
                    print("❌ Não foi possível identificar mês e ano.")
            
            elif 'consultar' in comando.lower():
                pergunta = comando.replace('consultar', '').strip()
                resposta = agente.consult_ai(pergunta)
                print(f"🤖 IA: {resposta}")
            
            else:
                print("❌ Comando não reconhecido. Use 'processar' ou 'consultar'.")
    
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
