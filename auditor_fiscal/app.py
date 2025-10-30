"""
Sistema Auditor Fiscal - Aplicação Principal
"""
import sys
import logging
from pathlib import Path
import importlib.util

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Adicionar o diretório src ao path para imports
sys.path.append(str(Path(__file__).parent / "src"))

# Importar e executar a aplicação principal
spec = importlib.util.spec_from_file_location(
    "inicio", 
    Path(__file__).parent / "0_Inicio.py"
)
inicio_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inicio_module)
main = inicio_module.main

if __name__ == "__main__":
    main()
