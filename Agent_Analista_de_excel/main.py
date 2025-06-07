# main.py
import subprocess
import sys
import os
import time
import threading

def run_streamlit_app():
    """Inicia o aplicativo Streamlit em um novo processo."""
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
        process = subprocess.Popen([streamlit_executable, 'run', streamlit_app_path],
                                   stdout=sys.stdout, stderr=sys.stderr)
        process.wait() # Espera o Streamlit terminar (se ele for fechado)

    except FileNotFoundError:
        print("ERRO: O comando 'streamlit' não foi encontrado.")
        print("Certifique-se de que o Streamlit está instalado (pip install streamlit) e que seu ambiente virtual está ativado.")
        print("Caminho procurado: ", streamlit_executable)
    except Exception as e:
        print(f"Ocorreu um erro ao iniciar o Streamlit: {e}")

def run_mcp_server():
    """Inicia o servidor MCP em um novo processo."""
    print("Iniciando o servidor MCP...")
    mcp_server_path = os.path.join(os.path.dirname(__file__), 'src', 'mcp_server.py')

    try:
        # Inicia o servidor MCP como um processo separado.
        # Asseguramos que ele usa o python do ambiente virtual.
        process = subprocess.Popen([sys.executable, mcp_server_path],
                                   stdout=sys.stdout, stderr=sys.stderr)
        process.wait() # Espera o servidor MCP terminar (se ele for encerrado)

    except FileNotFoundError:
        print("ERRO: O arquivo 'mcp_server.py' não foi encontrado. Verifique o caminho.")
    except Exception as e:
        print(f"Ocorreu um erro ao iniciar o servidor MCP: {e}")

if __name__ == "__main__":
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