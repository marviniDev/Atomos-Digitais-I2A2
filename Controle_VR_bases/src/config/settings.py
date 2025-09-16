"""
Configurações centralizadas do sistema de automação VR/VA
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path

@dataclass
class VRConfig:
    """Configurações do sistema VR/VA"""
    
    # Pastas do sistema (caminhos relativos ao projeto raiz)
    data_folder: str = "data/input"
    output_folder: str = "output/reports"
    
    # Configurações de benefícios
    company_percentage: float = 0.8  # 80% empresa
    employee_percentage: float = 0.2  # 20% colaborador
    
    # Cargos de exclusão
    excluded_positions: List[str] = None
    
    # Planilhas obrigatórias
    required_files: List[str] = None
    
    # Mapeamento de arquivos
    file_mapping: Dict[str, str] = None
    
    def __post_init__(self):
        if self.excluded_positions is None:
            self.excluded_positions = ["DIRETOR", "ESTAGIÁRIO", "ESTAGIARIO", "APRENDIZ"]
        
        if self.required_files is None:
            self.required_files = ["ativos", "dias_uteis", "sindicatos"]
        
        if self.file_mapping is None:
            self.file_mapping = {
                "afastados": "Afastados",
                "aprendiz": "Aprendiz", 
                "ativos": "Ativos",
                "dias_uteis": "Dias_Uteis",
                "sindicatos": "Sindicatos",
                "desligados": "Desligados",
                "estagio": "Estagio",
                "exterior": "Exterior",
                "ferias": "Ferias",
                "admissoes": "Admissoes",
            }
    
    def get_data_path(self) -> Path:
        """Retorna o caminho da pasta de dados"""
        # Caminho relativo ao projeto raiz (2 níveis acima de src/)
        project_root = Path(__file__).parent.parent.parent
        return project_root / self.data_folder
    
    def get_output_path(self) -> Path:
        """Retorna o caminho da pasta de saída"""
        # Caminho relativo ao projeto raiz (2 níveis acima de src/)
        project_root = Path(__file__).parent.parent.parent
        return project_root / self.output_folder
    
    def validate_config(self) -> bool:
        """Valida se as configurações estão corretas"""
        try:
            # Verificar se as pastas existem
            if not self.get_data_path().exists():
                raise FileNotFoundError(f"Pasta de dados não encontrada: {self.data_folder}")
            
            # Criar pasta de saída se não existir
            self.get_output_path().mkdir(parents=True, exist_ok=True)
            
            # Validar percentuais
            if not (0 <= self.company_percentage <= 1):
                raise ValueError(f"Percentual da empresa deve estar entre 0 e 1: {self.company_percentage}")
            
            if not (0 <= self.employee_percentage <= 1):
                raise ValueError(f"Percentual do colaborador deve estar entre 0 e 1: {self.employee_percentage}")
            
            if abs(self.company_percentage + self.employee_percentage - 1.0) > 0.01:
                raise ValueError("A soma dos percentuais deve ser 100%")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na validação da configuração: {e}")
            return False

# Instância global de configuração
config = VRConfig()
