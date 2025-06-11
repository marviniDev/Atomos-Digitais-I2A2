import streamlit as st
import pandas as pd
import asyncio
import uuid
import tempfile
import nest_asyncio
from fastmcp import Client
import os


nest_asyncio.apply()

st.set_page_config(page_title="Analisador de Excel", layout="wide")
st.title("📊 Analisador de Arquivo Excel")

# Unique user memory namespace
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


async def conectar_agent(question: str, user_id: str, filepath: str):
    client = Client("http://127.0.0.1:8005/sse")
    async with client:
        container = await client.call_tool("multi_analyst", {"question": question, "user_id": user_id, "filepath": filepath})
        return container[0].text if container and hasattr(container[0], "text") else str(container)
        

uploaded_file = st.file_uploader("📁 Envie seu arquivo Excel", type=["xlsx", "xls"])

# salvar o uploaded_file em uma pasta aqui no src
if uploaded_file is not None:
    temp_dir  = "Pasta_temporaria_excel"
    os.makedirs(temp_dir, exist_ok=True)
    
    file_path = os.path.join(temp_dir,uploaded_file.name )

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Arquivo salvo em: {file_path}")
    
    question = st.text_input("Digite sua pergunta...")
    if question:
        with st.chat_message("user"):
            st.markdown(question)
            st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("Analisando os dados com IA..."):
            response = asyncio.run(
                conectar_agent(str(question), str(st.session_state.user_id), str(file_path))
            )
        with st.chat_message("assistant"):
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})


            
    