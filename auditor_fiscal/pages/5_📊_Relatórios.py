"""
Relatórios - Sistema Auditor Fiscal
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Adicionar o diretório src ao path para imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from web_interface.components.metrics import render_metrics_grid
from web_interface.utils.session_manager import SessionManager
from services.auditor_service import AuditorService

def _count_inconsistencies_from_ai_result(ai_result: str) -> int:
    """
    Conta inconsistências de um resultado de IA salvo no banco (string JSON)
    
    Args:
        ai_result: String JSON do resultado da IA
        
    Returns:
        Número de inconsistências encontradas
    """
    import json
    
    inconsistencies_count = 0
    
    try:
        # Converter string JSON para objeto
        if isinstance(ai_result, str):
            ai_data = json.loads(ai_result)
        else:
            ai_data = ai_result
        
        # Obter dados de results
        results_data = ai_data.get('results', [])
        
        # Se results é uma string JSON, converter para objeto
        if isinstance(results_data, str):
            try:
                results_data = json.loads(results_data)
            except json.JSONDecodeError:
                return 0
        
        # Processar diferentes estruturas de dados
        if isinstance(results_data, dict):
            # Estrutura: {"inconsistencias": [...]}
            if 'inconsistencias' in results_data:
                inconsistencies_count = len(results_data['inconsistencias'])
        elif isinstance(results_data, list):
            # Estrutura: [{"inconsistencias": [...]}, ...]
            for result in results_data:
                if isinstance(result, dict) and 'inconsistencias' in result:
                    inconsistencies_count += len(result['inconsistencias'])
        
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    
    return inconsistencies_count

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Relatórios - Auditor Fiscal",
        page_icon="📊",
        layout="wide"
    )
    
    # Inicializar gerenciador de sessão
    session_manager = SessionManager()
    
    # Header
    st.title("📊 Relatórios e Visualizações")
    st.markdown("Gere relatórios detalhados e visualizações dos dados fiscais")
    st.markdown("---")
    
    # Verificar se há banco de dados carregado
    if not st.session_state.get('db_manager'):
        st.warning("⚠️ Nenhum banco de dados carregado")
        st.info("💡 Acesse a página 'Documentos' para carregar dados CSV primeiro")
        return
    
    # Conteúdo principal
    render_reports_interface()

def render_reports_interface():
    """Renderiza a interface de relatórios"""
    
    # Tabs para diferentes tipos de relatórios
    tabs_list = st.tabs([
        "📊 Resultados de Auditoria",
        "💾 Exportar Dados"
    ])
    
    with tabs_list[0]:
        render_audit_results_section()
    
    with tabs_list[1]:
        render_export_section()

def render_audit_results_section():
    """Renderiza seção de resultados de auditoria"""
    st.subheader("📊 Resultados de Auditoria")
    st.markdown("Visualize e analise os resultados das auditorias fiscais realizadas")
    
    try:
        # Inicializar serviço de auditoria
        auditor_service = AuditorService(st.session_state.db_manager)
        auditor_service.initialize_results_table()
        
        # Obter todos os resultados
        all_results = auditor_service.get_audit_results()
        
        if not all_results:
            st.info("ℹ️ Nenhum resultado de auditoria encontrado ainda.")
            st.info("💡 Realize análises na página 'Notas' ou 'Análise IA' para gerar resultados.")
            return
        
        # Estatísticas gerais
        st.markdown("### 📈 Estatísticas Gerais")
        col1, col2, col3, col4 = st.columns(4)
        
        total_audits = len(all_results)
        total_documents = sum(r.get('document_count', 0) for r in all_results)
        total_value = sum(r.get('total_value', 0.0) for r in all_results)
        
        # Recalcular inconsistências usando parsing correto do JSON
        total_inconsistencies = 0
        for r in all_results:
            ai_result = r.get('ai_result', '')
            if ai_result:
                total_inconsistencies += _count_inconsistencies_from_ai_result(ai_result)
        
        with col1:
            st.metric("📊 Total de Auditorias", total_audits)
        with col2:
            st.metric("📄 Documentos Analisados", f"{total_documents:,}")
        with col3:
            st.metric("💰 Valor Total Fiscalizado", f"R$ {total_value:,.2f}")
        with col4:
            st.metric("🚨 Total de Inconsistências", total_inconsistencies)
        
        st.markdown("---")
        
        # Filtros e visualizações
        st.markdown("### 🔍 Visualizações e Análises")
        
        # Converter para DataFrame
        df = pd.DataFrame(all_results)
        
        # Recalcular inconsistências para cada linha do DataFrame
        df['inconsistencies_found'] = df['ai_result'].apply(
            lambda x: _count_inconsistencies_from_ai_result(x) if x else 0
        )
        
        # Formatação de datas
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['data'] = df['timestamp'].dt.date
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de auditorias por tipo de análise
            if 'analysis_type' in df.columns and df['analysis_type'].notna().any():
                analysis_counts = df['analysis_type'].value_counts()
                fig = px.bar(
                    x=analysis_counts.index,
                    y=analysis_counts.values,
                    labels={'x': 'Tipo de Análise', 'y': 'Quantidade'},
                    title='📊 Auditorias por Tipo de Análise',
                    color=analysis_counts.values,
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Gráfico de status
            if 'status' in df.columns:
                status_counts = df['status'].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title='📈 Status das Auditorias',
                    color_discrete_map={'completed': '#00CC96', 'pending': '#FFA15A', 'failed': '#EF553B'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gráfico de inconsistências ao longo do tempo
            if 'timestamp' in df.columns and 'inconsistencies_found' in df.columns:
                df_sorted = df.sort_values('timestamp')
                fig = px.line(
                    df_sorted,
                    x='timestamp',
                    y='inconsistencies_found',
                    labels={'timestamp': 'Data', 'inconsistencies_found': 'Inconsistências'},
                    title='📉 Inconsistências ao Longo do Tempo',
                    markers=True
                )
                fig.update_traces(line_color='#EF553B')
                st.plotly_chart(fig, use_container_width=True)
            
            # Gráfico de tempo de processamento
            if 'processing_time_seconds' in df.columns:
                fig = px.histogram(
                    df,
                    x='processing_time_seconds',
                    labels={'processing_time_seconds': 'Tempo (segundos)', 'count': 'Frequência'},
                    title='⏱️ Distribuição do Tempo de Processamento',
                    nbins=20
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Tabela de resultados
        st.markdown("### 📋 Resultados Detalhados")
        
        # Filtrar colunas para exibição
        display_columns = ['id', 'access_key', 'timestamp', 'document_count', 'total_value', 
                          'inconsistencies_found', 'processing_time_seconds', 'analysis_type', 'status']
        available_columns = [col for col in display_columns if col in df.columns]
        
        # Adicionar coluna formatada de valor
        if 'total_value' in df.columns:
            df['valor_formatado'] = df['total_value'].apply(lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "R$ 0,00")
            available_columns.append('valor_formatado')
        
        # Seleção de filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            if 'status' in df.columns:
                status_filter = st.multiselect(
                    "Filtrar por Status:",
                    options=df['status'].unique().tolist(),
                    default=df['status'].unique().tolist(),
                    key="status_filter"
                )
                df_filtered = df[df['status'].isin(status_filter)] if status_filter else df
            else:
                df_filtered = df
        
        with col2:
            if 'analysis_type' in df.columns and df['analysis_type'].notna().any():
                type_filter = st.multiselect(
                    "Filtrar por Tipo:",
                    options=df['analysis_type'].unique().tolist(),
                    default=df['analysis_type'].unique().tolist(),
                    key="type_filter"
                )
                df_filtered = df_filtered[df_filtered['analysis_type'].isin(type_filter)] if type_filter else df_filtered
        
        with col3:
            # Ordenação
            sort_by = st.selectbox(
                "Ordenar por:",
                options=['timestamp', 'inconsistencies_found', 'total_value', 'processing_time_seconds'],
                key="sort_by",
                index=0
            )
            sort_order = st.selectbox(
                "Ordem:",
                options=['Descendente', 'Ascendente'],
                key="sort_order",
                index=0
            )
            
            ascending = sort_order == 'Ascendente'
            if sort_by in df_filtered.columns:
                df_filtered = df_filtered.sort_values(by=sort_by, ascending=ascending)
        
        # Exibir tabela
        display_df = df_filtered[available_columns].copy()
        
        # Renomear colunas para exibição
        column_mapping = {
            'id': 'ID',
            'access_key': 'Chave de Acesso',
            'timestamp': 'Data/Hora',
            'document_count': 'Documentos',
            'total_value': 'Valor Total',
            'valor_formatado': 'Valor (Formatado)',
            'inconsistencies_found': 'Inconsistências',
            'processing_time_seconds': 'Tempo (s)',
            'analysis_type': 'Tipo de Análise',
            'status': 'Status'
        }
        
        display_df = display_df.rename(columns=column_mapping)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Detalhes de um resultado específico
        st.markdown("---")
        st.markdown("### 🔍 Detalhes de Auditoria")
        
        selected_id = st.selectbox(
            "Selecione uma auditoria para ver detalhes:",
            options=df_filtered['id'].tolist(),
            format_func=lambda x: f"ID {x} - {df_filtered[df_filtered['id'] == x]['timestamp'].values[0] if len(df_filtered[df_filtered['id'] == x]) > 0 else ''}",
            key="audit_detail_selector"
        )
        
        if selected_id:
            selected_result = df_filtered[df_filtered['id'] == selected_id].iloc[0]
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**📄 Informações Básicas:**")
                st.json({
                    'ID': int(selected_result.get('id', 'N/A')),
                    'Chave de Acesso': selected_result.get('access_key', 'N/A'),
                    'Data/Hora': str(selected_result.get('timestamp', 'N/A')),
                    'Status': selected_result.get('status', 'N/A'),
                    'Tipo de Análise': selected_result.get('analysis_type', 'N/A')
                })
            
            with col2:
                st.markdown("**📊 Métricas:**")
                # Recalcular inconsistências para o resultado selecionado
                ai_result = selected_result.get('ai_result', '')
                correct_inconsistencies = _count_inconsistencies_from_ai_result(ai_result) if ai_result else 0
                
                st.json({
                    'Documentos Analisados': int(selected_result.get('document_count', 0)),
                    'Valor Total': f"R$ {selected_result.get('total_value', 0.0):,.2f}",
                    'Inconsistências Encontradas': correct_inconsistencies,
                    'Tempo de Processamento': f"{selected_result.get('processing_time_seconds', 0.0):.2f}s"
                })
            
            # Resultado da IA (se disponível)
            ai_result = selected_result.get('ai_result')
            if ai_result:
                with st.expander("🤖 Resultado da Análise IA", expanded=False):
                    try:
                        if isinstance(ai_result, str):
                            import json
                            ai_result = json.loads(ai_result)
                        st.json(ai_result)
                    except:
                        st.text(str(ai_result)[:1000] + "..." if len(str(ai_result)) > 1000 else str(ai_result))
        
        # Estatísticas adicionais
        st.markdown("---")
        st.markdown("### 📊 Estatísticas Avançadas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'processing_time_seconds' in df.columns:
                avg_time = df['processing_time_seconds'].mean()
                st.metric("⏱️ Tempo Médio de Processamento", f"{avg_time:.2f}s")
        
        with col2:
            if 'inconsistencies_found' in df.columns:
                avg_inconsistencies = df['inconsistencies_found'].mean()
                st.metric("🚨 Média de Inconsistências", f"{avg_inconsistencies:.2f}")
        
        with col3:
            if 'total_value' in df.columns:
                avg_value = df['total_value'].mean()
                st.metric("💰 Valor Médio por Auditoria", f"R$ {avg_value:,.2f}")
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar resultados de auditoria: {str(e)}")
        st.exception(e)

def render_export_section():
    """Renderiza seção de exportação de dados"""
    st.subheader("💾 Exportar Dados")
    
    # Exportar banco de dados
    st.subheader("🗄️ Exportar Banco de Dados")
    
    if st.session_state.get('db_manager'):
        db_bytes = st.session_state.db_manager.export_database()
        if db_bytes:
            st.download_button(
                "📥 Baixar Banco de Dados Completo",
                db_bytes,
                file_name=f"auditor_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite",
                mime="application/x-sqlite3",
                help="Baixa o banco de dados completo em formato SQLite"
            )
        else:
            st.warning("⚠️ Não foi possível exportar o banco de dados")

if __name__ == "__main__":
    main()
