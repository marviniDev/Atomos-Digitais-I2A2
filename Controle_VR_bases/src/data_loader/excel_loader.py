"""
Módulo para carregamento de planilhas Excel com integração ao banco de dados
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional
from config import config
from database import VRDatabaseManager

logger = logging.getLogger(__name__)

class ExcelLoader:
    """Classe responsável por carregar planilhas Excel e integrar com banco de dados"""
    
    def __init__(self, db_manager: Optional[VRDatabaseManager] = None):
        self.data_folder = config.get_data_path()
        self.file_mapping = config.file_mapping
        self.db_manager = db_manager
    
    def load_all_spreadsheets(self, load_to_db: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Carrega todas as planilhas da pasta de dados e opcionalmente salva no banco
        
        Args:
            load_to_db: Se True, carrega os dados para o banco de dados
            
        Returns:
            Dict[str, pd.DataFrame]: Dicionário com nome da planilha e DataFrame
        """
        logger.info("Carregando planilhas...")
        
        if not self.data_folder.exists():
            raise FileNotFoundError(f"Pasta de dados não encontrada: {self.data_folder}")
        
        # Buscar arquivos Excel
        excel_files = list(self.data_folder.glob("*.xlsx"))
        logger.info(f"Encontrados {len(excel_files)} arquivos XLSX")
        
        spreadsheets = {}
        
        for file_path in excel_files:
            try:
                # Identificar tipo de planilha
                planilha_type = self._identify_spreadsheet_type(file_path.name)
                
                if planilha_type:
                    # Carregar planilha
                    df = pd.read_excel(file_path)
                    spreadsheets[planilha_type] = df
                    logger.info(f"✅ Planilha carregada: {file_path.name} -> {planilha_type}")
                else:
                    logger.warning(f"⚠️ Arquivo não reconhecido: {file_path.name}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao carregar {file_path.name}: {e}")
        
        # Carregar dados para o banco se solicitado e disponível
        if load_to_db and self.db_manager:
            try:
                logger.info("Carregando dados para o banco de dados...")
                self.db_manager.load_spreadsheet_data(spreadsheets)
                logger.info("✅ Dados carregados no banco de dados com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar dados no banco: {e}")
                raise
        
        return spreadsheets
    
    def _identify_spreadsheet_type(self, filename: str) -> Optional[str]:
        """
        Identifica o tipo de planilha baseado no nome do arquivo
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            str: Tipo da planilha ou None se não reconhecida
        """
        filename_lower = filename.lower().replace(" ", "_").replace(".xlsx", "")
        
        # Mapear nome do arquivo para tipo
        for planilha_type, expected_name in self.file_mapping.items():
            if expected_name.lower().replace(" ", "_") in filename_lower:
                return planilha_type
        
        return None
    
    def validate_required_files(self, spreadsheets: Dict[str, pd.DataFrame]) -> List[str]:
        """
        Valida se todas as planilhas obrigatórias estão presentes
        
        Args:
            spreadsheets: Dicionário com planilhas carregadas
            
        Returns:
            List[str]: Lista de arquivos obrigatórios ausentes
        """
        missing_files = []
        
        for required_file in config.required_files:
            if required_file not in spreadsheets:
                missing_files.append(required_file)
        
        if missing_files:
            logger.error(f"❌ Planilhas obrigatórias ausentes: {missing_files}")
        else:
            logger.info("✅ Todas as planilhas obrigatórias estão presentes")
        
        return missing_files
    
    def get_spreadsheet_info(self, df: pd.DataFrame, name: str) -> Dict:
        """
        Obtém informações básicas sobre uma planilha
        
        Args:
            df: DataFrame da planilha
            name: Nome da planilha
            
        Returns:
            Dict: Informações da planilha
        """
        return {
            "name": name,
            "rows": len(df),
            "columns": list(df.columns),
            "has_data": len(df) > 0,
            "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
        }
    
    def get_database_info(self) -> Optional[Dict]:
        """
        Obtém informações do banco de dados se disponível
        
        Returns:
            Dict: Informações do banco de dados ou None se não disponível
        """
        if not self.db_manager:
            return None
        
        try:
            schema_info = self.db_manager.get_schema_info()
            return {
                "tables": list(schema_info.keys()),
                "schema": schema_info,
                "total_tables": len(schema_info)
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações do banco: {e}")
            return None
