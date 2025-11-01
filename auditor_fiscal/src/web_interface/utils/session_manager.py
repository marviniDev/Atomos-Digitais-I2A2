"""
Gerenciador de sessão para a aplicação Streamlit
"""
import streamlit as st
import logging
from typing import Dict, Any
from pathlib import Path

from config.config_persistence import config_persistence

logger = logging.getLogger(__name__)

class SessionManager:
    """Gerenciador centralizado de sessão"""
    
    def __init__(self):
        logger.info("🔧 Inicializando SessionManager")
        self.initialize_session_state()
        self._auto_initialize_database()
        logger.info("✅ SessionManager inicializado com sucesso")
    
    def _auto_initialize_database(self):
        """Inicializa automaticamente o banco de dados se existir"""
        logger.info("🔍 Verificando inicialização automática do banco de dados")
        # Não re-inicializar se já temos banco e tabelas
        if st.session_state.get('db_manager') and st.session_state.get('tables_info'):
            logger.info("✅ Banco de dados já inicializado (cache)")
            return
        
        # Se temos db_manager mas não temos tables_info, tentar carregar tables_info
        if st.session_state.get('db_manager') and not st.session_state.get('tables_info'):
            try:
                db_manager = st.session_state.db_manager
                schema_info = db_manager.get_schema_info()
                if schema_info:
                    tables_info = {}
                    for table_name, info in schema_info.items():
                        tables_info[table_name] = {
                            "columns": info['columns'],
                            "rows": info['row_count'],
                            "fileName": f"{table_name}.csv"
                        }
                    st.session_state.tables_info = tables_info
                    logger.info(f"Tabelas carregadas: {len(tables_info)}")
            except Exception as e:
                logger.warning(f"Erro ao carregar tables_info do banco existente: {str(e)}")
            return
            
        if not st.session_state.get('db_manager'):
            logger.info("📂 Inicializando novo DatabaseManager...")
            try:
                from database.db_manager import DatabaseManager
                from config.settings import config
                
                db_manager = DatabaseManager()
                db_path = config.get_db_path()
                
                logger.info(f"📁 Caminho do banco de dados: {db_path}")
                
                # Verificar se o banco de dados existe
                if db_path.exists():
                    logger.info(f"✅ Banco de dados existe em: {db_path}")
                    
                    # Inicializar banco de dados a partir do arquivo existente
                    db_manager.initialize(use_file=True, force_clean=False)
                    
                    # Verificar se há tabelas no banco
                    try:
                        schema_info = db_manager.get_schema_info()
                        
                        if schema_info:
                            # Converter schema_info para formato tables_info
                            tables_info = {}
                            for table_name, info in schema_info.items():
                                tables_info[table_name] = {
                                    "columns": info['columns'],
                                    "rows": info['row_count'],
                                    "fileName": f"{table_name}.csv"
                                }
                            
                            # Armazenar no session state
                            st.session_state.db_manager = db_manager
                            st.session_state.tables_info = tables_info
                            
                        else:
                            logger.info("Banco de dados encontrado mas sem tabelas")
                    except Exception as e:
                        logger.warning(f"Erro ao obter schema do banco: {str(e)}")
                        
                else:
                    # Tentar carregar CSV automaticamente se o banco não existir
                    logger.info("Banco de dados não encontrado, tentando carregar CSV automaticamente")
                    result = db_manager.auto_initialize_with_csv()
                    
                    # Verificar se alguma tabela foi carregada
                    if result.get('status') == 'success' and result.get('tables_info'):
                        tables_info = result['tables_info']
                        
                        st.session_state.db_manager = db_manager
                        st.session_state.tables_info = tables_info
                        
                        logger.info(f"CSV carregado automaticamente: {len(tables_info)} tabelas")
                    elif result.get('status') == 'cached' and db_manager._has_data():
                        # Dados carregados do cache, obter schema_info
                        try:
                            schema_info = db_manager.get_schema_info()
                            if schema_info:
                                tables_info = {}
                                for table_name, info in schema_info.items():
                                    tables_info[table_name] = {
                                        "columns": info['columns'],
                                        "rows": info['row_count'],
                                        "fileName": f"{table_name}.csv"
                                    }
                                
                                st.session_state.db_manager = db_manager
                                st.session_state.tables_info = tables_info
                        except Exception as e:
                            logger.warning(f"Erro ao obter schema após cache: {str(e)}")
            except Exception as e:
                logger.error(f"Erro na auto-inicialização do banco: {str(e)}")
    
    def initialize_session_state(self):
        """Inicializa o estado da sessão"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "db_manager" not in st.session_state:
            st.session_state.db_manager = None
        if "tables_info" not in st.session_state:
            st.session_state.tables_info = {}
        if "uploaded_files" not in st.session_state:
            st.session_state.uploaded_files = []
        if "query_history" not in st.session_state:
            st.session_state.query_history = []
        if "api_key" not in st.session_state:
            # Carregar chave API persistida
            persisted_api_key = config_persistence.load_config("api_key", "")
            st.session_state.api_key = persisted_api_key
    
    def get_database_status(self) -> Dict[str, Any]:
        """Obtém o status atual do banco de dados"""
        try:
            status = {
                "has_database": False,
                "connection_valid": False,
                "db_path": None,
                "tables_info": {},
                "tables_count": 0,
                "total_rows": 0
            }
            
            # Verificar se existe db_manager
            if not st.session_state.get('db_manager'):
                return status
            
            status["has_database"] = True
            db_manager = st.session_state.db_manager
            
            # Verificar conexão
            try:
                conn, cursor = db_manager._get_connection()
                if conn and self._is_connection_valid(conn):
                    status["connection_valid"] = True
                    status["db_path"] = getattr(db_manager, 'db_path', ':memory:')
            except Exception:
                pass
            
            # Obter informações das tabelas
            tables_info = st.session_state.get('tables_info', {})
            if tables_info:
                status["tables_info"] = tables_info
                status["tables_count"] = len(tables_info)
                status["total_rows"] = sum(info.get('rows', 0) for info in tables_info.values())
            else:
                # Tentar obter informações diretamente do banco
                try:
                    if status["connection_valid"]:
                        schema_info = db_manager.get_schema_info()
                        if schema_info:
                            # Converter schema_info para formato tables_info
                            tables_info = {}
                            for table_name, info in schema_info.items():
                                tables_info[table_name] = {
                                    "columns": info['columns'],
                                    "rows": info['row_count'],
                                    "fileName": f"{table_name}.csv"
                                }
                            status["tables_info"] = tables_info
                            status["tables_count"] = len(tables_info)
                            status["total_rows"] = sum(info.get('rows', 0) for info in tables_info.values())
                            
                            # Atualizar session_state se necessário
                            if not st.session_state.get('tables_info'):
                                st.session_state.tables_info = tables_info
                except Exception as e:
                    logger.warning(f"Erro ao obter informações do banco: {str(e)}")
            
            return status
            
        except Exception as e:
            logger.error(f"Erro ao obter status do banco: {str(e)}")
            return {
                "has_database": False,
                "connection_valid": False,
                "db_path": None,
                "tables_info": {},
                "tables_count": 0,
                "total_rows": 0
            }
    
    def _is_connection_valid(self, conn) -> bool:
        """Verifica se a conexão com o banco de dados é válida"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception:
            return False
    
    def clear_session_data(self):
        """Limpa todos os dados da sessão"""
        for key in ['db_manager', 'tables_info', 'uploaded_files', 'query_history']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do sistema"""
        db_status = self.get_database_status()
        
        return {
            "database_loaded": db_status["has_database"],
            "tables_count": db_status["tables_count"],
            "total_rows": db_status["total_rows"],
            "connection_valid": db_status["connection_valid"],
            "api_key_configured": bool(st.session_state.get('api_key')),
            "queries_count": len(st.session_state.get('query_history', []))
        }
