"""
Interface Web Corporativa - Sistema de Automação VR/VA
Interface moderna e profissional para processamento de Vale Refeição
"""
import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, date
from pathlib import Path
import json

# Adicionar src ao path para imports
sys.path.append(str(Path(__file__).parent))

from vr_agent import VRAgentRefactored

# Configuração da página
st.set_page_config(
    page_title="Sistema VR/VA - Automação Corporativa", 
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para interface corporativa
st.markdown("""
<style>
    /* Reset e configurações base */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header principal */
    .corporate-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2.5rem 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .corporate-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .corporate-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #2a5298;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin: 0.5rem 0;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2a5298;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Status cards */
    .status-success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 4px solid #28a745;
        color: #155724;
    }
    
    .status-warning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left: 4px solid #ffc107;
        color: #856404;
    }
    
    .status-error {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 4px solid #dc3545;
        color: #721c24;
    }
    
    .status-info {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-left: 4px solid #17a2b8;
        color: #0c5460;
    }
    
    /* Botões personalizados */
    .stButton > button {
        background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(42, 82, 152, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(42, 82, 152, 0.4);
    }
    
    /* Sidebar personalizada */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Tabelas personalizadas */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Progress bar personalizada */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #2a5298 0%, #1e3c72 100%);
    }
    
    /* Alertas personalizados */
    .alert-box {
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    
    .alert-success {
        background: #d4edda;
        border-left-color: #28a745;
        color: #155724;
    }
    
    .alert-warning {
        background: #fff3cd;
        border-left-color: #ffc107;
        color: #856404;
    }
    
    .alert-danger {
        background: #f8d7da;
        border-left-color: #dc3545;
        color: #721c24;
    }
    
    .alert-info {
        background: #d1ecf1;
        border-left-color: #17a2b8;
        color: #0c5460;
    }
    
    /* Footer */
    .corporate-footer {
        text-align: center;
        color: #666;
        padding: 2rem 0;
        border-top: 1px solid #e9ecef;
        margin-top: 3rem;
    }
    
    /* Gráficos simples */
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estado da sessão
if 'agente' not in st.session_state:
    st.session_state.agente = None
if 'processamento_ativo' not in st.session_state:
    st.session_state.processamento_ativo = False
if 'resultado_processamento' not in st.session_state:
    st.session_state.resultado_processamento = None

def main():
    """Função principal da interface"""
    
    # Header corporativo
    render_header()
    
    # Sidebar com configurações
    render_sidebar()
    
    # Conteúdo principal
    if st.session_state.agente:
        render_main_content()
    else:
        render_welcome_screen()
    
    # Footer
    render_footer()

def render_header():
    """Renderiza o header principal"""
    st.markdown("""
    <div class="corporate-header">
        <h1>🏢 Sistema VR/VA</h1>
        <p>Automação Inteligente para Processamento de Vale Refeição e Vale Alimentação</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Renderiza a sidebar com configurações"""
    with st.sidebar:
        st.markdown("## ⚙️ Configurações do Sistema")
        
        # Configuração da API OpenAI
        st.markdown("### 🔑 Autenticação")
        api_key = st.text_input(
            "Chave da API OpenAI",
            type="password",
            help="Insira sua chave da API OpenAI para ativar todas as funcionalidades",
            placeholder="sk-..."
        )
        
        if api_key:
            try:
                if st.session_state.agente is None or getattr(st.session_state.agente, 'api_key', None) != api_key:
                    st.session_state.agente = VRAgentRefactored(api_key)
                    st.session_state.agente.api_key = api_key
                
                st.success("✅ Sistema autenticado com sucesso!")
                
                # Status do sistema
                render_system_status()
                
            except Exception as e:
                st.error(f"❌ Erro na autenticação: {str(e)}")
                st.session_state.agente = None
        else:
            st.warning("⚠️ Insira a chave da API para continuar")
            st.session_state.agente = None
        
        st.divider()
        
        # Informações do sistema
        render_system_info()

def render_system_status():
    """Renderiza o status do sistema"""
    st.markdown("### 📊 Status do Sistema")
    
    try:
        status = st.session_state.agente.get_system_status()
        
        for key, value in status.items():
            if isinstance(value, bool):
                icon = "✅" if value else "❌"
                st.write(f"{icon} **{key.replace('_', ' ').title()}**")
            else:
                st.write(f"📋 **{key.replace('_', ' ').title()}**: {value}")
                
    except Exception as e:
        st.error(f"Erro ao verificar status: {e}")

def render_system_info():
    """Renderiza informações sobre o sistema"""
    st.markdown("### 🏗️ Arquitetura")
    st.info("""
    **Módulos do Sistema:**
    - �� **Config**: Configurações centralizadas
    - 📊 **Data Loader**: Carregamento de planilhas
    - ✅ **Validator**: Validação de dados
    - �� **Calculator**: Cálculos de VR
    - 🤖 **AI Service**: Serviços de IA
    - 📋 **Report Generator**: Geração de relatórios
    """)
    
    st.markdown("### 📋 Planilhas Suportadas")
    st.info("""
    **Obrigatórias:**
    - Ativos.xlsx
    - Dias_Uteis.xlsx
    - Sindicatos.xlsx
    
    **Opcionais:**
    - Afastados.xlsx
    - Ferias.xlsx
    - Desligados.xlsx
    - Admissoes.xlsx
    - Estagio.xlsx
    - Aprendiz.xlsx
    - Exterior.xlsx
    """)

def render_welcome_screen():
    """Renderiza a tela de boas-vindas"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="alert-info alert-box">
            <h3>�� Bem-vindo ao Sistema VR/VA</h3>
            <p>Configure sua chave da API OpenAI na barra lateral para começar a usar o sistema.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🚀 Funcionalidades Principais")
        
        features = [
            ("📊 Consolidação de Dados", "Reúne múltiplas planilhas em uma base única"),
            ("✅ Validação Automática", "Detecta inconsistências e problemas nos dados"),
            ("🧮 Cálculos Inteligentes", "Aplica regras de negócio automaticamente"),
            ("🤖 Análise com IA", "Insights e sugestões usando OpenAI"),
            ("📋 Relatórios Completos", "Gera planilhas prontas para operadora"),
            ("📈 Dashboards Interativos", "Visualizações e métricas em tempo real")
        ]
        
        for icon_title, description in features:
            st.markdown(f"**{icon_title}** - {description}")

def render_main_content():
    """Renderiza o conteúdo principal"""
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["�� Dashboard", "⚙️ Processamento", "�� Relatórios", "�� Consultas IA"])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_processing()
    
    with tab3:
        render_reports()
    
    with tab4:
        render_ai_queries()

def render_dashboard():
    """Renderiza o dashboard principal"""
    st.markdown("## 📊 Dashboard Executivo")
    
    # Métricas principais (se houver resultado de processamento)
    if st.session_state.resultado_processamento:
        render_metrics_cards()
        render_charts()
    else:
        st.info("💡 Execute um processamento para ver as métricas no dashboard")
    
    # Status do sistema
    render_system_overview()

def render_metrics_cards():
    """Renderiza os cards de métricas"""
    resultado = st.session_state.resultado_processamento
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{resultado['total_funcionarios_final']:,}</p>
            <p class="metric-label">Funcionários Elegíveis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">R$ {resultado['total_vr']:,.0f}</p>
            <p class="metric-label">Total VR</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">R$ {resultado['total_empresa']:,.0f}</p>
            <p class="metric-label">Empresa (80%)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{resultado['problemas_encontrados']}</p>
            <p class="metric-label">Problemas Detectados</p>
        </div>
        """, unsafe_allow_html=True)

def render_charts():
    """Renderiza os gráficos usando Streamlit nativo"""
    resultado = st.session_state.resultado_processamento
    
    if resultado.get('resumo_sindicatos'):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Distribuição por Sindicato")
            df_resumo = pd.DataFrame(resultado['resumo_sindicatos'])
            
            if not df_resumo.empty and 'Sindicato' in df_resumo.columns and 'VR_Total' in df_resumo.columns:
                # Gráfico de barras usando st.bar_chart
                chart_data = df_resumo.set_index('Sindicato')['VR_Total']
                st.bar_chart(chart_data)
        
        with col2:
            st.markdown("### 🥧 Proporção Empresa vs Colaborador")
            empresa = resultado['total_empresa']
            colaborador = resultado['total_colaborador']
            
            # Gráfico de pizza usando st.dataframe com formatação
            proporcao_data = {
                'Categoria': ['Empresa (80%)', 'Colaborador (20%)'],
                'Valor (R$)': [empresa, colaborador],
                'Percentual': ['80%', '20%']
            }
            df_proporcao = pd.DataFrame(proporcao_data)
            st.dataframe(df_proporcao, use_container_width=True)
            
            # Mostrar valores como texto
            st.markdown(f"""
            <div class="chart-container">
                <h4>💰 Distribuição de Custos</h4>
                <p><strong>Empresa:</strong> R$ {empresa:,.2f} (80%)</p>
                <p><strong>Colaborador:</strong> R$ {colaborador:,.2f} (20%)</p>
                <p><strong>Total:</strong> R$ {empresa + colaborador:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)

def render_system_overview():
    """Renderiza visão geral do sistema"""
    st.markdown("### 🔍 Visão Geral do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="alert-info alert-box">
            <h4>✅ Funcionalidades Ativas</h4>
            <ul>
                <li>Processamento automatizado de VR/VA</li>
                <li>Validação inteligente de dados</li>
                <li>Análise com IA para insights</li>
                <li>Geração de relatórios completos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="alert-success alert-box">
            <h4>📊 Métricas de Qualidade</h4>
            <ul>
                <li>Validação automática de dados</li>
                <li>Detecção de inconsistências</li>
                <li>Relatórios de auditoria</li>
                <li>Rastreabilidade completa</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def render_processing():
    """Renderiza a interface de processamento"""
    st.markdown("## ⚙️ Processamento de VR/VA")
    
    # Formulário de processamento
    with st.form("processamento_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            mes = st.selectbox(
                "Mês de Referência",
                options=[
                    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                ],
                index=8  # Setembro como padrão
            )
        
        with col2:
            ano = st.selectbox(
                "Ano de Referência",
                options=list(range(2020, 2030)),
                index=5  # 2025 como padrão
            )
        
        # Configurações avançadas
        st.markdown("### ⚙️ Configurações Avançadas")
        
        col3, col4 = st.columns(2)
        
        with col3:
            empresa_pct = st.slider(
                "Percentual da Empresa (%)",
                min_value=0,
                max_value=100,
                value=80,
                help="Percentual do VR pago pela empresa"
            )
        
        with col4:
            colaborador_pct = st.slider(
                "Percentual do Colaborador (%)",
                min_value=0,
                max_value=100,
                value=20,
                help="Percentual do VR pago pelo colaborador"
            )
        
        # Opções de processamento
        st.markdown("### 🔧 Opções de Processamento")
        
        col5, col6 = st.columns(2)
        
        with col5:
            validar_ia = st.checkbox("Ativar Validação com IA", value=True)
            relatorio_detalhado = st.checkbox("Gerar Relatório Detalhado", value=True)
        
        with col6:
            aplicar_exclusoes = st.checkbox("Aplicar Exclusões Automáticas", value=True)
            gerar_insights = st.checkbox("Gerar Insights da IA", value=True)
        
        # Botão de processamento
        submitted = st.form_submit_button(
            "�� Iniciar Processamento",
            use_container_width=True
        )
    
    if submitted:
        processar_dados(mes, ano, empresa_pct, colaborador_pct, validar_ia, relatorio_detalhado, aplicar_exclusoes, gerar_insights)

def processar_dados(mes, ano, empresa_pct, colaborador_pct, validar_ia, relatorio_detalhado, aplicar_exclusoes, gerar_insights):
    """Processa os dados de VR/VA"""
    
    # Mapear mês para número
    meses = {
        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
        "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
        "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }
    
    mes_num = meses[mes]
    
    # Validar percentuais
    if empresa_pct + colaborador_pct != 100:
        st.error("❌ A soma dos percentuais deve ser 100%")
        return
    
    # Atualizar configurações se necessário
    if empresa_pct != 80 or colaborador_pct != 20:
        st.warning("⚠️ Percentuais personalizados serão aplicados no próximo processamento")
    
    # Iniciar processamento
    st.session_state.processamento_ativo = True
    
    try:
        with st.spinner("🔄 Processando dados... Isso pode levar alguns minutos"):
            # Barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simular progresso (em produção, isso seria real)
            steps = [
                "Carregando planilhas...",
                "Validando dados...",
                "Aplicando exclusões...",
                "Calculando dias úteis...",
                "Calculando valores de VR...",
                "Gerando relatórios...",
                "Finalizando processamento..."
            ]
            
            for i, step in enumerate(steps):
                progress_bar.progress((i + 1) / len(steps))
                status_text.text(step)
                
                # Simular tempo de processamento
                import time
                time.sleep(0.5)
            
            # Processar com o agente
            resultado = st.session_state.agente.process_vr_complete(ano, mes_num)
            
            # Armazenar resultado
            st.session_state.resultado_processamento = resultado
            st.session_state.processamento_ativo = False
            
            # Mostrar resultado
            if resultado["sucesso"]:
                st.success("✅ Processamento concluído com sucesso!")
                render_resultado_processamento(resultado)
            else:
                st.error(f"❌ Erro no processamento: {resultado.get('erro', 'Erro desconhecido')}")
    
    except Exception as e:
        st.session_state.processamento_ativo = False
        st.error(f"❌ Erro durante o processamento: {str(e)}")

def render_resultado_processamento(resultado):
    """Renderiza o resultado do processamento"""
    
    # Métricas principais
    st.markdown("### �� Resultado do Processamento")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Funcionários Inicial",
            f"{resultado['total_funcionarios_inicial']:,}",
            delta=f"{resultado['total_funcionarios_final'] - resultado['total_funcionarios_inicial']}"
        )
    
    with col2:
        st.metric(
            "Funcionários Final",
            f"{resultado['total_funcionarios_final']:,}",
            delta=f"{resultado['total_funcionarios_final'] - resultado['total_funcionarios_inicial']}"
        )
    
    with col3:
        st.metric(
            "Total VR",
            f"R$ {resultado['total_vr']:,.2f}",
            delta=None
        )
    
    with col4:
        st.metric(
            "Problemas Detectados",
            resultado['problemas_encontrados'],
            delta=None
        )
    
    # Detalhes do processamento
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### �� Distribuição de Custos")
        st.write(f"**Empresa (80%):** R$ {resultado['total_empresa']:,.2f}")
        st.write(f"**Colaborador (20%):** R$ {resultado['total_colaborador']:,.2f}")
    
    with col2:
        st.markdown("#### 🚫 Exclusões Aplicadas")
        if resultado.get('exclusoes_aplicadas'):
            for exclusao in resultado['exclusoes_aplicadas']:
                st.write(f"• {exclusao}")
        else:
            st.write("Nenhuma exclusão aplicada")
    
    # Insights da IA
    if resultado.get('insights_ia'):
        render_ai_insights(resultado['insights_ia'])
    
    # Download do arquivo
    if os.path.exists(resultado["arquivo_saida"]):
        st.markdown("### �� Download do Relatório")
        
        with open(resultado["arquivo_saida"], "rb") as file:
            st.download_button(
                label="📊 Baixar Relatório Completo",
                data=file.read(),
                file_name=os.path.basename(resultado["arquivo_saida"]),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

def render_ai_insights(insights):
    """Renderiza os insights da IA"""
    st.markdown("### 🤖 Insights da Inteligência Artificial")
    
    if insights.get('resumo_geral'):
        st.markdown(f"""
        <div class="alert-info alert-box">
            <h4>📋 Resumo Geral</h4>
            <p>{insights['resumo_geral']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    if insights.get('alertas'):
        st.markdown(f"""
        <div class="alert-warning alert-box">
            <h4>⚠️ Alertas</h4>
            <ul>
                {''.join([f'<li>{alerta}</li>' for alerta in insights['alertas']])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    if insights.get('sugestoes'):
        st.markdown(f"""
        <div class="alert-success alert-box">
            <h4>�� Sugestões</h4>
            <ul>
                {''.join([f'<li>{sugestao}</li>' for sugestao in insights['sugestoes']])}
            </ul>
        </div>
        """, unsafe_allow_html=True)

def render_reports():
    """Renderiza a seção de relatórios"""
    st.markdown("## 📊 Relatórios e Análises")
    
    if st.session_state.resultado_processamento:
        # Relatório atual
        render_current_report()
        
        # Histórico de relatórios
        render_report_history()
    else:
        st.info("💡 Execute um processamento para gerar relatórios")
    
    # Relatórios disponíveis
    render_available_reports()

def render_current_report():
    """Renderiza o relatório atual"""
    st.markdown("### 📋 Relatório Atual")
    
    resultado = st.session_state.resultado_processamento
    
    if resultado.get('resumo_sindicatos'):
        st.markdown("#### 📈 Resumo por Sindicato")
        df_resumo = pd.DataFrame(resultado['resumo_sindicatos'])
        st.dataframe(df_resumo, use_container_width=True)
    
    # Validações
    if resultado.get('validacao_summary'):
        st.markdown("#### ✅ Resumo de Validações")
        validacao = resultado['validacao_summary']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Problemas", validacao.get('total_problemas', 0))
        
        with col2:
            st.metric("Problemas Críticos", validacao.get('problemas_criticos', 0))
        
        with col3:
            st.metric("Problemas de Aviso", validacao.get('problemas_aviso', 0))

def render_report_history():
    """Renderiza histórico de relatórios"""
    st.markdown("### 📚 Histórico de Relatórios")
    
    # Simular histórico (em produção, isso viria do banco de dados)
    historico = [
        {"data": "2025-09-15", "mes": "Setembro 2025", "status": "Concluído", "arquivo": "VR_2025_09_Processado.xlsx"},
        {"data": "2025-08-15", "mes": "Agosto 2025", "status": "Concluído", "arquivo": "VR_2025_08_Processado.xlsx"},
        {"data": "2025-07-15", "mes": "Julho 2025", "status": "Concluído", "arquivo": "VR_2025_07_Processado.xlsx"},
    ]
    
    df_historico = pd.DataFrame(historico)
    st.dataframe(df_historico, use_container_width=True)

def render_available_reports():
    """Renderiza relatórios disponíveis"""
    st.markdown("### 📁 Relatórios Disponíveis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **�� Relatório Principal**
        - Dados consolidados para operadora
        - Formato padrão VR Mensal
        - Pronto para envio
        """)
    
    with col2:
        st.markdown("""
        **📈 Relatório por Sindicato**
        - Consolidação por sindicato
        - Métricas de comparação
        - Análise de tendências
        """)
    
    with col3:
        st.markdown("""
        **✅ Relatório de Validações**
        - Problemas detectados
        - Sugestões de correção
        - Auditoria completa
        """)

def render_ai_queries():
    """Renderiza a seção de consultas IA"""
    st.markdown("## �� Consultas com Inteligência Artificial")
    
    # Interface de consulta
    st.markdown("### 💬 Faça uma Pergunta")
    
    pergunta = st.text_area(
        "Digite sua pergunta sobre os dados processados:",
        placeholder="Ex: Quantos funcionários foram excluídos? Quais sindicatos têm maior custo de VR?",
        height=100,
        help="A IA pode responder perguntas sobre os dados processados, tendências, anomalias e sugestões de melhoria"
    )
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        consultar = st.button("🤖 Consultar IA", use_container_width=True)
    
    with col2:
        if consultar and pergunta:
            try:
                with st.spinner("🤖 Analisando dados..."):
                    resposta = st.session_state.agente.consult_ai(pergunta)
                
                st.markdown(f"""
                <div class="alert-info alert-box">
                    <h4>🤖 Resposta da IA</h4>
                    <p>{resposta}</p>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Erro na consulta: {str(e)}")
        elif consultar and not pergunta:
            st.warning("⚠️ Digite uma pergunta antes de consultar a IA")
    
    # Exemplos de perguntas
    st.markdown("### �� Exemplos de Perguntas")
    
    exemplos = [
        "Quantos funcionários foram excluídos do processamento?",
        "Qual sindicato tem o maior custo total de VR?",
        "Há alguma anomalia nos dados que preciso verificar?",
        "Como posso otimizar o processo de VR?",
        "Quais são as principais tendências dos últimos meses?",
        "Existem funcionários com valores de VR muito altos ou baixos?"
    ]
    
    for exemplo in exemplos:
        if st.button(f"💬 {exemplo}", key=f"exemplo_{exemplo}"):
            st.session_state.pergunta_exemplo = exemplo
            st.rerun()
    
    # Se uma pergunta de exemplo foi selecionada
    if 'pergunta_exemplo' in st.session_state:
        pergunta = st.session_state.pergunta_exemplo
        del st.session_state.pergunta_exemplo
        
        try:
            with st.spinner("�� Analisando dados..."):
                resposta = st.session_state.agente.consult_ai(pergunta)
            
            st.markdown(f"""
            <div class="alert-info alert-box">
                <h4>🤖 Resposta da IA</h4>
                <p><strong>Pergunta:</strong> {pergunta}</p>
                <p><strong>Resposta:</strong> {resposta}</p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Erro na consulta: {str(e)}")

def render_footer():
    """Renderiza o footer"""
    st.markdown("""
    <div class="corporate-footer">
        <p><strong>�� Sistema VR/VA - Automação Corporativa</strong></p>
        <p>Desenvolvido com ❤️ usando OpenAI GPT e Streamlit</p>
        <p>Versão 2.0 - Arquitetura Limpa e Modular</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()