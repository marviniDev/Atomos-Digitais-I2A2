import streamlit as st
import pandas as pd
import asyncio
import uuid
import tempfile
import nest_asyncio
from fastmcp import Client
import os
import zipfile

nest_asyncio.apply()

st.set_page_config(page_title="Analisador de Arquivos CSV em ZIP", layout="wide")
st.title("🗂️ Analisador de Arquivo ZIP com CSVs")

# Unique user memory namespace
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Função para converter CSV para Excel
def csv_para_excel(csv_path: str) -> str:
    df = pd.read_csv(csv_path)
    excel_path = csv_path.replace(".csv", ".xlsx")
    df.to_excel(excel_path, index=False)
    return excel_path

async def conectar_agent(question: str, user_id: str, filepath: str):
    client = Client("http://127.0.0.1:8005/sse")
    async with client:
        container = await client.call_tool("multi_analyst", {
            "question": question,
            "user_id": user_id,
            "filepath": filepath
        })
        return container[0].text if container and hasattr(container[0], "text") else str(container)

uploaded_file = st.file_uploader("📁 Envie seu arquivo ZIP com arquivos CSV", type=["zip"])

if uploaded_file is not None:
    temp_dir = "pasta_temporaria_csv"
    os.makedirs(temp_dir, exist_ok=True)

    zip_path = os.path.join(temp_dir, uploaded_file.name)

    # Salva o arquivo ZIP temporariamente
    with open(zip_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"Arquivo ZIP salvo em: {zip_path}")

    extracted_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
        extracted_files = [f for f in zip_ref.namelist() if f.endswith(".csv")]

    if not extracted_files:
        st.warning("O arquivo ZIP não contém arquivos CSV.")
    else:
        st.info(f"{len(extracted_files)} arquivo(s) CSV encontrado(s):")
        for file in extracted_files:
            st.write(f"- {file}")

        selected_csv = st.selectbox("📄 Selecione o arquivo CSV para análise", extracted_files)

        file_path = os.path.join(temp_dir, selected_csv)

        # Mostra o conteúdo como preview
        df = pd.read_csv(file_path)
        st.dataframe(df.head(10))

        question = st.text_area("Digite sua pergunta...")

        if st.button("Enviar Pergunta"):
            if question:
                with st.chat_message("user"):
                    st.markdown(question)
                    st.session_state.messages.append({"role": "user", "content": question})

                # Converte CSV para Excel
                excel_path = csv_para_excel(file_path)

                with st.spinner("Analisando os dados com IA..."):
                    response = asyncio.run(
                        conectar_agent(str(question), str(st.session_state.user_id), str(excel_path))
                    )

                with st.chat_message("assistant"):
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
