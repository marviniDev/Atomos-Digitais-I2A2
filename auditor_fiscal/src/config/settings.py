"""
Configurações centralizadas do sistema de análise de dados CSV
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

@dataclass
class AuditorConfig:
    """Configurações do sistema de auditoria fiscal"""
    
    # Pastas do sistema
    data_folder: str = "data/input"
    output_folder: str = "output/reports"
    temp_folder: str = "temp"
    
    # Configurações de IA
    openai_model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    
    # Configurações de banco de dados
    db_type: str = "sqlite"
    db_path: str = "./data/auditor_database.db"
    
    # Configurações de processamento
    max_file_size_mb: int = 100
    supported_formats: List[str] = None
    encoding: str = "utf-8"
    
    # Configurações de logging
    log_level: str = "INFO"
    log_file: str = "logs/auditor.log"
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = [".csv", ".xlsx", ".xls"]
    
    def get_db_path(self) -> Path:
        """Retorna o caminho do banco de dados"""
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / "data" / "auditor_database.db"
        
        # Criar pasta data se não existir
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        return db_path
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Retorna configurações para OpenAI"""
        return {
            "model": self.openai_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

# Instância global de configuração
config = AuditorConfig()
