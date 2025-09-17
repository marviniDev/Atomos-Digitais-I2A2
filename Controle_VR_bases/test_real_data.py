#!/usr/bin/env python3
"""
Teste com dados reais para identificar o problema
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

from database import VRDatabaseManager
from data_loader import ExcelLoader
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_real_data():
    """Testa com dados reais"""
    print("🧪 Testando com dados reais...")
    
    try:
        # 1. Inicializar banco de dados
        print("\n1. Inicializando banco de dados...")
        db_manager = VRDatabaseManager("test_real.db")
        db_manager.initialize("test_real.db")
        
        # 2. Inicializar data loader
        print("\n2. Inicializando data loader...")
        data_loader = ExcelLoader(db_manager)
        
        # 3. Verificar tabelas antes do carregamento
        print("\n3. Verificando tabelas antes do carregamento...")
        conn, cursor = db_manager._get_connection()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   Tabelas existentes: {[table[0] for table in tables]}")
        
        # 4. Carregar dados reais
        print("\n4. Carregando dados reais...")
        try:
            spreadsheets = data_loader.load_all_spreadsheets(load_to_db=True)
            print(f"   ✅ Dados carregados: {list(spreadsheets.keys())}")
        except Exception as e:
            print(f"   ❌ Erro ao carregar dados: {e}")
            # Verificar se as tabelas ainda existem
            conn, cursor = db_manager._get_connection()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"   Tabelas após erro: {[table[0] for table in tables]}")
            raise
        
        # 5. Verificar dados inseridos
        print("\n5. Verificando dados inseridos...")
        cursor.execute("SELECT COUNT(*) FROM funcionarios_ativos")
        count = cursor.fetchone()[0]
        print(f"   Registros na tabela funcionarios_ativos: {count}")
        
        print("\n✅ Teste com dados reais concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando teste com dados reais...")
    
    success = test_real_data()
    
    if success:
        print("\n🎉 Teste passou!")
    else:
        print("\n💥 Teste falhou!")
        sys.exit(1)
