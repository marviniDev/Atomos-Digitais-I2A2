"""
Script principal para automação de VR/VA
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent))

from data_loader.excel_loader import ExcelLoader
from database.db_manager import VRDatabaseManager
from calculator.vr_calculator import VRCalculator
from ai_service.openai_service import OpenAIService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/logs/vr_automation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Função principal de automação"""
    try:
        print("🚀 AUTOMAÇÃO DE VR/VA - SISTEMA COMPLETO")
        print("=" * 50)
        
        # Obter parâmetros
        ano = int(input("Digite o ano (ex: 2025): ") or "2025")
        mes = int(input("Digite o mês (ex: 5): ") or "5")
        
        print(f"\n📅 Processando VR para {mes:02d}/{ano}")
        print("-" * 30)
        
        # 1. Inicializar sistema
        print("1. 🔧 Inicializando sistema...")
        db_manager = VRDatabaseManager()
        db_manager.initialize()
        
        loader = ExcelLoader(db_manager)
        ai_service = OpenAIService(os.environ.get('OPENAI_API_KEY'))
        calculator = VRCalculator(db_manager)
        
        print("   ✅ Sistema inicializado")
        
        # 2. Importar dados
        print("\n2. 📊 Importando dados das planilhas...")
        spreadsheets = loader.load_all_spreadsheets(load_to_db=True)
        print(f"   ✅ {len(spreadsheets)} planilhas importadas")
        
        # 3. Executar automação
        print(f"\n3. 🤖 Executando automação de VR...")
        output_path = calculator.execute_complete_vr_automation(ano, mes)
        
        print(f"\n🎉 AUTOMAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📁 Arquivo gerado: {output_path}")
        print(f"📊 Verifique o arquivo para validação final")
        
        # 4. Mostrar estatísticas
        print(f"\n�� ESTATÍSTICAS:")
        result = db_manager.execute_query("""
            SELECT * FROM processamentos 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        if result:
            stats = result[0]
            print(f"   👥 Funcionários iniciais: {stats['total_funcionarios_inicial']}")
            print(f"   👥 Funcionários finais: {stats['total_funcionarios_final']}")
            print(f"   💰 Total VR: R$ {stats['total_vr']:,.2f}")
            print(f"   🏢 Custo empresa: R$ {stats['total_empresa']:,.2f}")
            print(f"   👤 Desconto colaborador: R$ {stats['total_colaborador']:,.2f}")
            print(f"   ⚠️ Problemas encontrados: {stats['problemas_encontrados']}")
        
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro na automação: {e}")
        print(f"\n❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
