"""
Módulo para carregamento de planilhas Excel
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional
from config import config

logger = logging.getLogger(__name__)

class ExcelLoader:
    """Classe responsável por carregar planilhas Excel"""
    
    def __init__(self):
        self.data_folder = config.get_data_path()
        self.file_mapping = config.file_mapping
    
    def load_all_spreadsheets(self) -> Dict[str, pd.DataFrame]:
        """
        Carrega todas as planilhas da pasta de dados
        
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
