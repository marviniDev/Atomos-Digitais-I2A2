import streamlit as st
import pandas as pd
import asyncio
import uuid
import tempfile
import zipfile
import os
import nest_asyncio
import json
from fastmcp import Client



nest_asyncio.apply()

st.set_page_config(page_title="Analisador de CSV em ZIP", layout="wide")
st.title("📊 Analisador de Arquivos CSV (ZIP)")

# Unique user memory namespace
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Função para analisar com IA (via MCP)
async def call_agent(question: str, user_id: str, dfs: dict):
    client = Client("http://127.0.0.1:8005/sse")
    async with client:
        # Envia todos os dataframes como dicts
        payload = {
            "question": question,
            "user_id": user_id,
            "data": {name: df.to_dict(orient="records") for name, df in dfs.items()}
        }
        result = await client.call_tool("multi_analyst", payload)
        return result[0].text if result and hasattr(result[0], "text") else str(result)

# Upload do arquivo ZIP
uploaded_zip = st.file_uploader("📁 Envie seu arquivo .zip contendo arquivos CSV", type="zip")

if uploaded_zip:
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.read())
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)
            csv_files = [f for f in zip_ref.namelist() if f.lower().endswith(".csv")]

        if not csv_files:
            st.error("Nenhum arquivo CSV encontrado no ZIP.")
        else:
            dfs = {}
            st.subheader("Arquivos encontrados:")
            for csv_file in csv_files:
                file_path = os.path.join(tmpdir, csv_file)
                try:
                    df = pd.read_csv(file_path)
                    dfs[csv_file] = df
                    st.markdown(f"**{csv_file}**")
                    st.dataframe(df.head(3))
                except Exception as e:
                    st.warning(f"Erro ao ler {csv_file}: {e}")

            st.markdown("## 💬 Pergunta ou ação")
            question = st.text_input("Digite sua pergunta sobre os arquivos...")

            if question:
                with st.chat_message("user"):
                    st.markdown(question)
                st.session_state.messages.append({"role": "user", "content": question})

                with st.spinner("Analisando os dados com IA..."):
                    response = asyncio.run(call_agent(question, st.session_state.user_id, dfs))

                # Tenta extrair o texto do campo 'raw' se for JSON
                try:
                    # Se já for dict, não precisa carregar
                    if isinstance(response, dict):
                        answer = response.get("raw", str(response))
                    else:
                        # Tenta converter de string para dict
                        answer = json.loads(response).get("raw", str(response))
                except Exception:
                    answer = str(response)

                with st.chat_message("assistant"):
                    st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
else:
    st.info("Envie um arquivo ZIP contendo arquivos CSV para começar.")
