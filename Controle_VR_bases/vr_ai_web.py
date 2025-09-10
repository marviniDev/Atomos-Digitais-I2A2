import streamlit as st
import os
import json
from datetime import datetime
from vr_ai_agent import VRAIAgent

# Configuração da página
st.set_page_config(
    page_title="🤖 Agente IA - Automação VR/VA", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .insight-box {
        background: #e8f4fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196F3;
        margin: 1rem 0;
    }
    .alert-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .exclusion-box {
        background: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🤖 Agente IA - Automação de Compra VR/VA</h1>
    <p>Processamento completo com todas as regras de negócio automatizadas</p>
</div>
""", unsafe_allow_html=True)

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Configuração da API OpenAI
    st.subheader("🔑 API OpenAI")
    api_key = st.text_input(
        "Chave da API OpenAI", 
        type="password",
        help="Insira sua chave da API OpenAI para usar o agente IA"
    )
    
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
        st.success("✅ API Key configurada!")
    else:
        st.warning("⚠️ Configure a API Key para usar o agente IA")
    
    st.divider()
    
    # Informações sobre o sistema
    st.subheader("🎯 Funcionalidades")
    st.info("""
    **Automação Completa:**
    - ✅ Base única consolidada
    - 🚫 Tratamento de exclusões
    - 🔍 Validação e correção
    - 📊 Cálculo automatizado
    - 📋 Entrega final para operadora
    """)
    
    st.subheader("📋 Regras Aplicadas")
    st.info("""
    **Exclusões Automáticas:**
    - Diretores, estagiários, aprendizes
    - Afastados (licença maternidade, etc.)
    - Profissionais no exterior
    
    **Cálculos:**
    - Dias úteis por sindicato
    - Regras de férias
    - Desligamentos (dia 15)
    - Admissões proporcionais
    - 80% empresa / 20% colaborador
    """)

# Interface principal
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🚀 Processamento Completo de VR/VA")
    
    # Input para comando natural
    comando_usuario = st.text_input(
        "Digite o mês e ano para processamento completo (ex: 'processar setembro 2025'):",
        placeholder="Ex: processar setembro 2025"
    )
    
    # Botão de processamento
    if st.button("🎯 Processar VR/VA Completo", type="primary", disabled=not api_key):
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
                    
                    # Inicializar agente
                    agente = VRAIAgent()
                    if agente:
                        with st.spinner(f"🤖 Processando VR/VA completo para {mes_texto.capitalize()} de {ano}..."):
                            # Processar com IA
                            nome_saida = f"VR_{ano}_{mes:02d}_Processado_Completo.xlsx"
                            resultado = agente.processar_vr_completo(ano, mes, nome_saida=nome_saida)
                        
                        if resultado["sucesso"]:
                            st.markdown(f"""
                            <div class="success-box">
                                <h4>✅ Processamento Completo Concluído!</h4>
                                <p><strong>Arquivo:</strong> {os.path.basename(resultado['arquivo_saida'])}</p>
                                <p><strong>Funcionários Inicial:</strong> {resultado['total_funcionarios_inicial']}</p>
                                <p><strong>Funcionários Final:</strong> {resultado['total_funcionarios_final']}</p>
                                <p><strong>Total VR:</strong> R$ {resultado['total_vr']:,.2f}</p>
                                <p><strong>Total Empresa (80%):</strong> R$ {resultado['total_empresa']:,.2f}</p>
                                <p><strong>Total Colaborador (20%):</strong> R$ {resultado['total_colaborador']:,.2f}</p>
                                <p><strong>Problemas Encontrados:</strong> {resultado['problemas_encontrados']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Botão de download
                            if os.path.exists(resultado['arquivo_saida']):
                                with open(resultado['arquivo_saida'], "rb") as f:
                                    st.download_button(
                                        label="⬇️ Baixar arquivo processado completo",
                                        data=f,
                                        file_name=os.path.basename(resultado['arquivo_saida']),
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                            
                            # Mostrar exclusões aplicadas
                            if resultado.get("exclusoes_aplicadas"):
                                st.markdown(f"""
                                <div class="exclusion-box">
                                    <h4>🚫 Exclusões Aplicadas</h4>
                                    <ul>
                                        {''.join([f'<li>{exclusao}</li>' for exclusao in resultado['exclusoes_aplicadas']])}
                                    </ul>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Mostrar insights da IA
                            if resultado.get("insights_ia"):
                                st.header("🧠 Insights da IA")
                                insights = resultado["insights_ia"]
                                
                                if insights.get("resumo_geral"):
                                    st.markdown(f"""
                                    <div class="insight-box">
                                        <h4>📊 Resumo Geral</h4>
                                        <p>{insights['resumo_geral']}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                if insights.get("alertas"):
                                    st.markdown(f"""
                                    <div class="alert-box">
                                        <h4>⚠️ Alertas</h4>
                                        <ul>
                                            {''.join([f'<li>{alerta}</li>' for alerta in insights['alertas']])}
                                        </ul>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                if insights.get("sugestoes"):
                                    st.markdown(f"""
                                    <div class="insight-box">
                                        <h4>💡 Sugestões</h4>
                                        <ul>
                                            {''.join([f'<li>{sugestao}</li>' for sugestao in insights['sugestoes']])}
                                        </ul>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            # Resumo por sindicato
                            if resultado.get("resumo_sindicatos"):
                                st.header("📈 Resumo por Sindicato")
                                resumo_df = st.dataframe(resultado["resumo_sindicatos"])
                        else:
                            st.error(f"❌ Erro no processamento: {resultado['erro']}")
                else:
                    st.warning("⚠️ Não foi possível identificar o mês e o ano. Tente novamente.")
            except Exception as e:
                st.error(f"❌ Erro durante o processamento: {e}")
        else:
            st.warning("⚠️ Digite um comando para processar.")

with col2:
    st.header("💬 Consulta IA")
    
    # Interface para consultas diretas
    pergunta = st.text_area(
        "Faça uma pergunta sobre os dados:",
        placeholder="Ex: Quantos funcionários foram excluídos? Quais sindicatos têm mais VR?",
        height=100
    )
    
    if st.button("🤖 Consultar IA", disabled=not api_key):
        if pergunta:
            agente = VRAIAgent()
            if agente:
                with st.spinner("🤖 Analisando..."):
                    resposta = agente.consultar_ia(pergunta)
                
                st.markdown(f"""
                <div class="insight-box">
                    <h4>🤖 Resposta da IA</h4>
                    <p>{resposta}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Digite uma pergunta.")

# Seção de métricas (se houver dados processados)
if os.path.exists("output"):
    arquivos_output = [f for f in os.listdir("output") if f.endswith("_Completo.xlsx")]
    if arquivos_output:
        st.header("📊 Histórico de Processamentos Completos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Arquivos Processados", len(arquivos_output))
        
        with col2:
            ultimo_arquivo = max(arquivos_output, key=lambda x: os.path.getctime(os.path.join("output", x)))
            st.metric("Último Processamento", ultimo_arquivo.split("_")[2][:7])
        
        with col3:
            tamanho_total = sum(os.path.getsize(os.path.join("output", f)) for f in arquivos_output)
            st.metric("Tamanho Total", f"{tamanho_total / 1024:.1f} KB")

# Seção de informações sobre o processo
st.header("📋 Sobre o Processo de Automação")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 Objetivos Atendidos")
    st.info("""
    ✅ **Base única consolidada** - Reúne 5 bases em uma única
    ✅ **Tratamento de exclusões** - Remove diretores, estagiários, afastados, exterior
    ✅ **Validação e correção** - Detecta datas inconsistentes, campos faltantes
    ✅ **Cálculo automatizado** - Dias úteis, férias, desligamentos, admissões
    ✅ **Entrega final** - Planilha pronta para operadora com 80%/20%
    """)

with col2:
    st.subheader("📊 Abas Geradas")
    st.info("""
    📋 **VR_Mensal** - Dados principais para operadora
    📈 **resumo_sindicato** - Consolidação por sindicato
    ✅ **validações** - Problemas detectados
    📊 **VR_Completo** - Dados completos processados
    🧠 **insights_ia** - Análises da IA
    📈 **estatisticas** - Métricas gerais
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🤖 Agente IA para Automação de Compra VR/VA | Desenvolvido com OpenAI GPT</p>
    <p>Processamento completo com todas as regras de negócio automatizadas</p>
</div>
""", unsafe_allow_html=True)
