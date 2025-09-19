"""
Gerenciador de Banco de Dados SQLite para Sistema VR/VA
Baseado no padrão do agent_csv_analyzer
"""
import sqlite3
import tempfile
import threading
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

class VRDatabaseManager:
    """Gerenciador do banco de dados SQLite para dados de VR/VA"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa o gerenciador do banco de dados
        
        Args:
            db_path: Caminho do arquivo de banco (None para banco em arquivo padrão)
        """
        # Usar arquivo padrão se não especificado
        if db_path is None:
            db_path = "data/vr_database.db"
        
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._local = threading.local()
        
    def initialize(self, db_path: Optional[str] = None) -> 'VRDatabaseManager':
        """
        Inicializa o banco de dados
        
        Args:
            db_path: Caminho do arquivo de banco (None para banco em arquivo padrão)
            
        Returns:
            VRDatabaseManager: Instância do gerenciador
        """
        # Usar arquivo padrão se não especificado
        if db_path is None:
            db_path = self.db_path
        
        self.db_path = db_path
        # Criar diretório se não existir
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local.conn = sqlite3.connect(db_path)
        
        self._local.cursor = self._local.conn.cursor()
        self.conn = self._local.conn
        self.cursor = self._local.cursor
        
                # Limpar banco completamente antes de inicializar
        self._clean_database_completely()
        
        # Criar tabelas
        self._create_tables()
        
        logger.info(f"Banco de dados inicializado: {db_path or 'memória'}")
        return self
    
    def _get_connection(self):
        """Obtém a conexão para a thread atual"""
        if not hasattr(self._local, 'conn'):
            # Sempre usar arquivo, nunca memória
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.cursor = self._local.conn.cursor()
        return self._local.conn, self._local.cursor
    
    def _escape_identifier(self, identifier: str) -> str:
        """Escapa identificador SQLite (nome de tabela ou coluna)"""
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'
    
    def _sanitize_column_name(self, column_name: str) -> str:
        """Transforma nome da coluna para formato SQLite compatível"""
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
    
    def _create_tables(self):
        """Cria as tabelas do banco de dados"""
        conn, cursor = self._get_connection()
        
        # Tabela de funcionários ativos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS funcionarios_ativos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            empresa TEXT,
            cargo TEXT,
            situacao TEXT,
            situaçao TEXT,
            sindicato TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de sindicatos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sindicatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sindicato TEXT NOT NULL UNIQUE,
            valor_dia_sindicato REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de dias úteis
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dias_uteis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sindicato TEXT NOT NULL UNIQUE,
            dias_uteis_sindicato INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de férias
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ferias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            situacao TEXT,
            situaçao TEXT,
            dias_ferias INTEGER,
            dias_comprados INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de afastados
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS afastados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            afastamento_tipo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de desligados
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS desligados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            data_desligamento DATE,
            data_comunicado_desligamento TEXT,
            dias_trabalhados INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de admissões
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admissoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            data_admissao DATE,
            cargo TEXT,
            situacao TEXT,
            situaçao TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de estagiários
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS estagio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            titulo_do_cargo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de aprendizes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS aprendiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            titulo_do_cargo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de exterior
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS exterior (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL,
            valor REAL,
            observacao TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de processamentos (histórico)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS processamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            total_funcionarios_inicial INTEGER,
            total_funcionarios_final INTEGER,
            total_vr REAL,
            total_empresa REAL,
            total_colaborador REAL,
            problemas_encontrados INTEGER,
            arquivo_saida TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        logger.info("Tabelas do banco de dados criadas com sucesso")
    
    def load_spreadsheet_data(self, spreadsheets: Dict[str, pd.DataFrame]) -> None:
        """
        Carrega dados das planilhas para o banco de dados
        
        Args:
            spreadsheets: Dicionário com DataFrames das planilhas
        """
        conn, cursor = self._get_connection()
        
       # Mapeamento de planilhas para tabelas
        table_mapping = {
            'ativos': 'funcionarios_ativos',
            'sindicatos': 'sindicatos',
            'dias_uteis': 'dias_uteis',
            'ferias': 'ferias',
            'afastados': 'afastados',
            'desligados': 'desligados',
            'admissoes': 'admissoes',
            'estagio': 'estagio',
            'aprendiz': 'aprendiz',
            'exterior': 'exterior'
        }
        
        for planilha_name, df in spreadsheets.items():
            if planilha_name in table_mapping and not df.empty:
                table_name = table_mapping[planilha_name]
                self._insert_dataframe_to_table(df, table_name)
                logger.info(f"Dados da planilha '{planilha_name}' carregados na tabela '{table_name}'")
    
    def _insert_dataframe_to_table(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Insere dados de um DataFrame em uma tabela
        
        Args:
            df: DataFrame com os dados
            table_name: Nome da tabela de destino
        """
        conn, cursor = self._get_connection()
        
        # Verificar se a tabela existe antes de inserir dados
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            logger.error(f"❌ Tabela '{table_name}' não existe! Criando tabelas...")
            self._create_tables()
            # Verificar novamente
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                raise ValueError(f"Tabela '{table_name}' não pôde ser criada!")
        
        # Sanitizar nomes das colunas
        df_clean = df.copy()
        df_clean.columns = [self._sanitize_column_name(col) for col in df_clean.columns]
        
        # Preparar dados para inserção
        columns = list(df_clean.columns)
        placeholders = ', '.join(['?' for _ in columns])
        
        # Inserir dados com tratamento melhorado
        inserted_count = 0
        error_count = 0
        
        for _, row in df_clean.iterrows():
            try:
                # Tratar valores especiais
                values = []
                for val in row.values:
                    if pd.isna(val):
                        values.append(None)
                    elif isinstance(val, (int, float)):
                        values.append(val)
                    elif isinstance(val, str):
                        # Limpar strings
                        clean_val = str(val).strip()
                        values.append(clean_val if clean_val else None)
                    else:
                        values.append(str(val))
                
                # Executar inserção
                cursor.execute(
                    f"INSERT INTO {self._escape_identifier(table_name)} ({', '.join([self._escape_identifier(col) for col in columns])}) VALUES ({placeholders})",
                    values
                )
                inserted_count += 1
                
            except Exception as e:
                error_count += 1
                logger.warning(f"Erro ao inserir linha na tabela {table_name}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Tabela {table_name}: {inserted_count} registros inseridos, {error_count} erros")
    
    def clear_all_data(self) -> None:
        """Remove todos os dados das tabelas"""
        conn, cursor = self._get_connection()
        
        tables = [
            'funcionarios_ativos', 'sindicatos', 'dias_uteis', 'ferias',
            'afastados', 'desligados', 'admissoes', 'estagio', 'aprendiz',
            'exterior', 'processamentos'
        ]
        
        for table in tables:
            # Verificar se a tabela existe antes de tentar limpar
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                cursor.execute(f"DELETE FROM {self._escape_identifier(table)}")
            else:
                logger.warning(f"Tabela '{table}' não existe, pulando limpeza")
        
        conn.commit()
        logger.info("Dados das tabelas existentes foram removidos")
    
    
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
            
            # Limpar sequências
            cursor.execute('DELETE FROM sqlite_sequence')
            
            # Reabilitar foreign keys
            cursor.execute('PRAGMA foreign_keys = ON')
            
            conn.commit()
            logger.info('Banco de dados completamente limpo')
            
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

    def get_schema_info(self) -> Dict[str, Any]:
        """Obtém informações do schema do banco"""
        conn, cursor = self._get_connection()
        schema_info = {}
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({self._escape_identifier(table_name)})")
            columns = cursor.fetchall()
            schema_info[table_name] = {
                'columns': [col[1] for col in columns],
                'types': [col[2] for col in columns]
            }
        
        return schema_info
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executa uma consulta SQL e retorna os resultados
        
        Args:
            query: Consulta SQL
            
        Returns:
            List[Dict[str, Any]]: Resultados da consulta
        """
        try:
            conn, cursor = self._get_connection()
            logger.info(f"Executando consulta: {query}")
            cursor.execute(query)
            
            # Para comandos INSERT/UPDATE/DELETE, cursor.description é None
            if cursor.description is None:
                conn.commit()
                logger.info(f"Comando executado com sucesso")
                return []
            
            # Para comandos SELECT, processar resultados
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            logger.info(f"Consulta executada com sucesso. {len(results)} registros retornados")
            return results
            
        except Exception as e:
            logger.error(f"Erro ao executar consulta: {e}")
            raise Exception(f"Erro ao executar consulta: {str(e)}")
    
    def save_processing_result(self, resultado: Dict[str, Any]) -> None:
        """
        Salva resultado de processamento no banco
        
        Args:
            resultado: Dicionário com resultado do processamento
        """
        conn, cursor = self._get_connection()
        
        cursor.execute("""
        INSERT INTO processamentos 
        (ano, mes, total_funcionarios_inicial, total_funcionarios_final, 
         total_vr, total_empresa, total_colaborador, problemas_encontrados, arquivo_saida)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resultado.get('ano'),
            resultado.get('mes'),
            resultado.get('total_funcionarios_inicial'),
            resultado.get('total_funcionarios_final'),
            resultado.get('total_vr'),
            resultado.get('total_empresa'),
            resultado.get('total_colaborador'),
            resultado.get('problemas_encontrados'),
            resultado.get('arquivo_saida')
        ))
        
        conn.commit()
        logger.info("Resultado do processamento salvo no banco")
    
    def get_processing_history(self) -> List[Dict[str, Any]]:
        """Obtém histórico de processamentos"""
        query = """
        SELECT * FROM processamentos 
        ORDER BY created_at DESC
        """
        return self.execute_query(query)
    
    def export_database(self) -> bytes:
        """Exporta o banco de dados para bytes"""
        conn, _ = self._get_connection()
        if not conn:
            return None
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Exportar banco em memória para arquivo temporário
            backup = sqlite3.connect(tmp.name)
            conn.backup(backup)
            backup.close()
            
            # Ler arquivo e retornar conteúdo
            with open(tmp.name, 'rb') as f:
                return f.read()
    
    def close(self):
        """Fecha a conexão com o banco"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
