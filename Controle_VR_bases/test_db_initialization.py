#!/usr/bin/env python3
"""
Teste de inicialização do banco de dados
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

from database import VRDatabaseManager
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_database_initialization():
    """Testa a inicialização do banco de dados"""
    print("🧪 Testando inicialização do banco de dados...")
    
    try:
        # Teste 1: Banco em memória
        print("\n1. Testando banco em memória...")
        db_memory = VRDatabaseManager()
        db_memory.initialize()
        
        # Verificar se as tabelas foram criadas
        conn, cursor = db_memory._get_connection()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   Tabelas criadas: {[table[0] for table in tables]}")
        
        # Verificar especificamente a tabela funcionarios_ativos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='funcionarios_ativos'")
        funcionarios_table = cursor.fetchall()
        print(f"   Tabela funcionarios_ativos existe: {len(funcionarios_table) > 0}")
        
        if len(funcionarios_table) > 0:
            # Verificar estrutura da tabela
            cursor.execute("PRAGMA table_info(funcionarios_ativos)")
            columns = cursor.fetchall()
            print(f"   Colunas da tabela funcionarios_ativos: {[col[1] for col in columns]}")
        
        # Teste 2: Banco em arquivo
        print("\n2. Testando banco em arquivo...")
        db_file = VRDatabaseManager("test.db")
        db_file.initialize("test.db")
        
        # Verificar se as tabelas foram criadas
        conn, cursor = db_file._get_connection()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   Tabelas criadas: {[table[0] for table in tables]}")
        
        # Verificar especificamente a tabela funcionarios_ativos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='funcionarios_ativos'")
        funcionarios_table = cursor.fetchall()
        print(f"   Tabela funcionarios_ativos existe: {len(funcionarios_table) > 0}")
        
        print("\n✅ Teste de inicialização concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_loading():
    """Testa o carregamento de dados"""
    print("\n🧪 Testando carregamento de dados...")
    
    try:
        # Criar banco de dados
        db = VRDatabaseManager("test.db")
        db.initialize("test.db")
        
        # Criar dados de teste
        import pandas as pd
        test_data = {
            'ativos': pd.DataFrame({
                'Matricula': ['001', '002', '003'],
                'Empresa': ['Empresa A', 'Empresa B', 'Empresa C'],
                'Cargo': ['Analista', 'Gerente', 'Diretor'],
                'Situacao': ['Ativo', 'Ativo', 'Ativo'],
                'Sindicato': ['Sindicato A', 'Sindicato B', 'Sindicato C']
            })
        }
        
        # Carregar dados
        db.load_spreadsheet_data(test_data)
        
        # Verificar se os dados foram inseridos
        conn, cursor = db._get_connection()
        cursor.execute("SELECT COUNT(*) FROM funcionarios_ativos")
        count = cursor.fetchone()[0]
        print(f"   Registros inseridos na tabela funcionarios_ativos: {count}")
        
        # Verificar dados
        cursor.execute("SELECT * FROM funcionarios_ativos LIMIT 3")
        rows = cursor.fetchall()
        print(f"   Dados inseridos: {rows}")
        
        print("\n✅ Teste de carregamento concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste de carregamento: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando testes do banco de dados...")
    
    # Executar testes
    test1 = test_database_initialization()
    test2 = test_data_loading()
    
    if test1 and test2:
        print("\n🎉 Todos os testes passaram!")
    else:
        print("\n💥 Alguns testes falharam!")
        sys.exit(1)
