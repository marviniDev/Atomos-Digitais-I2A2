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
            nome_saida: Nome do arquivo de saída (opcional)
            use_database: Se True, usa dados do banco de dados
            
        Returns:
            Dict: Resultado do processamento
        """
        logger.info(f"🚀 Iniciando processamento completo de VR para {mes}/{ano}...")
        
        try:
            # 1. Carregar dados para validação (banco já carregado)
            logger.info("📁 Dados já carregados automaticamente, usando banco de dados...")
            # Carregar dados para validação (sem salvar no banco)
            spreadsheets = self.data_loader.load_all_spreadsheets(load_to_db=False)
            
            # 3. Validar estrutura e qualidade dos dados
            logger.info("🔍 Validando dados...")
            validation_summary = self.validator.get_validation_summary(spreadsheets)
            
            if validation_summary["total_problemas"] > 0:
                logger.warning(f"⚠️ Encontrados {validation_summary['total_problemas']} problemas nos dados")
            
            # 4. Processar com IA (se disponível)
            insights_ia = {}
            if self.ai_service:
                logger.info("🤖 Processando com IA...")
                insights_ia = self.ai_service.process_data_with_ai(spreadsheets, ano, mes)
            
            # 5. Aplicar exclusões
            logger.info("🚫 Aplicando exclusões...")
            df_base = spreadsheets["ativos"].copy()
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
                nome_saida = f"VR_{ano}_{mes:02d}_Processado_Completo.xlsx"
            
            logger.info("💾 Salvando arquivo final...")
            caminho_saida = self.report_generator.save_complete_report(
                df_final, df_resumo, df_validacoes, df_insights, df_statistics, nome_saida
            )
            
            # 11. Preparar resultado
            problemas = df_validacoes[df_validacoes['Problema'] != 'ok']
            
            resultado = {
                "sucesso": True,
                "arquivo_saida": caminho_saida,
                "total_funcionarios_inicial": len(spreadsheets["ativos"]),
                "total_funcionarios_final": len(df_final),
                "total_vr": df_final["VR_Total"].sum(),
                "total_empresa": df_final["%_Empresa"].sum(),
                "total_colaborador": df_final["%_Colaborador"].sum(),
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
        Permite fazer consultas diretas à IA sobre os dados de VR
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            str: Resposta da IA
        """
        try:
            # Carregar dados atuais se disponível
            spreadsheets = {}
            if config.get_data_path().exists():
                spreadsheets = self.data_loader.load_all_spreadsheets(load_to_db=False)
            
            # Preparar dados de contexto
            context_data = {}
            for nome, df in spreadsheets.items():
                context_data[nome] = {
                    "linhas": len(df),
                    "colunas": list(df.columns),
                    "amostra": df.head(3).to_dict('records') if len(df) > 0 else []
                }
            
            # Se IA disponível, usar IA
            if self.ai_service:
                return self.ai_service.consult_ai(pergunta, context_data)
            
            # Se IA não disponível, usar análise local
            return self._analyze_data_locally(pergunta, context_data)
            
        except Exception as e:
            logger.error(f"Erro na consulta IA: {e}")
            return f"Erro ao consultar dados: {e}"
    
    def consult_ai_with_database(self, pergunta: str) -> str:
        """
        Permite fazer consultas diretas à IA usando dados do banco de dados
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            str: Resposta da IA
        """
        try:
            if not self.db_manager:
                return "❌ Banco de dados não disponível para consultas"
            
            # Obter schema do banco
            schema_info = self.db_manager.get_schema_info()
            
            # Preparar contexto com dados do banco
            context_data = {}
            for table_name, info in schema_info.items():
                # Obter contagem de registros
                count_query = f"SELECT COUNT(*) as total FROM {table_name}"
                count_result = self.db_manager.execute_query(count_query)
                total_records = count_result[0]['total'] if count_result else 0
                
                context_data[table_name] = {
                    "linhas": total_records,
                    "colunas": info['columns'],
                    "tipos": info['types']
                }
            
            # Se IA disponível, usar IA
            if self.ai_service:
                return self.ai_service.consult_ai(pergunta, context_data)
            
            # Se IA não disponível, usar análise local
            return self._analyze_data_locally(pergunta, context_data)
            
        except Exception as e:
            logger.error(f"Erro na consulta IA com banco: {e}")
            return f"Erro ao consultar dados do banco: {e}"
    
    def _analyze_data_locally(self, pergunta: str, context_data: Dict) -> str:
        """
        Analisa dados localmente quando IA não está disponível
        
        Args:
            pergunta: Pergunta do usuário
            context_data: Dados de contexto
            
        Returns:
            str: Resposta baseada em análise local
        """
        pergunta_lower = pergunta.lower()
        
        # Análise de sindicatos (verificar primeiro para evitar conflito com "existem")
        if any(palavra in pergunta_lower for palavra in ['sindicato', 'sindicatos']):
            if 'sindicatos' in context_data:
                total_sindicatos = context_data['sindicatos']['linhas']
                return f"📊 **Total de sindicatos:** {total_sindicatos}\n\n💡 *Análise baseada nos dados carregados da planilha Sindicatos.xlsx*"
            else:
                return "❌ Não foi possível carregar os dados de sindicatos. Verifique se a planilha Sindicatos.xlsx está na pasta data/input/"
        
        # Análise de férias
        elif any(palavra in pergunta_lower for palavra in ['ferias', 'férias', 'ausencia', 'ausência', 'estao de ferias']):
            if 'ferias' in context_data:
                total_ferias = context_data['ferias']['linhas']
                return f"📊 **Funcionários com férias:** {total_ferias}\n\n💡 *Análise baseada nos dados carregados da planilha Ferias.xlsx*"
            else:
                return "❌ Não foi possível carregar os dados de férias. Verifique se a planilha Ferias.xlsx está na pasta data/input/"
        
        # Análise de afastados
        elif any(palavra in pergunta_lower for palavra in ['afastado', 'afastados', 'licenca', 'licença']):
            if 'afastados' in context_data:
                total_afastados = context_data['afastados']['linhas']
                return f"📊 **Funcionários afastados:** {total_afastados}\n\n💡 *Análise baseada nos dados carregados da planilha Afastados.xlsx*"
            else:
                return "❌ Não foi possível carregar os dados de afastados. Verifique se a planilha Afastados.xlsx está na pasta data/input/"
        
        # Análise de desligados
        elif any(palavra in pergunta_lower for palavra in ['desligado', 'desligados', 'demitido', 'demitidos', 'foram desligados']):
            if 'desligados' in context_data:
                total_desligados = context_data['desligados']['linhas']
                return f"📊 **Funcionários desligados:** {total_desligados}\n\n💡 *Análise baseada nos dados carregados da planilha Desligados.xlsx*"
            else:
                return "❌ Não foi possível carregar os dados de desligados. Verifique se a planilha Desligados.xlsx está na pasta data/input/"
        
        # Análise de admissões
        elif any(palavra in pergunta_lower for palavra in ['admissao', 'admissão', 'admitido', 'admitidos', 'novo', 'novos']):
            if 'admissoes' in context_data:
                total_admissoes = context_data['admissoes']['linhas']
                return f"📊 **Novas admissões:** {total_admissoes}\n\n💡 *Análise baseada nos dados carregados da planilha Admissoes.xlsx*"
            else:
                return "❌ Não foi possível carregar os dados de admissões. Verifique se a planilha Admissoes.xlsx está na pasta data/input/"
        
        # Análise de estagiários
        elif any(palavra in pergunta_lower for palavra in ['estagiario', 'estagiários', 'estagio', 'estágio']):
            if 'estagio' in context_data:
                total_estagio = context_data['estagio']['linhas']
                return f"📊 **Estagiários:** {total_estagio}\n\n💡 *Análise baseada nos dados carregados da planilha Estagio.xlsx*"
            else:
                return "❌ Não foi possível carregar os dados de estagiários. Verifique se a planilha Estagio.xlsx está na pasta data/input/"
        
        # Análise de aprendizes
        elif any(palavra in pergunta_lower for palavra in ['aprendiz', 'aprendizes']):
            if 'aprendiz' in context_data:
                total_aprendiz = context_data['aprendiz']['linhas']
                return f"📊 **Aprendizes:** {total_aprendiz}\n\n💡 *Análise baseada nos dados carregados da planilha Aprendiz.xlsx*"
            else:
                return "❌ Não foi possível carregar os dados de aprendizes. Verifique se a planilha Aprendiz.xlsx está na pasta data/input/"
        
        # Análise de exterior
        elif any(palavra in pergunta_lower for palavra in ['exterior', 'fora', 'internacional']):
            if 'exterior' in context_data:
                total_exterior = context_data['exterior']['linhas']
                return f"📊 **Funcionários no exterior:** {total_exterior}\n\n💡 *Análise baseada nos dados carregados da planilha Exterior.xlsx*"
            else:
                return "❌ Não foi possível carregar os dados de exterior. Verifique se a planilha Exterior.xlsx está na pasta data/input/"
        
        # Análise de funcionários (verificar por último para evitar conflitos)
        elif any(palavra in pergunta_lower for palavra in ['funcionario', 'funcionários', 'colaborador', 'colaboradores', 'pessoas', 'existem']):
            if 'funcionarios_ativos' in context_data:
                total_ativos = context_data['funcionarios_ativos']['linhas']
                return f"📊 **Total de funcionários ativos:** {total_ativos:,}\n\n💡 *Análise baseada nos dados carregados da planilha Ativos.xlsx*"
            elif 'ativos' in context_data:
                total_ativos = context_data['ativos']['linhas']
                return f"📊 **Total de funcionários ativos:** {total_ativos:,}\n\n💡 *Análise baseada nos dados carregados da planilha Ativos.xlsx*"
            else:
                return "❌ Não foi possível carregar os dados de funcionários. Verifique se a planilha Ativos.xlsx está na pasta data/input/"
        
        # Resumo geral
        elif any(palavra in pergunta_lower for palavra in ['resumo', 'total', 'geral', 'estatistica', 'estatística']):
            resumo = "📊 **Resumo dos Dados Carregados:**\n\n"
            
            for nome, dados in context_data.items():
                if dados['linhas'] > 0:
                    resumo += f"• **{nome.title()}:** {dados['linhas']:,} registros\n"
            
            resumo += "\n💡 *Análise baseada nos dados carregados das planilhas*"
            return resumo
        
        # Resposta padrão
        else:
            resumo = f"🤖 **Análise Local de Dados**\n\nPergunta: {pergunta}\n\n📊 **Dados disponíveis:**\n"
            for nome, dados in context_data.items():
                if dados['linhas'] > 0:
                    resumo += f"• {nome.title()}: {dados['linhas']:,} registros\n"
            resumo += "\n💡 *Para análise mais avançada, configure a chave da API OpenAI*"
            return resumo
    
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
                if use_db:
                    resposta = agente.consult_ai_with_database(pergunta)
                else:
                    resposta = agente.consult_ai(pergunta)
                print(f"🤖 IA: {resposta}")
            
            else:
                print("❌ Comando não reconhecido. Use 'processar' ou 'consultar'.")
    
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main()
