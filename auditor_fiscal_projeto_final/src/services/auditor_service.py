"""
Serviço de Auditoria - Gerencia resultados de auditoria fiscal
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sqlite3
import json

logger = logging.getLogger(__name__)

class AuditorService:
    """
    Serviço para gerenciar resultados de auditoria fiscal
    """
    
    def __init__(self, db_manager=None):
        """
        Inicializa o serviço de auditoria
        
        Args:
            db_manager: Instância do DatabaseManager
        """
        self.db_manager = db_manager
        self.results_table_name = "auditor_results"
        
    def initialize_results_table(self):
        """Cria a tabela de resultados de auditoria se não existir"""
        try:
            if not self.db_manager:
                logger.warning("DatabaseManager não fornecido")
                return False
            
            conn, cursor = self.db_manager._get_connection()
            
            # Criar tabela de resultados de auditoria
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.db_manager._escape_identifier(self.results_table_name)} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_key TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                document_count INTEGER DEFAULT 0,
                total_value REAL DEFAULT 0.0,
                processing_time_seconds REAL DEFAULT 0.0,
                analysis_type TEXT,
                ai_result TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            
            # Criar índice para melhor performance
            create_index_sql = f"""
            CREATE INDEX IF NOT EXISTS idx_access_key 
            ON {self.db_manager._escape_identifier(self.results_table_name)}(access_key)
            """
            cursor.execute(create_index_sql)
            conn.commit()
            
            logger.info("Tabela de resultados de auditoria criada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar tabela de resultados: {str(e)}")
            return False
    
    def _serialize_ai_result(self, ai_result: Any) -> str:
        """
        Serializa o resultado da IA para JSON, lidando com objetos complexos do CrewAI
        
        Args:
            ai_result: Resultado da análise da IA (pode ser dict, CrewOutput, etc.)
            
        Returns:
            String JSON serializada
        """
        def _convert_to_json_serializable(obj: Any) -> Any:
            """Converte objetos complexos para tipos JSON serializáveis"""
            # Tipos básicos
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            
            # Listas - converter recursivamente
            if isinstance(obj, list):
                return [_convert_to_json_serializable(item) for item in obj]
            
            # Dicionários - converter recursivamente
            if isinstance(obj, dict):
                return {str(k): _convert_to_json_serializable(v) for k, v in obj.items()}
            
            # Objetos CrewOutput e similares - extrair conteúdo
            if hasattr(obj, 'output'):
                try:
                    return _convert_to_json_serializable(obj.output)
                except:
                    return str(obj.output)
            
            if hasattr(obj, 'raw'):
                try:
                    return _convert_to_json_serializable(obj.raw)
                except:
                    return str(obj.raw)
            
            # Objetos com __dict__
            if hasattr(obj, '__dict__'):
                result = {}
                for key, value in obj.__dict__.items():
                    try:
                        result[str(key)] = _convert_to_json_serializable(value)
                    except:
                        result[str(key)] = str(value)
                return result
            
            # Outros objetos - converter para string
            return str(obj)
        
        try:
            # Converter para tipos serializáveis
            serializable_result = _convert_to_json_serializable(ai_result)
            
            # Serializar para JSON
            return json.dumps(serializable_result, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao serializar resultado da IA: {str(e)}")
            # Fallback: converter tudo para string
            return json.dumps({
                'error': f'Serialization error: {str(e)}',
                'result_str': str(ai_result),
                'error_type': type(ai_result).__name__
            }, ensure_ascii=False)
    
    def save_audit_result(
        self,
        access_key: str,
        document_count: int,
        total_value: float,
        processing_time_seconds: float,
        analysis_type: str,
        ai_result: Any,
        status: str = "completed"
    ) -> Optional[int]:
        """
        Salva um resultado de auditoria
        
        Args:
            access_key: Chave de acesso identificando a sessão/auditoria
            document_count: Número de documentos analisados
            total_value: Valor total fiscalizado (R$)
            processing_time_seconds: Tempo de processamento em segundos
            analysis_type: Tipo de análise realizada
            ai_result: Resultado da análise da IA (contém inconsistências no JSON)
            status: Status da auditoria (pending, completed, failed)
        
        Returns:
            ID do registro inserido ou None se já existe análise para esta chave de acesso
        """
        try:
            if not self.db_manager:
                logger.error("DatabaseManager não disponível")
                return None
            
            # Verificar se a tabela existe, se não, criar
            self.initialize_results_table()
            
            conn, cursor = self.db_manager._get_connection()
            
            # Verificar se já existe análise com esta chave de acesso
            check_sql = f"""
            SELECT id, timestamp FROM {self.db_manager._escape_identifier(self.results_table_name)}
            WHERE access_key = ?
            LIMIT 1
            """
            cursor.execute(check_sql, (access_key,))
            existing = cursor.fetchone()
            
            if existing:
                # Análise já existe - não permitir duplicata
                result_id = existing[0]
                timestamp = existing[1]
                logger.warning(f"Análise já existe para access_key: {access_key[:20]}... (ID: {result_id}, criada em: {timestamp})")
                raise ValueError(f"Já existe uma análise para esta chave de acesso. ID: {result_id}, criada em: {timestamp}")
            
            # Serializar resultado da IA - handle CrewOutput and other objects
            ai_result_json = self._serialize_ai_result(ai_result)
            
            # Inserir nova análise (apenas se não existir)
            insert_sql = f"""
            INSERT INTO {self.db_manager._escape_identifier(self.results_table_name)}
            (access_key, timestamp, document_count, total_value,
             processing_time_seconds, analysis_type, ai_result, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_sql, (
                access_key,
                datetime.now(),
                document_count,
                total_value,
                processing_time_seconds,
                analysis_type,
                ai_result_json,
                status
            ))
            
            conn.commit()
            result_id = cursor.lastrowid
            logger.info(f"Nova análise salva com ID: {result_id} para access_key: {access_key[:20]}...")
            
            return result_id
            
        except ValueError as ve:
            # Re-raise ValueError (análise já existe)
            raise ve
        except Exception as e:
            logger.error(f"Erro ao salvar resultado de auditoria: {str(e)}")
            return None
    
    def get_audit_results(self, access_key: str = None) -> List[Dict[str, Any]]:
        """
        Recupera resultados de auditoria
        
        Args:
            access_key: Filtro por chave de acesso (opcional)
        
        Returns:
            Lista de resultados de auditoria
        """
        try:
            if not self.db_manager:
                logger.error("DatabaseManager não disponível")
                return []
            
            conn, cursor = self.db_manager._get_connection()
            
            if access_key:
                select_sql = f"""
                SELECT * FROM {self.db_manager._escape_identifier(self.results_table_name)}
                WHERE access_key = ?
                ORDER BY timestamp DESC
                """
                cursor.execute(select_sql, (access_key,))
            else:
                select_sql = f"""
                SELECT * FROM {self.db_manager._escape_identifier(self.results_table_name)}
                ORDER BY timestamp DESC
                """
                cursor.execute(select_sql)
            
            results = cursor.fetchall()
            
            # Converter para lista de dicionários
            if results:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao recuperar resultados de auditoria: {str(e)}")
            return []
    
    def get_ai_result(self, access_key: str) -> Optional[Dict[str, Any]]:
        """
        Recupera o resultado da IA de uma auditoria
        
        Args:
            access_key: Chave de acesso da auditoria
        
        Returns:
            Resultado da IA como dict ou None se não encontrado
        """
        try:
            if not self.db_manager:
                logger.error("DatabaseManager não disponível")
                return None
            
            conn, cursor = self.db_manager._get_connection()
            
            select_sql = f"""
            SELECT ai_result FROM {self.db_manager._escape_identifier(self.results_table_name)}
            WHERE access_key = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """
            cursor.execute(select_sql, (access_key,))
            
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao recuperar resultado da IA: {str(e)}")
            return None
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """
        Calcula estatísticas agregadas dos resultados de auditoria
        
        Returns:
            Dicionário com estatísticas agregadas
        """
        try:
            if not self.db_manager:
                return {
                    "total_documents": 0,
                    "total_value": 0.0,
                    "total_inconsistencies": 0,
                    "total_processing_time": 0.0,
                    "total_audits": 0,
                    "average_processing_time": 0.0
                }
            
            conn, cursor = self.db_manager._get_connection()
            
            # Verificar se a tabela existe
            cursor.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{self.results_table_name}'
            """)
            
            if not cursor.fetchone():
                return {
                    "total_documents": 0,
                    "total_value": 0.0,
                    "total_inconsistencies": 0,
                    "total_processing_time": 0.0,
                    "total_audits": 0,
                    "average_processing_time": 0.0
                }
            
            # Calcular estatísticas agregadas
            stats_sql = f"""
            SELECT 
                COUNT(*) as total_audits,
                SUM(document_count) as total_documents,
                SUM(total_value) as total_value,
                SUM(inconsistencies_found) as total_inconsistencies,
                SUM(processing_time_seconds) as total_processing_time,
                AVG(processing_time_seconds) as average_processing_time
            FROM {self.db_manager._escape_identifier(self.results_table_name)}
            """
            
            cursor.execute(stats_sql)
            stats = cursor.fetchone()
            
            return {
                "total_documents": stats[1] or 0,
                "total_value": stats[2] or 0.0,
                "total_inconsistencies": stats[3] or 0,
                "total_processing_time": stats[4] or 0.0,
                "total_audits": stats[0] or 0,
                "average_processing_time": stats[5] or 0.0
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {str(e)}")
            return {
                "total_documents": 0,
                "total_value": 0.0,
                "total_inconsistencies": 0,
                "total_processing_time": 0.0,
                "total_audits": 0,
                "average_processing_time": 0.0
            }
    
    def get_recent_audits(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera auditorias recentes
        
        Args:
            limit: Número máximo de resultados
        
        Returns:
            Lista de auditorias recentes
        """
        try:
            if not self.db_manager:
                return []
            
            conn, cursor = self.db_manager._get_connection()
            
            select_sql = f"""
            SELECT * FROM {self.db_manager._escape_identifier(self.results_table_name)}
            ORDER BY timestamp DESC
            LIMIT ?
            """
            
            cursor.execute(select_sql, (limit,))
            results = cursor.fetchall()
            
            if results:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao recuperar auditorias recentes: {str(e)}")
            return []
    
    def generate_access_key(self) -> str:
        """
        Gera uma chave de acesso única para identificar uma sessão de auditoria
        
        Returns:
            Chave de acesso única
        """
        import uuid
        return f"audit_{uuid.uuid4().hex[:12]}"
