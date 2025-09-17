#!/usr/bin/env python3
"""
Teste para verificar se a correção do clear_all_data funciona
"""
import sys
from pathlib import Path
import sqlite3
import tempfile

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

from database import VRDatabaseManager
import pandas as pd
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_fixed_clear_all():
    """Testa se a correção do clear_all_data funciona"""
    print("🧪 Testando correção do clear_all_data...")
    
    try:
        # 1. Criar um banco de dados sem tabelas
        print("\n1. Criando banco de dados sem tabelas...")
        db_path = "test_fixed_clear.db"
        
        # Criar banco vazio
        conn = sqlite3.connect(db_path)
        conn.close()
        
        # 2. Inicializar VRDatabaseManager sem chamar initialize()
        print("\n2. Inicializando VRDatabaseManager sem initialize()...")
        db_manager = VRDatabaseManager(db_path)
        
        # 3. Tentar chamar clear_all_data (deve funcionar sem erro)
        print("\n3. Chamando clear_all_data...")
        try:
            db_manager.clear_all_data()
            print("   ✅ clear_all_data executado sem erro")
        except Exception as e:
            print(f"   ❌ Erro no clear_all_data: {e}")
            return False
        
        # 4. Tentar inserir dados (deve criar tabelas automaticamente)
        print("\n4. Tentando inserir dados...")
        test_data = pd.DataFrame({
            'Matricula': ['001', '002'],
            'Empresa': ['Empresa A', 'Empresa B'],
            'Cargo': ['Analista', 'Gerente']
        })
        
        try:
            db_manager._insert_dataframe_to_table(test_data, 'funcionarios_ativos')
            print("   ✅ Dados inseridos com sucesso")
        except Exception as e:
            print(f"   ❌ Erro ao inserir dados: {e}")
            return False
        
        # 5. Verificar se a tabela foi criada
        print("\n5. Verificando se a tabela foi criada...")
        conn, cursor = db_manager._get_connection()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='funcionarios_ativos'")
        table_exists = cursor.fetchone()
        print(f"   Tabela funcionarios_ativos existe: {table_exists is not None}")
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM funcionarios_ativos")
            count = cursor.fetchone()[0]
            print(f"   Registros na tabela: {count}")
        
        print("\n✅ Teste de correção concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando teste de correção do clear_all_data...")
    
    success = test_fixed_clear_all()
    
    if success:
        print("\n🎉 Teste passou!")
    else:
        print("\n�� Teste falhou!")
        sys.exit(1)
