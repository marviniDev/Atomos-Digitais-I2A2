"""
Sistema de persistência de configurações
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigPersistence:
    """Gerencia persistência de configurações do sistema"""
    
    def __init__(self, config_dir: Path = None):
        """
        Inicializa o sistema de persistência
        
        Args:
            config_dir: Diretório para salvar configurações (padrão: ~/.auditor_fiscal)
        """
        if config_dir is None:
            # Usar diretório home do usuário
            self.config_dir = Path.home() / ".auditor_fiscal"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Garante que o diretório de configuração existe"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório de configuração: {self.config_dir}")
        except Exception as e:
            logger.error(f"Erro ao criar diretório de configuração: {str(e)}")
    
    def save_config(self, key: str, value: Any) -> bool:
        """
        Salva uma configuração
        
        Args:
            key: Chave da configuração
            value: Valor a ser salvo
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            # Carregar configurações existentes
            config = self.load_all_configs()
            
            # Atualizar configuração
            config[key] = value
            
            # Salvar no arquivo
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuração '{key}' salva com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração '{key}': {str(e)}")
            return False
    
    def load_config(self, key: str, default: Any = None) -> Any:
        """
        Carrega uma configuração específica
        
        Args:
            key: Chave da configuração
            default: Valor padrão se não encontrar
            
        Returns:
            Valor da configuração ou default
        """
        try:
            config = self.load_all_configs()
            return config.get(key, default)
        except Exception as e:
            logger.error(f"Erro ao carregar configuração '{key}': {str(e)}")
            return default
    
    def load_all_configs(self) -> Dict[str, Any]:
        """
        Carrega todas as configurações
        
        Returns:
            Dicionário com todas as configurações
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {str(e)}")
            return {}
    
    def delete_config(self, key: str) -> bool:
        """
        Remove uma configuração
        
        Args:
            key: Chave da configuração a ser removida
            
        Returns:
            True se removeu com sucesso, False caso contrário
        """
        try:
            config = self.load_all_configs()
            if key in config:
                del config[key]
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Configuração '{key}' removida com sucesso")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao remover configuração '{key}': {str(e)}")
            return False
    
    def clear_all_configs(self) -> bool:
        """
        Remove todas as configurações
        
        Returns:
            True se removeu com sucesso, False caso contrário
        """
        try:
            if self.config_file.exists():
                self.config_file.unlink()
                logger.info("Todas as configurações foram removidas")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao limpar configurações: {str(e)}")
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o sistema de configuração
        
        Returns:
            Dicionário com informações do sistema
        """
        return {
            "config_dir": str(self.config_dir),
            "config_file": str(self.config_file),
            "file_exists": self.config_file.exists(),
            "file_size": self.config_file.stat().st_size if self.config_file.exists() else 0,
            "total_configs": len(self.load_all_configs())
        }

# Instância global para uso em toda a aplicação
config_persistence = ConfigPersistence()
