# main.py
import subprocess
import sys
import os
import time
import threading
import signal
import atexit

# Global variables to track processes
mcp_process = None
streamlit_process = None

def cleanup():
    """Cleanup function to ensure all processes are terminated properly"""
    global mcp_process, streamlit_process
    
    print("\nExecutando limpeza...")
    
    if mcp_process:
        try:
            print("Encerrando servidor MCP...")
            mcp_process.terminate()
            mcp_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Forçando encerramento do servidor MCP...")
            mcp_process.kill()
        except Exception as e:
            print(f"Erro ao encerrar servidor MCP: {e}")
    
    if streamlit_process:
        try:
            print("Encerrando Streamlit...")
            streamlit_process.terminate()
            streamlit_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Forçando encerramento do Streamlit...")
            streamlit_process.kill()
        except Exception as e:
            print(f"Erro ao encerrar Streamlit: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\nRecebido sinal {signum}. Encerrando aplicação...")
    cleanup()
    sys.exit(0)

def run_streamlit_app():
    """Inicia o aplicativo Streamlit em um novo processo."""
    global streamlit_process
    print("Iniciando o aplicativo Streamlit...")
    streamlit_app_path = os.path.join(os.path.dirname(__file__), 'src', 'app.py')

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
        print("Certifique-se de que o Streamlit está instalado (pip install streamlit) e que seu ambiente virtual está ativado.")
        print("Caminho procurado: ", streamlit_executable)
    except Exception as e:
        print(f"Ocorreu um erro ao iniciar o Streamlit: {e}")
    finally:
        cleanup()

def run_mcp_server():
    """Inicia o servidor MCP em um novo processo."""
    global mcp_process
    print("Iniciando o servidor MCP...")
    mcp_server_path = os.path.join(os.path.dirname(__file__), 'src', 'mcp_server.py')

    try:
        # Inicia o servidor MCP como um processo separado.
        # Asseguramos que ele usa o python do ambiente virtual.
        mcp_process = subprocess.Popen([sys.executable, mcp_server_path],
                                   stdout=sys.stdout, stderr=sys.stderr)
        
        # Aguarda o processo terminar
        mcp_process.wait()

    except FileNotFoundError:
        print("ERRO: O arquivo 'mcp_server.py' não foi encontrado. Verifique o caminho.")
    except Exception as e:
        print(f"Ocorreu um erro ao iniciar o servidor MCP: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function
    atexit.register(cleanup)
    
    print("Iniciando a orquestração do projeto: Servidor MCP e Aplicativo Streamlit.")

    # Cria e inicia uma thread para o servidor MCP.
    # Usamos `daemon=True` para que a thread do servidor termine automaticamente quando o programa principal (main.py) encerrar.
    mcp_thread = threading.Thread(target=run_mcp_server)
    mcp_thread.daemon = True
    mcp_thread.start()

    print("Aguardando 3 segundos para o servidor MCP inicializar completamente...")
    time.sleep(3) # Dá um pequeno tempo para o servidor MCP iniciar antes do Streamlit

    # Inicia o aplicativo Streamlit no thread principal.
    # Este comando bloqueará o main.py enquanto o Streamlit estiver rodando.
    # Quando você fechar o Streamlit (Ctrl+C no terminal), o main.py continuará e encerrará.
    run_streamlit_app()

    print("Ambos os serviços foram encerrados ou o Streamlit foi fechado.")