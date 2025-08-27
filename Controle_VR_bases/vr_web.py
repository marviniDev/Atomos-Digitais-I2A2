import streamlit as st
import os
from vr_bot import processar_vr
from datetime import datetime

st.set_page_config(page_title="Bot de Análise de VR", layout="centered")
st.title("🤖 Bot de Análise de Vale Refeição")

st.markdown("""
Este bot analisa automaticamente as planilhas **cruas** da pasta `/dados`
e gera o arquivo final processado na pasta `/output`, com base no mês e ano que você solicitar.
""")

# Input natural de linguagem
comando_usuario = st.text_input("Digite o mês e ano para análise (ex: 'analisar setembro 2025'):")

if comando_usuario:
    try:
        # Detectar mês e ano
        partes = comando_usuario.lower().replace("de", "").split()
        meses = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
            "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
            "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
        }

        mes_texto = next((p for p in partes if p in meses), None)
        ano = next((p for p in partes if p.isdigit() and len(p) == 4), None)

        if mes_texto and ano:
            mes = meses[mes_texto]
            ano = int(ano)
            st.info(f"Iniciando análise para {mes_texto.capitalize()} de {ano}...")

            # Rodar o bot com nome dinâmico da planilha final
            nome_saida = f"VR_{ano}_{mes:02d}_Processado.xlsx"
            processar_vr(ano, mes, nome_saida=nome_saida)

            if os.path.exists(nome_saida):
                with open(nome_saida, "rb") as f:
                    st.success("Arquivo gerado com sucesso!")
                    st.download_button(
                        label="⬇️ Baixar arquivo de VR",
                        data=f,
                        file_name=os.path.basename(nome_saida),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error("Erro: O arquivo de saída não foi encontrado.")
        else:
            st.warning("Não foi possível identificar o mês e o ano. Tente novamente.")

    except Exception as e:
        st.error(f"Erro durante o processamento: {e}")
