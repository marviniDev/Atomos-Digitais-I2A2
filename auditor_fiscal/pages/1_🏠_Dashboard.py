"""
Dashboard Principal - Sistema Auditor Fiscal
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Adicionar o diretório src ao path para imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from web_interface.utils.session_manager import SessionManager
from services.auditor_service import AuditorService

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Dashboard - Auditor Fiscal",
        page_icon="🏠",
        layout="wide"
    )
    
    # Inicializar gerenciador de sessão
    session_manager = SessionManager()
    
    # Header
    st.title("🏠 Dashboard Principal")
    st.markdown("Visão geral do sistema de auditoria fiscal")
    st.markdown("---")
    
    # Carregar métricas fiscais
    render_fiscal_metrics()
    
def render_fiscal_metrics():
    """Renderiza as métricas fiscais no dashboard"""
    
    # Verificar se há banco de dados inicializado
    if not st.session_state.get('db_manager'):
        st.warning("⚠️ Nenhum banco de dados carregado")
        st.info("💡 Acesse a página 'Documentos' para carregar dados CSV primeiro")
        _render_quick_actions()
        return
    
    # Inicializar serviço de auditoria
    auditor_service = AuditorService(st.session_state.db_manager)
    auditor_service.initialize_results_table()
    
    # Obter estatísticas
    stats = auditor_service.get_audit_statistics()
    
    # Métricas principais
    st.subheader("📊 Métricas de Auditoria Fiscal")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📄 Total de Documentos",
            value=f"{stats['total_documents']:,}",
            help="Total de documentos fiscais analisados"
        )
    
    with col2:
        st.metric(
            label="💰 Valor Total Fiscalizado",
            value=f"R$ {stats['total_value']:,.2f}",
            help="Valor total fiscalizado em Reais"
        )
    
    with col3:
        st.metric(
            label="🚨 Inconsistências",
            value=f"{stats['total_inconsistencies']:,}",
            delta=f"{stats['total_inconsistencies']} problemas detectados" if stats['total_inconsistencies'] > 0 else None,
            help="Total de inconsistências encontradas"
        )
    
    with col4:
        avg_time = stats['average_processing_time']
        st.metric(
            label="⏱️ Tempo Médio",
            value=f"{avg_time:.2f}s",
            help="Tempo médio de processamento"
        )
    
    # Auditorias recentes
    st.markdown("---")
    st.subheader("📋 Auditorias Recentes")
    
    recent_audits = auditor_service.get_recent_audits(limit=5)
    
    if recent_audits:
        # Exibir em cards
        for i, audit in enumerate(recent_audits):
            with st.expander(f"🔍 Auditoria {i+1} - {audit.get('timestamp', 'N/A')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Status:** {audit.get('status', 'N/A')}")
                    st.write(f"**Documentos:** {audit.get('document_count', 0)}")
                
                with col2:
                    st.write(f"**Valor:** R$ {audit.get('total_value', 0):,.2f}")
                    st.write(f"**Inconsistências:** {audit.get('inconsistencies_found', 0)}")
                
                with col3:
                    st.write(f"**Tempo:** {audit.get('processing_time_seconds', 0):.2f}s")
                    st.write(f"**Tipo:** {audit.get('analysis_type', 'N/A')}")
    else:
        st.info("ℹ️ Nenhuma auditoria realizada ainda. Comece analisando documentos!")
    
    # Status das auditorias ativas
    st.markdown("---")
    st.subheader("⚡ Status das Auditorias")
    
    all_audits = auditor_service.get_audit_results()
    active_audits = [a for a in all_audits if a.get('status') == 'pending']
    completed_audits = [a for a in all_audits if a.get('status') == 'completed']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🔄 Auditorias Ativas",
            value=len(active_audits),
            help="Auditorias em processamento"
        )
    
    with col2:
        st.metric(
            label="✅ Auditorias Concluídas",
            value=len(completed_audits),
            help="Auditorias finalizadas"
        )
    
    with col3:
        st.metric(
            label="📊 Total de Auditorias",
            value=len(all_audits),
            help="Total de auditorias realizadas"
        )
    
    # Alertas de irregularidades
    if stats['total_inconsistencies'] > 0:
        st.markdown("---")
        st.error(f"🚨 **ALERTA:** {stats['total_inconsistencies']} inconsistências detectadas! "
                f"Clique aqui para ver os detalhes.")
    
    # Ações rápidas
    _render_quick_actions()

def _render_quick_actions():
    """Renderiza ações rápidas"""
    st.markdown("---")
    st.subheader("🚀 Ações Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📤 Upload de Documentos**
        
        Carregue arquivos CSV ou ZIP contendo dados fiscais para análise.
        """)
        if st.button("Ir para Upload", key="quick_upload", use_container_width=True):
            st.switch_page("pages/2_📤_Documentos.py")
    
    with col2:
        st.markdown("""
        **🔍 Análise com IA**
        
        Use inteligência artificial para analisar dados fiscais e detectar irregularidades.
        """)
        if st.button("Ir para Análise", key="quick_analysis", use_container_width=True):
            st.switch_page("pages/3_🔍_Análise_IA.py")
    
    with col3:
        st.markdown("""
        **📊 Relatórios**
        
        Gere relatórios detalhados sobre os dados carregados.
        """)
        if st.button("Ir para Relatórios", key="quick_reports", use_container_width=True):
            st.switch_page("pages/4_📊_Relatórios.py")

if __name__ == "__main__":
    main()
