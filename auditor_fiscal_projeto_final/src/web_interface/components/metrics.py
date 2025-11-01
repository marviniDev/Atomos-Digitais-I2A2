"""
Componentes de métricas reutilizáveis
"""
import streamlit as st

def render_metric_card(title, value, delta=None, help_text=None):
    """
    Renderiza um card de métrica
    
    Args:
        title: Título da métrica
        value: Valor principal
        delta: Variação (opcional)
        help_text: Texto de ajuda (opcional)
    """
    st.metric(
        label=title,
        value=value,
        delta=delta,
        help=help_text
    )

def render_metrics_grid(metrics_data):
    """
    Renderiza um grid de métricas
    
    Args:
        metrics_data: Lista de dicionários com dados das métricas
    """
    if not metrics_data:
        st.info("Nenhuma métrica disponível")
        return
    
    # Calcular número de colunas baseado no número de métricas
    num_metrics = len(metrics_data)
    if num_metrics <= 2:
        cols = st.columns(2)
    elif num_metrics <= 4:
        cols = st.columns(4)
    else:
        cols = st.columns(4)
    
    for i, metric in enumerate(metrics_data):
        with cols[i % len(cols)]:
            render_metric_card(
                title=metric.get('title', ''),
                value=metric.get('value', 0),
                delta=metric.get('delta'),
                help_text=metric.get('help_text')
            )

def render_database_status():
    """Renderiza o status do banco de dados"""
    if st.session_state.get('db_manager') and st.session_state.get('tables_info'):
        # Calcular métricas do banco
        total_tables = len(st.session_state.tables_info)
        total_rows = sum(info.get('rows', 0) for info in st.session_state.tables_info.values())
        total_columns = sum(len(info.get('columns', [])) for info in st.session_state.tables_info.values())
        
        metrics_data = [
            {
                'title': '📊 Total de Linhas',
                'value': f"{total_rows:,}",
                'help_text': 'Total de registros no banco de dados'
            },
            {
                'title': '📋 Total de Colunas',
                'value': total_columns,
                'help_text': 'Total de colunas em todas as tabelas'
            },
            {
                'title': '📑 Total de Tabelas',
                'value': total_tables,
                'help_text': 'Número de tabelas carregadas'
            },
            {
                'title': '💾 Status',
                'value': '✅ Ativo',
                'help_text': 'Status da conexão com o banco'
            }
        ]
        
        render_metrics_grid(metrics_data)
    else:
        st.warning("⚠️ Nenhum banco de dados carregado")
