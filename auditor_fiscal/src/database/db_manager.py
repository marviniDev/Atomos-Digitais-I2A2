"""
Gerenciador de banco de dados SQLite
"""
from pathlib import Path
import sqlite3
import tempfile
import logging
from typing import Dict, List, Any, Optional
import threading

from config.settings import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Gerenciador de banco de dados para análise de dados CSV
    
    Responsabilidades:
    - Gerenciar conexões com SQLite
    - Criar tabelas a partir de dados CSV
    - Executar consultas SQL
    - Exportar banco de dados
    - Gerenciar schema
    """
    
    def __init__(self):
        """Inicializa o gerenciador de banco de dados"""
        self.conn = None
        self.cursor = None
        self.db_path = None
        self._local = threading.local()
        
        logger.info("DatabaseManager inicializado")
    
    def initialize(self, use_file: bool = False, force_clean: bool = False):
        """
        Inicializa o banco de dados
        
        Args:
            use_file: Se True, usa arquivo em disco; se False, usa memória
            force_clean: Se True, força limpeza do banco; se False, preserva dados existentes
        """
        try:
            if use_file:
                # Usar arquivo em disco
                self.db_path = str(config.get_db_path())
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
                self._local.conn = sqlite3.connect(self.db_path)
                logger.info(f"Banco de dados inicializado em arquivo: {self.db_path}")
            else:
                # Usar memória
                self._local.conn = sqlite3.connect(':memory:')
                self.db_path = ':memory:'
                logger.info("Banco de dados inicializado em memória")
            
            self._local.cursor = self._local.conn.cursor()
            
            # Só limpar se forçado ou se for banco em memória
            if force_clean or not use_file:
                self._clean_database_completely()
            else:
                logger.info("Banco de dados preservado - dados existentes mantidos")
            
            return self
            
        except Exception as e:
            error_msg = f"Erro ao inicializar banco de dados: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def auto_initialize_with_csv(self, input_path: Path = None, force_reload: bool = False) -> Dict[str, Any]:
        """
        Inicializa o banco de dados e carrega automaticamente arquivos CSV
        
        Args:
            input_path: Caminho da pasta com arquivos CSV (padrão: data/input)
            force_reload: Se True, força recarregamento mesmo se cache existe
            
        Returns:
            Dicionário com informações dos arquivos carregados
        """
        try:
            # Verificar se já existe conexão ativa e dados carregados
            if not force_reload and self._has_active_connection() and self._has_data():
                logger.info("Banco já inicializado com dados - usando conexão existente")
                return {"status": "cached", "message": "Dados carregados do banco existente"}
            
            # Definir caminho padrão se não especificado
            if input_path is None:
                input_path = Path(__file__).parent.parent.parent / "data" / "input"
            
            logger.info(f"Inicialização automática com CSV em: {input_path}")
            
            # Verificar se pasta existe
            if not input_path.exists():
                logger.info("Pasta data/input não encontrada - criando...")
                input_path.mkdir(parents=True, exist_ok=True)
                return {"status": "no_files", "message": "Pasta criada, nenhum arquivo encontrado"}
            
            # Buscar arquivos CSV
            csv_files = list(input_path.glob("*.csv"))
            
            if not csv_files:
                logger.info("Nenhum arquivo CSV encontrado em data/input")
                return {"status": "no_files", "message": "Nenhum arquivo CSV encontrado"}
            
            # Verificar se precisa recarregar baseado em hash dos arquivos
            current_file_hashes = self._get_file_hashes(csv_files)
            cached_hashes = getattr(self, '_file_hashes', {})
            
            # Se os hashes são iguais e não é reload forçado, usar cache
            if not force_reload and current_file_hashes == cached_hashes and self._has_data():
                logger.info("Arquivos não mudaram - usando cache do banco de dados")
                return {"status": "cached", "message": "Dados carregados do cache"}
            
            # Verificar se banco de dados já existe e tem dados
            db_path = config.get_db_path()
            if not force_reload and db_path.exists() and self._database_file_has_data(db_path):
                logger.info("Banco de dados existente encontrado - carregando dados existentes")
                self.initialize(use_file=True, force_clean=False)
                return {"status": "cached", "message": "Dados carregados do banco existente"}
            
            logger.info(f"Encontrados {len(csv_files)} arquivos CSV em data/input")
            
            # Inicializar banco de dados (só limpar se for reload forçado)
            self.initialize(use_file=True, force_clean=force_reload)
            
            # Importar FileProcessor para processar CSVs
            from data_loader.file_processor import FileProcessor
            file_processor = FileProcessor()
            
            tables_info = {}
            loaded_files = []
            
            # Processar cada arquivo CSV
            for csv_file in csv_files:
                try:
                    logger.info(f"Processando arquivo: {csv_file.name}")
                    
                    # Ler arquivo CSV com detecção automática de separador e encoding
                    df = file_processor._process_csv_file(str(csv_file))
                    
                    # Nome da tabela baseado no nome do arquivo
                    table_name = self._sanitize_table_name(csv_file.stem)
                    
                    # Converter DataFrame para lista de dicionários
                    data = df.to_dict('records')
                    
                    # Criar tabela
                    self.create_table_from_csv(table_name, data)
                    
                    # Armazenar informações
                    tables_info[table_name] = {
                        "columns": list(df.columns),
                        "rows": len(df),
                        "fileName": csv_file.name
                    }
                    
                    loaded_files.append(csv_file.name)
                    logger.info(f"Tabela {table_name} criada com {len(df)} linhas")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar {csv_file.name}: {str(e)}")
                    continue
            
            if tables_info:
                # Armazenar hashes dos arquivos para cache
                self._file_hashes = current_file_hashes
                
                logger.info(f"Carregamento automático concluído: {len(tables_info)} tabelas")
                return {
                    "status": "success",
                    "tables_info": tables_info,
                    "loaded_files": loaded_files,
                    "message": f"{len(tables_info)} tabelas carregadas com sucesso"
                }
            else:
                logger.warning("Nenhum arquivo CSV foi carregado com sucesso")
                return {"status": "error", "message": "Nenhum arquivo CSV foi carregado com sucesso"}
                
        except Exception as e:
            logger.error(f"Erro na inicialização automática: {str(e)}")
            return {"status": "error", "message": f"Erro na inicialização automática: {str(e)}"}
    
    def _has_active_connection(self) -> bool:
        """Verifica se existe uma conexão ativa com o banco de dados"""
        try:
            if hasattr(self._local, 'conn') and self._local.conn:
                # Testar a conexão
                cursor = self._local.conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
        except Exception:
            pass
        return False
    
    def _get_file_hashes(self, csv_files):
        """Calcula hash dos arquivos para detectar mudanças"""
        import hashlib
        file_hashes = {}
        
        for csv_file in csv_files:
            try:
                with open(csv_file, 'rb') as f:
                    content = f.read()
                    file_hash = hashlib.md5(content).hexdigest()
                    file_hashes[csv_file.name] = file_hash
            except Exception as e:
                logger.warning(f"Erro ao calcular hash de {csv_file.name}: {e}")
                
        return file_hashes
    
    def _has_data(self) -> bool:
        """Verifica se o banco de dados tem dados"""
        try:
            conn, cursor = self._get_connection()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            return len(tables) > 0
        except Exception:
            return False
    
    def _database_file_has_data(self, db_path: Path) -> bool:
        """Verifica se um arquivo de banco de dados tem dados"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()
            conn.close()
            return len(tables) > 0
        except Exception:
            return False
    
    def _sanitize_table_name(self, filename: str) -> str:
        """Sanitiza nome do arquivo para nome de tabela"""
        # Converter para minúsculas
        table_name = filename.lower()
        
        # Remover extensão
        table_name = table_name.replace('.csv', '')
        
        # Mapear nomes específicos para nomes padronizados
        table_mapping = {
            '202505_nfe_notafiscal': 'nfe_notas_fiscais',
            '202505_nfe_notafiscalitem': 'nfe_itens_nota'
        }
        
        if table_name in table_mapping:
            return table_mapping[table_name]
        
        # Substituir caracteres não alfanuméricos por underscore
        table_name = ''.join(c if c.isalnum() else '_' for c in table_name)
        
        # Garantir que comece com letra
        if not table_name[0].isalpha():
            table_name = 't_' + table_name
        
        # Remover underscores consecutivos
        while '__' in table_name:
            table_name = table_name.replace('__', '_')
        
        # Remover underscores no final
        table_name = table_name.strip('_')
        
        return table_name
    
    def _get_connection(self):
        """Obtém conexão para a thread atual"""
        if not hasattr(self._local, 'conn'):
            self.initialize(use_file=True)
        return self._local.conn, self._local.cursor
    
    def _escape_identifier(self, identifier: str) -> str:
        """Escapa identificador SQLite (nome de tabela ou coluna)"""
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'
    
    def _sanitize_column_name(self, column_name: str) -> str:
        """
        Sanitiza nome de coluna para SQLite
        
        Args:
            column_name: Nome original da coluna
            
        Returns:
            Nome sanitizado
        """
        # Converter para minúsculas
        sanitized = column_name.lower()
        
        # Substituir espaços por underscores
        sanitized = sanitized.replace(' ', '_')
        
        # Remover caracteres especiais exceto underscores
        sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in sanitized)
        
        # Remover underscores consecutivos
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')
        
        # Remover underscores no início e fim
        sanitized = sanitized.strip('_')
        
        return sanitized
    
    def create_table_from_csv(self, table_name: str, data: List[Dict[str, Any]]) -> None:
        """
        Cria tabela a partir de dados CSV
        
        Args:
            table_name: Nome da tabela
            data: Dados da tabela
        """
        if not data:
            logger.warning(f"Nenhum dado fornecido para tabela {table_name}")
            return
        
        try:
            conn, cursor = self._get_connection()
            
            # Obter colunas originais e sanitizadas
            original_columns = list(data[0].keys())
            sanitized_columns = [self._sanitize_column_name(col) for col in original_columns]
            
            # Criar mapeamento de colunas
            column_mapping = dict(zip(original_columns, sanitized_columns))
            
            # Definir campos adicionais para tabelas NFe
            additional_columns = self._get_additional_nfe_columns(table_name)
            
            # Criar tabela com colunas sanitizadas + campos adicionais
            all_columns = sanitized_columns + list(additional_columns.keys())
            escaped_columns = [self._escape_identifier(col) for col in sanitized_columns]
            
            # Definir tipos de coluna
            column_definitions = []
            for col in sanitized_columns:
                column_definitions.append(f'{self._escape_identifier(col)} TEXT')
            
            for col, col_type in additional_columns.items():
                column_definitions.append(f'{self._escape_identifier(col)} {col_type}')
            
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self._escape_identifier(table_name)} (
                {', '.join(column_definitions)}
            )
            """
            
            cursor.execute(create_table_sql)
            logger.info(f"Tabela {table_name} criada com {len(all_columns)} colunas ({len(sanitized_columns)} originais + {len(additional_columns)} adicionais)")
            
            # Inserir dados
            placeholders = ', '.join(['?' for _ in sanitized_columns])
            insert_sql = f"""
            INSERT INTO {self._escape_identifier(table_name)} ({', '.join(escaped_columns)})
            VALUES ({placeholders})
            """
            
            # Transformar dados para usar nomes sanitizados
            transformed_data = []
            for row in data:
                transformed_row = [str(row[orig_col]) for orig_col in original_columns]
                transformed_data.append(transformed_row)
            
            cursor.executemany(insert_sql, transformed_data)
            conn.commit()
            
            logger.info(f"Dados inseridos na tabela {table_name}: {len(transformed_data)} linhas")
            
        except Exception as e:
            error_msg = f"Erro ao criar tabela {table_name}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Obtém informações do schema do banco
        
        Returns:
            Dicionário com informações das tabelas
        """
        try:
            conn, cursor = self._get_connection()
            schema_info = {}
            
            # Obter lista de tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                
                # Obter informações das colunas
                cursor.execute(f"PRAGMA table_info({self._escape_identifier(table_name)})")
                columns = cursor.fetchall()
                
                # Obter número de linhas
                cursor.execute(f"SELECT COUNT(*) FROM {self._escape_identifier(table_name)}")
                row_count = cursor.fetchone()[0]
                
                schema_info[table_name] = {
                    'columns': [col[1] for col in columns],
                    'types': [col[2] for col in columns],
                    'row_count': row_count
                }
            
            logger.info(f"Schema obtido: {len(schema_info)} tabelas")
            return schema_info
            
        except Exception as e:
            error_msg = f"Erro ao obter schema: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executa consulta SQL
        
        Args:
            query: Consulta SQL
            
        Returns:
            Lista de resultados
        """
        try:
            conn, cursor = self._get_connection()
            
            logger.info(f"Executando consulta: {query[:100]}...")
            cursor.execute(query)
            
            # Obter nomes das colunas
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Converter resultados para lista de dicionários
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            logger.info(f"Consulta executada: {len(results)} resultados")
            return results
            
        except Exception as e:
            error_msg = f"Erro ao executar consulta: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def export_database(self) -> Optional[bytes]:
        """
        Exporta banco de dados para bytes
        
        Returns:
            Bytes do banco de dados ou None se erro
        """
        try:
            conn, _ = self._get_connection()
            if not conn:
                logger.warning("Nenhuma conexão ativa para exportar")
                return None
            
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                # Exportar banco em memória para arquivo temporário
                backup = sqlite3.connect(tmp.name)
                conn.backup(backup)
                backup.close()
                
                # Ler arquivo e retornar bytes
                with open(tmp.name, 'rb') as f:
                    db_bytes = f.read()
                
                logger.info(f"Banco de dados exportado: {len(db_bytes)} bytes")
                return db_bytes
                
        except Exception as e:
            error_msg = f"Erro ao exportar banco de dados: {str(e)}"
            logger.error(error_msg)
            return None
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Obtém informações de uma tabela específica
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Informações da tabela
        """
        try:
            conn, cursor = self._get_connection()
            
            # Obter informações das colunas
            cursor.execute(f"PRAGMA table_info({self._escape_identifier(table_name)})")
            columns = cursor.fetchall()
            
            # Obter número de linhas
            cursor.execute(f"SELECT COUNT(*) FROM {self._escape_identifier(table_name)}")
            row_count = cursor.fetchone()[0]
            
            return {
                'name': table_name,
                'columns': [col[1] for col in columns],
                'types': [col[2] for col in columns],
                'row_count': row_count
            }
            
        except Exception as e:
            error_msg = f"Erro ao obter informações da tabela {table_name}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def close(self):
        """Fecha conexão com banco de dados"""
        try:
            if hasattr(self._local, 'conn') and self._local.conn:
                self._local.conn.close()
                logger.info("Conexão com banco de dados fechada")
        except Exception as e:
            logger.warning(f"Erro ao fechar conexão: {str(e)}")

    def _clean_database_completely(self) -> None:
        """Remove completamente todos os dados e recria a estrutura do banco"""
        conn, cursor = self._get_connection()
        
        try:
            # Desabilitar foreign keys temporariamente
            cursor.execute('PRAGMA foreign_keys = OFF')
            
            # Obter lista de todas as tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()

            # Deletar todas as tabelas
            for table in tables:
                table_name = table[0]
                cursor.execute(f'DROP TABLE IF EXISTS {self._escape_identifier(table_name)}')
                logger.info(f'Tabela {table_name} removida')
            
            # Limpar sequências (se a tabela existir)
            try:
                cursor.execute('DELETE FROM sqlite_sequence')
            except sqlite3.OperationalError:
                # Tabela sqlite_sequence não existe, isso é normal em bancos vazios
                pass
            
            # Reabilitar foreign keys
            cursor.execute('PRAGMA foreign_keys = ON')
        except Exception as e:
            logger.error(f'Erro ao limpar banco: {e}')
            conn.rollback()
            raise
        finally:
            # Reabilitar foreign keys em caso de erro
            try:
                cursor.execute('PRAGMA foreign_keys = ON')
            except:
                pass
    
    def _get_additional_nfe_columns(self, table_name: str) -> Dict[str, str]:
        """
        Retorna campos adicionais para tabelas NFe baseado no nome da tabela
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Dicionário com nome da coluna e tipo SQLite
        """
        if table_name == 'nfe_notas_fiscais':
            return {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'data_saida': 'TEXT',
                'tipo_nf': 'TEXT',
                'ambiente': 'TEXT',
                'finalidade': 'TEXT',
                'processo_emissao': 'TEXT',
                'versao_processo': 'TEXT',
                'emit_fantasia': 'TEXT',
                'emit_crt': 'TEXT',
                'dest_cpf': 'TEXT',
                'dest_ie': 'TEXT',
                'valor_produtos': 'REAL DEFAULT 0.0',
                'valor_frete': 'REAL DEFAULT 0.0',
                'valor_seguro': 'REAL DEFAULT 0.0',
                'valor_desconto': 'REAL DEFAULT 0.0',
                'valor_outros': 'REAL DEFAULT 0.0',
                'valor_icms': 'REAL DEFAULT 0.0',
                'valor_ipi': 'REAL DEFAULT 0.0',
                'valor_pis': 'REAL DEFAULT 0.0',
                'valor_cofins': 'REAL DEFAULT 0.0',
                'arquivo_origem': 'TEXT',
                'data_processamento': 'TEXT',
                'versao_xml': 'TEXT',
                'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP'
            }
        elif table_name == 'nfe_itens_nota':
            return {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'nota_id': 'INTEGER',
                'codigo_produto': 'TEXT',
                'codigo_ean': 'TEXT',
                'unidade_tributavel': 'TEXT',
                'quantidade_tributavel': 'REAL DEFAULT 0.0',
                'valor_unitario_tributavel': 'REAL DEFAULT 0.0',
                'valor_frete': 'REAL DEFAULT 0.0',
                'valor_seguro': 'REAL DEFAULT 0.0',
                'valor_desconto': 'REAL DEFAULT 0.0',
                'valor_outros': 'REAL DEFAULT 0.0',
                'indicador_total': 'TEXT',
                'icms_origem': 'TEXT',
                'icms_cst': 'TEXT',
                'icms_csosn': 'TEXT',
                'icms_modalidade_bc': 'TEXT',
                'icms_base_calculo': 'REAL DEFAULT 0.0',
                'icms_aliquota': 'REAL DEFAULT 0.0',
                'icms_valor': 'REAL DEFAULT 0.0',
                'icms_modalidade_bc_st': 'TEXT',
                'icms_base_calculo_st': 'REAL DEFAULT 0.0',
                'icms_aliquota_st': 'REAL DEFAULT 0.0',
                'icms_valor_st': 'REAL DEFAULT 0.0',
                'icms_percentual_reducao': 'REAL DEFAULT 0.0',
                'icms_valor_desoneracao': 'REAL DEFAULT 0.0',
                'icms_motivo_desoneracao': 'TEXT',
                'ipi_codigo_enquadramento': 'TEXT',
                'ipi_cst': 'TEXT',
                'ipi_base_calculo': 'REAL DEFAULT 0.0',
                'ipi_aliquota': 'REAL DEFAULT 0.0',
                'ipi_quantidade': 'REAL DEFAULT 0.0',
                'ipi_valor_unitario': 'REAL DEFAULT 0.0',
                'ipi_valor': 'REAL DEFAULT 0.0',
                'pis_cst': 'TEXT',
                'pis_base_calculo': 'REAL DEFAULT 0.0',
                'pis_aliquota': 'REAL DEFAULT 0.0',
                'pis_quantidade': 'REAL DEFAULT 0.0',
                'pis_valor_aliquota': 'REAL DEFAULT 0.0',
                'pis_valor': 'REAL DEFAULT 0.0',
                'cofins_cst': 'TEXT',
                'cofins_base_calculo': 'REAL DEFAULT 0.0',
                'cofins_aliquota': 'REAL DEFAULT 0.0',
                'cofins_quantidade': 'REAL DEFAULT 0.0',
                'cofins_valor_aliquota': 'REAL DEFAULT 0.0',
                'cofins_valor': 'REAL DEFAULT 0.0',
                'informacoes_adicionais': 'TEXT',
                'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP'
            }
        else:
            return {}