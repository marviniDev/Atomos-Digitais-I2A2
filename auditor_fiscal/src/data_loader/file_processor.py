"""
Processador de arquivos CSV e ZIP
"""
import sys
from pathlib import Path

# Adicionar src ao path para imports
if Path(__file__).parent.parent not in [Path(p) for p in sys.path]:
    sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import tempfile
import zipfile
import logging
from typing import Dict, List, Any, Optional

import pandas as pd

from database.db_manager import DatabaseManager
from config.settings import config

logger = logging.getLogger(__name__)

class FileProcessor:
    """
    Processador de arquivos para análise de dados
    
    Responsabilidades:
    - Extrair arquivos de ZIP
    - Processar arquivos CSV
    - Validar formatos de arquivo
    - Sanitizar dados
    """
    
    def __init__(self):
        """Inicializa o processador de arquivos"""
        self.supported_formats = config.supported_formats
        self.max_file_size = config.max_file_size_mb * 1024 * 1024  # Converter para bytes
        self.encoding = config.encoding
        
        logger.info("FileProcessor inicializado")
    
    async def extract_csv_from_zip(self, zip_file: Any) -> List[Dict[str, Any]]:
        """
        Extrai arquivos CSV de um arquivo ZIP
        
        Args:
            zip_file: Arquivo ZIP carregado
            
        Returns:
            Lista de dados dos arquivos CSV extraídos
            
        Raises:
            Exception: Se não encontrar arquivos CSV ou houver erro no processamento
        """
        try:
            logger.info("Iniciando extração de arquivos CSV do ZIP")
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Salvar arquivo ZIP temporariamente
                zip_path = os.path.join(tmpdir, "uploaded.zip")
                with open(zip_path, "wb") as f:
                    f.write(zip_file.read())
                
                # Verificar tamanho do arquivo
                file_size = os.path.getsize(zip_path)
                if file_size > self.max_file_size:
                    raise Exception(f"Arquivo muito grande. Máximo permitido: {config.max_file_size_mb}MB")
                
                # Extrair arquivos CSV
                results = []
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    csv_files = [f for f in zip_ref.namelist() if self._is_csv_file(f)]
                    
                    if not csv_files:
                        raise Exception("Nenhum arquivo CSV encontrado no ZIP")
                    
                    logger.info(f"Encontrados {len(csv_files)} arquivos CSV")
                    
                    for csv_file in csv_files:
                        try:
                            # Extrair arquivo
                            file_path = os.path.join(tmpdir, csv_file)
                            zip_ref.extract(csv_file, tmpdir)
                            
                            # Processar CSV
                            df = self._process_csv_file(file_path)
                            
                            results.append({
                                "name": csv_file,
                                "data": df.to_dict(orient="records"),
                                "rows": len(df),
                                "columns": list(df.columns)
                            })
                            
                            logger.info(f"Processado: {csv_file} ({len(df)} linhas)")
                            
                        except Exception as e:
                            logger.warning(f"Erro ao processar {csv_file}: {str(e)}")
                            continue
                
                if not results:
                    raise Exception("Nenhum arquivo CSV válido foi processado")
                
                logger.info(f"Extração concluída: {len(results)} arquivos processados")
                return results
                
        except Exception as e:
            error_msg = f"Erro ao extrair arquivos do ZIP: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _is_csv_file(self, filename: str) -> bool:
        """Verifica se o arquivo é um CSV"""
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in ['.csv'])
    
    def _process_csv_file(self, file_path: str) -> pd.DataFrame:
        """
        Processa um arquivo CSV com detecção automática de separador e encoding
        
        Args:
            file_path: Caminho do arquivo CSV
            
        Returns:
            DataFrame processado
        """
        try:
            # Lista de separadores comuns para testar
            separators = [';', ',', '\t', '|']
            
            # Lista de encodings para testar
            encodings = [self.encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-8-sig']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        logger.info(f"Tentando ler {file_path} com encoding={encoding} e separador='{sep}'")
                        df = pd.read_csv(file_path, encoding=encoding, sep=sep, nrows=5)
                        
                        # Verificar se a leitura foi bem-sucedida (pelo menos 2 colunas)
                        if len(df.columns) >= 2:
                            logger.info(f"✅ Sucesso! Encoding: {encoding}, Separador: '{sep}', Colunas: {len(df.columns)}")
                            
                            # Ler o arquivo completo com os parâmetros corretos
                            df_full = pd.read_csv(file_path, encoding=encoding, sep=sep)
                            
                            return df_full
                            
                    except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as e:
                        logger.debug(f"Falhou com encoding={encoding}, sep='{sep}': {str(e)[:50]}...")
                        continue
                    except Exception as e:
                        logger.debug(f"Erro inesperado com encoding={encoding}, sep='{sep}': {str(e)[:50]}...")
                        continue
            
            # Se chegou aqui, nenhuma combinação funcionou
            raise Exception(f"Não foi possível ler o arquivo {file_path} com nenhuma combinação de encoding/separador testada")
            
        except Exception as e:
            raise Exception(f"Erro ao processar arquivo CSV {file_path}: {str(e)}")
    
    def auto_load_csv_files(self):
        """Carrega automaticamente arquivos CSV da pasta data/input"""
        try:
            # Caminho da pasta de input
            input_path = Path(__file__).parent.parent.parent / "data" / "input"
            
            if not input_path.exists():
                logger.info("Pasta data/input não encontrada - criando...")
                input_path.mkdir(parents=True, exist_ok=True)
                return
            
            # Buscar arquivos CSV
            csv_files = list(input_path.glob("*.csv"))
            
            if not csv_files:
                logger.info("Nenhum arquivo CSV encontrado em data/input")
                return
            
            logger.info(f"Encontrados {len(csv_files)} arquivos CSV em data/input")
            
            # Inicializar banco de dados
            db_manager = DatabaseManager().initialize(use_file=True, force_clean=True)
            tables_info = {}
            loaded_files = []
            
            # Processar cada arquivo CSV
            for csv_file in csv_files:
                try:
                    logger.info(f"Processando arquivo: {csv_file.name}")
                    
                    # Ler arquivo CSV com detecção automática de separador e encoding
                    df = self._process_csv_file(csv_file)
                    
                    # Nome da tabela baseado no nome do arquivo
                    table_name = csv_file.stem
                    
                    # Converter DataFrame para lista de dicionários
                    data = df.to_dict('records')
                    
                    # Criar tabela
                    db_manager.create_table_from_csv(table_name, data)
                    
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
                # Atualizar estado da sessão
                return db_manager, tables_info, loaded_files
            else:
                logger.warning("Nenhum arquivo CSV foi carregado com sucesso")
                return None, None, None
        except Exception as e:
            logger.error(f"Erro no carregamento automático: {str(e)}")
            return None, None, None
    
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e sanitiza o DataFrame
        
        Args:
            df: DataFrame original
            
        Returns:
            DataFrame limpo
        """
        try:
            # Remover linhas completamente vazias
            df = df.dropna(how='all')
            
            # Remover colunas completamente vazias
            df = df.dropna(axis=1, how='all')
            
            # Limpar espaços em branco nas strings
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype(str).str.strip()
            
            # Substituir valores vazios por None
            df = df.replace(['', ' ', 'nan', 'NaN'], None)
            
            logger.info(f"DataFrame limpo: {len(df)} linhas, {len(df.columns)} colunas")
            return df
            
        except Exception as e:
            logger.warning(f"Erro ao limpar DataFrame: {str(e)}")
            return df
    
    def validate_file(self, file: Any) -> bool:
        """
        Valida se o arquivo é válido para processamento
        
        Args:
            file: Arquivo carregado
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            # Verificar se é um arquivo ZIP
            if not file.name.lower().endswith('.zip'):
                return False
            
            # Verificar tamanho
            file.seek(0, 2)  # Ir para o final
            file_size = file.tell()
            file.seek(0)  # Voltar para o início
            
            if file_size > self.max_file_size:
                logger.warning(f"Arquivo muito grande: {file_size / (1024*1024):.2f}MB")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar arquivo: {str(e)}")
            return False
    
    def get_file_info(self, file: Any) -> Dict[str, Any]:
        """
        Obtém informações sobre o arquivo
        
        Args:
            file: Arquivo carregado
            
        Returns:
            Dicionário com informações do arquivo
        """
        try:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            return {
                "name": file.name,
                "size_mb": file_size / (1024 * 1024),
                "type": "ZIP",
                "valid": self.validate_file(file)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do arquivo: {str(e)}")
            return {
                "name": file.name,
                "size_mb": 0,
                "type": "Unknown",
                "valid": False
            }
