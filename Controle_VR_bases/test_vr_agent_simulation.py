#!/usr/bin/env python3
"""
Teste que simula exatamente o que acontece no vr_agent.py
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

from database import VRDatabaseManager
from data_loader import ExcelLoader
from validator import DataValidator
from calculator import VRCalculator
from report_generator import ExcelReportGenerator
from config import config
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_vr_agent_simulation():
    """Testa simulando exatamente o que acontece no vr_agent.py"""
    print("🧪 Testando simulação do VR Agent...")
    
    try:
        # Simular o construtor do VRAgentRefactored
        print("\n1. Validando configuração...")
        if not config.validate_config():
            raise ValueError("Configuração inválida")
        print("   ✅ Configuração válida")
        
        # Simular inicialização do banco de dados
        print("\n2. Inicializando banco de dados...")
        db_manager = VRDatabaseManager("test_simulation.db")
        db_manager.initialize("test_simulation.db")
        print("   ✅ Banco de dados inicializado")
        
        # Simular inicialização dos módulos
        print("\n3. Inicializando módulos...")
        data_loader = ExcelLoader(db_manager)
        validator = DataValidator()
        calculator = VRCalculator(db_manager)
        report_generator = ExcelReportGenerator()
        print("   ✅ Módulos inicializados")
        
        # Simular o processamento
        print("\n4. Simulando processamento...")
        
        # Carregar planilhas
        print("   Carregando planilhas...")
        spreadsheets = data_loader.load_all_spreadsheets(load_to_db=True)
        print(f"   ✅ Planilhas carregadas: {list(spreadsheets.keys())}")
        
        # Validar planilhas obrigatórias
        print("   Validando planilhas obrigatórias...")
        missing_files = data_loader.validate_required_files(spreadsheets)
        if missing_files:
            raise ValueError(f"Planilhas obrigatórias ausentes: {missing_files}")
        print("   ✅ Planilhas obrigatórias validadas")
        
        # Validar estrutura e qualidade dos dados
        print("   Validando dados...")
        validation_summary = validator.get_validation_summary(spreadsheets)
        print(f"   ✅ Validação concluída: {validation_summary['total_problemas']} problemas encontrados")
        
        print("\n✅ Simulação do VR Agent concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na simulação: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando simulação do VR Agent...")
    
    success = test_vr_agent_simulation()
    
    if success:
        print("\n🎉 Simulação passou!")
    else:
        print("\n💥 Simulação falhou!")
        sys.exit(1)
