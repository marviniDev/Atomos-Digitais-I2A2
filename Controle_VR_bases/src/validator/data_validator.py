"""
Módulo de validação de dados
"""
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)

class DataValidator:
    """Classe responsável por validar dados das planilhas"""
    
    def __init__(self):
        self.excluded_positions = config.excluded_positions
    
    def validate_spreadsheet_structure(self, df: pd.DataFrame, planilha_type: str) -> Tuple[bool, List[str]]:
        """
        Valida se a estrutura da planilha está correta
        
        Args:
            df: DataFrame da planilha
            planilha_type: Tipo da planilha
            
        Returns:
            Tuple[bool, List[str]]: (é_válida, lista_de_erros)
        """
        errors = []
        
        # Validações específicas por tipo de planilha
        if planilha_type == "ativos":
            errors.extend(self._validate_ativos_structure(df))
        elif planilha_type == "dias_uteis":
            errors.extend(self._validate_dias_uteis_structure(df))
        elif planilha_type == "sindicatos":
            errors.extend(self._validate_sindicatos_structure(df))
        elif planilha_type in ["afastados", "estagio", "aprendiz", "exterior"]:
            errors.extend(self._validate_matricula_only_structure(df))
        elif planilha_type == "ferias":
            errors.extend(self._validate_ferias_structure(df))
        elif planilha_type == "desligados":
            errors.extend(self._validate_desligados_structure(df))
        elif planilha_type == "admissoes":
            errors.extend(self._validate_admissoes_structure(df))
        
        # Validações gerais
        errors.extend(self._validate_general_structure(df, planilha_type))
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_ativos_structure(self, df: pd.DataFrame) -> List[str]:
        """Valida estrutura da planilha de ativos"""
        errors = []
        required_columns = ["Matricula", "Sindicato"]
        
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Coluna obrigatória '{col}' não encontrada na planilha de ativos")
        
        return errors
    
    def _validate_dias_uteis_structure(self, df: pd.DataFrame) -> List[str]:
        """Valida estrutura da planilha de dias úteis"""
        errors = []
        required_columns = ["Sindicato", "Dias_Uteis_Sindicato"]
        
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Coluna obrigatória '{col}' não encontrada na planilha de dias úteis")
        
        return errors
    
    def _validate_sindicatos_structure(self, df: pd.DataFrame) -> List[str]:
        """Valida estrutura da planilha de sindicatos"""
        errors = []
        required_columns = ["Sindicato", "Valor_Dia_Sindicato"]
        
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Coluna obrigatória '{col}' não encontrada na planilha de sindicatos")
        
        return errors
    
    def _validate_matricula_only_structure(self, df: pd.DataFrame) -> List[str]:
        """Valida estrutura de planilhas que só precisam de matrícula"""
        errors = []
        
        if "Matricula" not in df.columns:
            errors.append("Coluna obrigatória 'Matricula' não encontrada")
        
        return errors
    
    def _validate_ferias_structure(self, df: pd.DataFrame) -> List[str]:
        """Valida estrutura da planilha de férias"""
        errors = []
        required_columns = ["Matricula", "Dias_Ferias", "Dias_Comprados"]
        
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Coluna obrigatória '{col}' não encontrada na planilha de férias")
        
        return errors
    
    def _validate_desligados_structure(self, df: pd.DataFrame) -> List[str]:
        """Valida estrutura da planilha de desligados"""
        errors = []
        required_columns = ["Matricula", "Data_Desligamento", "Data_Comunicado_Desligamento"]
        
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Coluna obrigatória '{col}' não encontrada na planilha de desligados")
        
        return errors
    
    def _validate_admissoes_structure(self, df: pd.DataFrame) -> List[str]:
        """Valida estrutura da planilha de admissões"""
        errors = []
        required_columns = ["Matricula", "Data_Admissao"]
        
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Coluna obrigatória '{col}' não encontrada na planilha de admissões")
        
        return errors
    
    def _validate_general_structure(self, df: pd.DataFrame, planilha_type: str) -> List[str]:
        """Validações gerais para todas as planilhas"""
        errors = []
        
        # Verificar se tem dados
        if len(df) == 0:
            errors.append(f"Planilha '{planilha_type}' está vazia")
        
        # Verificar se tem colunas
        if len(df.columns) == 0:
            errors.append(f"Planilha '{planilha_type}' não tem colunas")
        
        return errors
    
    def validate_data_quality(self, df: pd.DataFrame, planilha_type: str) -> Tuple[bool, List[str]]:
        """
        Valida a qualidade dos dados
        
        Args:
            df: DataFrame da planilha
            planilha_type: Tipo da planilha
            
        Returns:
            Tuple[bool, List[str]]: (dados_válidos, lista_de_problemas)
        """
        problems = []
        
        # Verificar valores nulos em colunas críticas
        if planilha_type == "ativos":
            if "Matricula" in df.columns:
                null_matriculas = df["Matricula"].isnull().sum()
                if null_matriculas > 0:
                    problems.append(f"Encontradas {null_matriculas} matrículas nulas na planilha de ativos")
        
        # Verificar duplicatas de matrícula
        if "Matricula" in df.columns:
            duplicates = df["Matricula"].duplicated().sum()
            if duplicates > 0:
                problems.append(f"Encontradas {duplicates} matrículas duplicadas na planilha '{planilha_type}'")
        
        # Verificar datas inválidas
        date_columns = [col for col in df.columns if "Data" in col or "data" in col]
        for col in date_columns:
            try:
                pd.to_datetime(df[col], errors='coerce')
                invalid_dates = pd.to_datetime(df[col], errors='coerce').isnull().sum()
                if invalid_dates > 0:
                    problems.append(f"Encontradas {invalid_dates} datas inválidas na coluna '{col}'")
            except:
                problems.append(f"Erro ao validar datas na coluna '{col}'")
        
        is_valid = len(problems) == 0
        return is_valid, problems
    
    def get_validation_summary(self, spreadsheets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Gera resumo das validações de todas as planilhas
        
        Args:
            spreadsheets: Dicionário com planilhas
            
        Returns:
            Dict: Resumo das validações
        """
        summary = {
            "total_planilhas": len(spreadsheets),
            "planilhas_validas": 0,
            "planilhas_com_problemas": 0,
            "problemas_por_planilha": {},
            "total_problemas": 0
        }
        
        for planilha_type, df in spreadsheets.items():
            # Validar estrutura
            is_structure_valid, structure_errors = self.validate_spreadsheet_structure(df, planilha_type)
            
            # Validar qualidade
            is_quality_valid, quality_problems = self.validate_data_quality(df, planilha_type)
            
            # Combinar problemas
            all_problems = structure_errors + quality_problems
            
            if len(all_problems) == 0:
                summary["planilhas_validas"] += 1
            else:
                summary["planilhas_com_problemas"] += 1
            
            summary["problemas_por_planilha"][planilha_type] = all_problems
            summary["total_problemas"] += len(all_problems)
        
        return summary
