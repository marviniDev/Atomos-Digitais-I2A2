import streamlit as st
import pandas as pd
import asyncio
import uuid
import tempfile
import nest_asyncio
from fastmcp import Client



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

# Função para analisar com IA
async def call_agent(question: str, user_id: str, df: pd.DataFrame):
    client = Client("http://127.0.0.1:8005/sse")
    async with client:
        payload = {
            "question": question,
            "user_id": user_id,
            "data": df.to_dict(orient="records")
        }
        result = await client.call_tool("multi_analyst", payload)
        return result[0].text if result and hasattr(result[0], "text") else str(result)

# Função para escrever dados no Excel via MCP
async def write_to_excel(filepath, sheet_name, data, start_cell="A1"):
    client = Client("http://127.0.0.1:8005/sse")
    async with client:
        result = await client.call_tool("write_data_to_excel", {
            "filepath": filepath,
            "sheet_name": sheet_name,
            "data": data,
            "start_cell": start_cell
        })
        return result[0].text if result and hasattr(result[0], "text") else str(result)

# Upload do arquivo Excel
uploaded_file = st.file_uploader("📁 Envie seu arquivo Excel", type=["xlsx", "xls"])

if uploaded_file:
    try:
        # salvar o uploaded_file em uma pasta aqui no src
        st.session_state.uploaded_file = uploaded_file
        
        
        df = pd.read_excel(uploaded_file)
        
        st.subheader("🔍 Pré-visualização dos Dados")
        st.dataframe(df, use_container_width=True)

        st.markdown("## 💬 Pergunta ou ação")
        tab1, tab2 = st.tabs(["🔎 Analisar com IA", "✍️ Escrever no Excel"])

        # Aba: Analisar com IA
        with tab1:
            question = st.text_input("Digite sua pergunta...")
            if question:
                with st.chat_message("user"):
                    st.markdown(question)
                st.session_state.messages.append({"role": "user", "content": question})

                with st.spinner("Analisando os dados com IA..."):
                    response = asyncio.run(call_agent(question, st.session_state.user_id, df))

                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

        # Aba: Escrever no Excel
        with tab2:
            sheet_name = st.text_input("📄 Nome da planilha de destino", value="Sheet1")
            start_cell = st.text_input("🔢 Célula de início", value="A1")

            if st.button("✍️ Enviar dados para o Excel"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name

                st.info("📡 Enviando dados para o MCP...")
                result = asyncio.run(write_to_excel(
                    filepath=tmp_path,
                    sheet_name=sheet_name,
                    data=df.to_dict(orient="records"),
                    start_cell=start_cell
                ))
                st.success(f"✅ {result}")

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
else:
    st.info("Envie um arquivo para começar.")
