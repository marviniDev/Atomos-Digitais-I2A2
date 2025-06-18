import os
import sys
import atexit
import socket
import asyncio
import datetime
import tempfile
import zipfile
import subprocess

import pandas as pd
import streamlit as st

from typing import Dict, List, Any
from fastmcp import Client
from db_utils import DatabaseManager

# --- INÍCIO: Código para rodar o MCP como subprocesso ---
MCP_PROCESS = None

def is_port_in_use(port, host="127.0.0.1"):
    """Verifica se a porta está ocupada."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def start_mcp_server():
    global MCP_PROCESS
    mcp_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    # Só inicia se a porta 8005 estiver livre
    if not is_port_in_use(8005):
        MCP_PROCESS = subprocess.Popen([sys.executable, mcp_path])

def stop_mcp_server():
    global MCP_PROCESS
    if MCP_PROCESS and MCP_PROCESS.poll() is None:
        MCP_PROCESS.terminate()
        try:
            MCP_PROCESS.wait(timeout=5)
        except Exception:
            MCP_PROCESS.kill()

# Inicia MCP ao carregar o app
start_mcp_server()
atexit.register(stop_mcp_server)
# --- FIM: Código para rodar o MCP como subprocesso ---

# File Processor Class
class FileProcessor:
    @staticmethod
    async def extract_csv_from_zip(zip_file: Any) -> List[Dict[str, Any]]:
        """Extract CSV files from ZIP and return their contents"""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "uploaded.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_file.read())
            
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                csv_files = [f for f in zip_ref.namelist() if f.lower().endswith(".csv")]
                if not csv_files:
                    raise Exception("No CSV files found in the uploaded ZIP file")
                
                results = []
                for csv_file in csv_files:
                    file_path = os.path.join(tmpdir, csv_file)
                    zip_ref.extract(csv_file, tmpdir)
                    df = pd.read_csv(file_path)
                    results.append({
                        "name": csv_file,
                        "data": df.to_dict(orient="records")
                    })
                return results

# Initialize Streamlit app
st.set_page_config(page_title="Analisador de CSV em ZIP", layout="wide")

# Initialize session state
# if "user_id" not in st.session_state:
#     st.session_state.user_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "db_manager" not in st.session_state:
    st.session_state.db_manager = None
if "tables_info" not in st.session_state:
    st.session_state.tables_info = {}
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "query_history" not in st.session_state:
    st.session_state.query_history = []

# Main title
st.title("📊 Analisador de Arquivos CSV (ZIP)")

# Sidebar
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input("Chave da API OpenAI", type="password")
    
    if st.session_state.db_manager and st.session_state.tables_info:
        st.subheader("Tabelas no Banco")
        for table_name, info in st.session_state.tables_info.items():
            with st.expander(f"📑 {info['fileName']}"):
                st.write("Colunas no Banco de Dados:")
                for col in info['columns']:
                    st.write(f"- {col}")
                st.write(f"Linhas: {info['rows']}")

# Create tabs
tab1, tab2 = st.tabs(["📤 Upload de Arquivos", "🔍 Consultas e Resultados"])

# Tab 1: File Upload
with tab1:
    st.header("Upload de Arquivos")
    uploaded_zip = st.file_uploader("📁 Envie seu arquivo .zip contendo arquivos CSV", type="zip")
    
    if uploaded_zip:
        try:
            with st.spinner("Processando arquivos..."):
                # Process files
                file_processor = FileProcessor()
                csv_data = asyncio.run(file_processor.extract_csv_from_zip(uploaded_zip))
                
                # Initialize database
                db_manager = DatabaseManager().initialize()
                tables_info = {}
                
                for data in csv_data:
                    # Sanitize table name to be SQLite compatible
                    table_name = data["name"].lower()
                    # Remove file extension
                    table_name = table_name.replace('.csv', '')
                    # Replace any non-alphanumeric characters with underscore
                    table_name = ''.join(c if c.isalnum() else '_' for c in table_name)
                    # Ensure table name starts with a letter
                    if not table_name[0].isalpha():
                        table_name = 't_' + table_name
                    # Remove consecutive underscores
                    while '__' in table_name:
                        table_name = table_name.replace('__', '_')
                    # Remove trailing underscores
                    table_name = table_name.strip('_')
                    
                    # Get original and sanitized column names
                    original_columns = list(data["data"][0].keys()) if data["data"] else []
                    sanitized_columns = [db_manager._sanitize_column_name(col) for col in original_columns]
                    
                    # Create table with sanitized column names
                    db_manager.create_table_from_csv(table_name, data["data"])
                    
                    # Store both original and sanitized column names in tables_info
                    tables_info[table_name] = {
                        "columns": sanitized_columns,  # Store sanitized column names
                        "original_columns": original_columns,  # Keep original names for reference
                        "rows": len(data["data"]),
                        "fileName": data["name"]
                    }
                
                # Update session state
                st.session_state.db_manager = db_manager
                st.session_state.tables_info = tables_info
                st.session_state.uploaded_files = [d["name"] for d in csv_data]
                
                # Export database
                db_bytes = db_manager.export_database()
                if db_bytes:
                    st.download_button(
                        "📥 Baixar Banco de Dados",
                        db_bytes,
                        file_name="database.sqlite",
                        mime="application/x-sqlite3"
                    )
                
                st.success("Arquivos processados com sucesso!")
                
        except Exception as e:
            st.error(f"Erro ao processar arquivos: {str(e)}")

# Tab 2: Queries and Results
with tab2:
    if st.session_state.db_manager:
        st.header("Consultas e Resultados")
        question = st.text_input("💬 Digite sua pergunta sobre os dados...")
        
        if question and api_key:
            with st.spinner("Analisando com IA..."):
                try:
                    # Get schema info
                    schema_info = st.session_state.db_manager.get_schema_info()
                    
                    # Call AI agent
                    async def process_query():
                        try:
                            client = Client("http://127.0.0.1:8005/sse")
                            async with client:
                                # Test connection first
                                try:
                                    await client.ping()
                                except Exception as e:
                                    raise Exception("Não foi possível conectar ao servidor MCP. Verifique se o servidor está rodando na porta 8005.")
                                
                                payload = {
                                    "question": question,
                                    "schema_info": schema_info,
                                    "api_key": api_key
                                }
                                result = await client.call_tool("multi_analyst_tool", payload)
                                
                                if not result:
                                    raise Exception("O servidor MCP não retornou uma resposta válida.")
                                
                                if not hasattr(result[0], "text"):
                                    raise Exception("Formato de resposta inválido do servidor MCP.")
                                
                                sql_query = result[0].text
                                
                                # Execute query
                                query_results = st.session_state.db_manager.execute_query(sql_query)
                                
                                # Generate answer
                                answer_result = await client.call_tool("generate_answer_tool", {
                                    "question": question,
                                    "sql": sql_query,
                                    "results": query_results,
                                    "api_key": api_key
                                })
                                
                                if not answer_result or not hasattr(answer_result[0], "text"):
                                    raise Exception("Erro ao gerar resposta.")
                                
                                return sql_query, query_results, answer_result[0].text
                                
                        except Exception as e:
                            raise Exception(f"Erro na comunicação com o servidor MCP: {str(e)}")
                    
                    # Run async function
                    try:
                        sql_query, query_results, answer = asyncio.run(process_query())
                        
                        # Add to history
                        query_result = {
                            "question": question,
                            "sql": sql_query,
                            "results": query_results,
                            "answer": answer,
                            "timestamp": datetime.datetime.now()
                        }
                        st.session_state.query_history.append(query_result)
                        
                        # Display results
                        st.markdown("### Resposta")
                        st.markdown(answer)
                        
                        st.markdown("### Consulta SQL")
                        st.code(sql_query, language="sql")
                        
                        st.markdown("### Resultados")
                        st.dataframe(pd.DataFrame(query_results))
                        
                    except Exception as e:
                        st.error(f"Erro ao processar pergunta: {str(e)}")
                        st.info("Verifique se o servidor MCP está rodando com o comando: python src/mcp_server.py")
                        
                except Exception as e:
                    st.error(f"Erro ao processar pergunta: {str(e)}")
        elif question and not api_key:
            st.warning("Por favor, insira sua chave da API OpenAI para continuar.")
    else:
        st.info("Envie um arquivo ZIP contendo arquivos CSV para começar.")

    # Display query history
    if st.session_state.query_history:
        st.markdown("## 📜 Histórico de Consultas")
        for query in reversed(st.session_state.query_history):
            with st.expander(f"Pergunta: {query['question']} ({query['timestamp'].strftime('%H:%M:%S')})"):
                st.markdown("**Resposta:**")
                st.markdown(query['answer'])
                st.markdown("**SQL:**")
                st.code(query['sql'], language="sql")
                st.markdown("**Resultados:**")
                st.dataframe(pd.DataFrame(query['results']))
