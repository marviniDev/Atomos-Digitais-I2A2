"""
Componente de Sidebar Reutilizável
"""
import streamlit as st
from pathlib import Path

def render_sidebar():
    """Renderiza a sidebar unificada para todas as páginas"""
    with st.sidebar:
        # Header da sidebar
        st.header("⚙️ Configuração")
        
        # API Key
        st.session_state.api_key = st.text_input("Chave da API OpenAI", type="password")
        
        # Status do sistema
        st.markdown("---")
        st.subheader("📊 Status do Sistema")
        
        if st.session_state.get('db_manager'):
            st.success("✅ Banco inicializado")
            if st.session_state.get('tables_info'):
                st.info(f"📊 {len(st.session_state.tables_info)} tabelas carregadas")
        else:
            st.warning("⚠️ Banco não inicializado")
        
        # Informações sobre arquivos
        st.markdown("---")
        st.subheader("📁 Arquivos")
        input_path = Path(__file__).parent.parent.parent.parent / "data" / "input"
        if input_path.exists():
            csv_files = list(input_path.glob("*.csv"))
            if csv_files:
                st.write(f"📁 {len(csv_files)} arquivo(s) CSV encontrado(s)")
                for csv_file in csv_files:
                    st.write(f"• {csv_file.name}")
            else:
                st.write("📁 Nenhum arquivo CSV encontrado")
        
        # Controles de dados
        st.markdown("---")
        st.subheader("🔄 Controles")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Recarregar", help="Força o recarregamento dos dados CSV"):
                st.session_state.db_manager = None
                st.session_state.tables_info = {}
                st.rerun()
        
        with col2:
            if st.button("🗑️ Limpar", help="Limpa todos os dados carregados"):
                for key in ['db_manager', 'tables_info', 'uploaded_files']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
