#!/usr/bin/env python3
"""
Orquestrador do Sistema VR/VA com MCP Server
Baseado no padrão do agent_csv_analyzer
"""
import os
import sys
import subprocess
import threading
import time
import atexit

def cleanup_processes():
    """Limpa processos em execução"""
    global mcp_process, streamlit_process
    
    if mcp_process:
        print("Encerrando servidor MCP...")
        mcp_process.terminate()
        try:
            mcp_process.wait(timeout=5)
        except Exception:
            print("Forçando encerramento do servidor MCP...")
            mcp_process.kill()
    else:
        print(f"Erro ao encerrar servidor MCP: {e}")

def run_mcp_server():
    """Inicia o servidor MCP em um novo processo."""
    global mcp_process
    print("Iniciando o servidor MCP...")
    mcp_server_path = os.path.join(os.path.dirname(__file__), 'src', 'mcp_server.py')
    
    if os.path.exists(mcp_server_path):
        # Inicia o servidor MCP como um processo separado.
        try:
            mcp_process = subprocess.Popen([sys.executable, mcp_server_path],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
            print("✅ Servidor MCP iniciado com sucesso!")
            mcp_process.wait()
        except Exception as e:
            print(f"Ocorreu um erro ao iniciar o servidor MCP: {e}")
    else:
        print("ERRO: O arquivo 'mcp_server.py' não foi encontrado. Verifique o caminho.")

def run_streamlit_app():
    """Inicia o aplicativo Streamlit em um novo processo."""
    global streamlit_process
    print("Iniciando o aplicativo Streamlit...")
    streamlit_app_path = os.path.join(os.path.dirname(__file__), 'src', 'web_interface.py')

    try:
        # Tenta encontrar o executável 'streamlit' no PATH do ambiente virtual
        # sys.prefix aponta para o diretório raiz do ambiente virtual (.venv/)
        streamlit_executable = os.path.join(sys.prefix, 'bin', 'streamlit')
        if sys.platform == "win32": # Para Windows, o executável pode estar em Scripts
            streamlit_executable = os.path.join(sys.prefix, 'Scripts', 'streamlit.exe')

        # Fallback se não encontrar no ambiente virtual específico
        if not os.path.exists(streamlit_executable):
            streamlit_executable = 'streamlit'
            print(f"AVISO: 'streamlit' não encontrado em {os.path.join(sys.prefix, 'bin')} ou {os.path.join(sys.prefix, 'Scripts')}. Tentando usar o 'streamlit' do PATH global.")

        # Inicia o Streamlit como um processo separado.
        # stdout e stderr são redirecionados para o terminal do main.py
        streamlit_process = subprocess.Popen([streamlit_executable, 'run', streamlit_app_path],
                                   stdout=sys.stdout, stderr=sys.stderr)
        
        # Aguarda o processo terminar
        streamlit_process.wait()
        
    except FileNotFoundError:
        print("ERRO: O comando 'streamlit' não foi encontrado.")
    except Exception as e:
        print(f"ERRO: Ocorreu um erro ao iniciar o aplicativo Streamlit: {e}")
def main():
    """Função principal que orquestra MCP e Streamlit."""
    global mcp_process, streamlit_process
    mcp_process = None
    streamlit_process = None
    
    print("🚀 Iniciando a orquestração do projeto: Servidor MCP e Aplicativo Streamlit.")
    
    # Cria e inicia uma thread para o servidor MCP.
    try:
        mcp_thread = threading.Thread(target=run_mcp_server)
        mcp_thread.daemon = True
        mcp_thread.start()
        
        print("Aguardando 3 segundos para o servidor MCP inicializar completamente...")
        time.sleep(3) # Dá um pequeno tempo para o servidor MCP iniciar antes do Streamlit
        
        # Registra função de limpeza
        atexit.register(cleanup_processes)
        
        # Inicia o Streamlit
        run_streamlit_app()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
        cleanup_processes()
    except Exception as e:
        print(f"❌ Erro na orquestração: {e}")
        cleanup_processes()

if __name__ == "__main__":
    main()
