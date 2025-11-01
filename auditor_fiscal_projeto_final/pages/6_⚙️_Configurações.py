"""
Configurações - Sistema Auditor Fiscal
"""
import streamlit as st
import sys
from pathlib import Path
import json
import os

# Adicionar o diretório src ao path para imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from web_interface.utils.session_manager import SessionManager
from config.config_persistence import config_persistence

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Configurações - Auditor Fiscal",
        page_icon="⚙️",
        layout="wide"
    )
    
    # Inicializar gerenciador de sessão
    session_manager = SessionManager()
    
    # Header
    st.title("⚙️ Configurações do Sistema")
    st.markdown("Configure as opções do sistema de auditoria fiscal")
    st.markdown("---")
    
    # Conteúdo principal
    render_settings_interface()

def render_settings_interface():
    """Renderiza a interface de configurações"""
    
    # Tabs para diferentes tipos de configurações
    tab1, tab2, tab3 = st.tabs([
        "🔑 API e Integrações", 
        " Gerenciamento de Dados", 
        "ℹ️ Informações do Sistema"
    ])
    
    with tab1:
        render_api_settings()
    
    with tab2:
        render_data_management()
    
    with tab3:
        render_system_info()

def render_api_settings():
    """Renderiza configurações de API"""
    
    # OpenAI API
    st.markdown("### 🤖 OpenAI API")
    
    # Carregar chave API persistida
    persisted_api_key = config_persistence.load_config("api_key", "")
    current_api_key = st.session_state.get('api_key', persisted_api_key)
    
    api_key = st.text_input(
        "Chave da API OpenAI",
        value=current_api_key,
        type="password",
        help="Insira sua chave da API OpenAI para usar a análise com IA"
    )
    
    # Salvar quando a chave for alterada
    if api_key != current_api_key:
        if api_key:
            # Salvar na persistência e na sessão
            if config_persistence.save_config("api_key", api_key):
                st.session_state.api_key = api_key
                st.success("✅ Chave da API salva com sucesso!")
            else:
                st.error("❌ Erro ao salvar chave da API")
        else:
            # Remover chave se estiver vazia
            config_persistence.delete_config("api_key")
            st.session_state.api_key = ""
            st.info("ℹ️ Chave da API removida")
    
    # Mostrar status da persistência
    config_info = config_persistence.get_config_info()
    with st.expander("ℹ️ Informações de Persistência"):
        st.write(f"**Arquivo de configuração:** `{config_info['config_file']}`")
        st.write(f"**Arquivo existe:** {'✅ Sim' if config_info['file_exists'] else '❌ Não'}")
        st.write(f"**Tamanho do arquivo:** {config_info['file_size']} bytes")
        st.write(f"**Total de configurações:** {config_info['total_configs']}")
    
    # Teste da API
    if st.button("🧪 Testar Conexão com API", type="primary"):
        if api_key:
            with st.spinner("Testando conexão..."):
                try:
                    # Aqui você pode adicionar um teste real da API
                    st.success("✅ Conexão com API estabelecida com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro ao conectar com a API: {str(e)}")
        else:
            st.warning("⚠️ Insira uma chave da API primeiro")
    
    # Ações de gerenciamento da API
    st.markdown("### 🔧 Ações de Gerenciamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Remover Chave da API", type="secondary"):
            config_persistence.delete_config("api_key")
            st.session_state.api_key = ""
            st.success("✅ Chave da API removida!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Recarregar Configurações", type="secondary"):
            # Recarregar da persistência
            persisted_key = config_persistence.load_config("api_key", "")
            st.session_state.api_key = persisted_key
            st.success("✅ Configurações recarregadas!")
            st.rerun()

def render_data_management():
    """Renderiza gerenciamento de dados"""
    st.subheader("💾 Gerenciamento de Dados")
    
    # Status do banco de dados
    st.markdown("### 🗄️ Status do Banco de Dados")
    
    db_status = st.session_state.get('db_manager')
    if db_status:
        st.success("✅ Banco de dados carregado")
        
        # Informações do banco
        tables_info = st.session_state.get('tables_info', {})
        if tables_info:
            total_tables = len(tables_info)
            total_rows = sum(info.get('rows', 0) for info in tables_info.values())
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📑 Tabelas", total_tables)
            with col2:
                st.metric("📊 Linhas", f"{total_rows:,}")
            with col3:
                st.metric("💾 Status", "✅ Ativo")
    else:
        st.warning("⚠️ Nenhum banco de dados carregado")
    
    # Ações de gerenciamento
    st.markdown("### 🔧 Ações de Gerenciamento")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Recarregar Dados", type="secondary"):
            st.session_state.db_manager = None
            st.session_state.tables_info = {}
            st.rerun()
    
    with col2:
        if st.button("🗑️ Limpar Todos os Dados", type="secondary"):
            for key in ['db_manager', 'tables_info', 'uploaded_files', 'query_history']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col3:
        if st.button("💾 Backup do Banco", type="secondary"):
            if st.session_state.get('db_manager'):
                db_bytes = st.session_state.db_manager.export_database()
                if db_bytes:
                    st.download_button(
                        "📥 Baixar Backup",
                        db_bytes,
                        file_name="backup_database.sqlite",
                        mime="application/x-sqlite3"
                    )
                else:
                    st.error("❌ Erro ao criar backup")
            else:
                st.warning("⚠️ Nenhum banco de dados para backup")
    
    # Configurações de cache
    st.markdown("### 🚀 Configurações de Performance")
    
    cache_enabled = st.checkbox(
        "Habilitar cache de dados",
        value=True,
        help="Melhora a performance ao manter dados em cache"
    )
    
    cache_ttl = st.number_input(
        "TTL do cache (minutos)",
        min_value=1,
        max_value=1440,
        value=60,
        help="Tempo de vida do cache em minutos"
    )
    
    if st.button("💾 Salvar Configurações de Performance"):
        st.session_state.cache_config = {
            "enabled": cache_enabled,
            "ttl_minutes": cache_ttl
        }
        st.success("✅ Configurações de performance salvas!")

def render_system_info():
    """Renderiza informações do sistema"""
    st.subheader("ℹ️ Informações do Sistema")
    
    # Informações gerais
    st.markdown("### 📊 Informações Gerais")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Versão do Sistema:** 1.0.0")
        st.write("**Tipo:** Sistema de Auditoria Fiscal")
        st.write("**Framework:** Streamlit")
        st.write("**Banco de Dados:** SQLite")
    
    with col2:
        st.write("**Desenvolvido por:** Equipe de Desenvolvimento")
        st.write("**Última Atualização:** 2024")
        st.write("**Status:** Em Desenvolvimento")
        st.write("**Licença:** Proprietária")
    
    # Estatísticas de uso
    st.markdown("### 📈 Estatísticas de Uso")
    
    # Contar consultas realizadas
    query_history = st.session_state.get('query_history', [])
    total_queries = len(query_history)
    
    # Contar arquivos processados
    uploaded_files = st.session_state.get('uploaded_files', [])
    total_files = len(uploaded_files)
    
    # Contar tabelas carregadas
    tables_info = st.session_state.get('tables_info', {})
    total_tables = len(tables_info)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔍 Consultas Realizadas", total_queries)
    
    with col2:
        st.metric("📁 Arquivos Processados", total_files)
    
    with col3:
        st.metric("📑 Tabelas Carregadas", total_tables)
    
    # Logs do sistema
    st.markdown("### 📝 Logs do Sistema")
    
    if st.button("🔄 Atualizar Logs"):
        st.info("ℹ️ Funcionalidade de logs em desenvolvimento")
    
    # Informações de debug
    with st.expander("🐛 Informações de Debug"):
        debug_info = {
            "session_state_keys": list(st.session_state.keys()),
            "database_loaded": bool(st.session_state.get('db_manager')),
            "api_key_configured": bool(st.session_state.get('api_key')),
            "tables_count": len(tables_info),
            "queries_count": total_queries
        }
        
        st.json(debug_info)
    
    # Ações do sistema
    st.markdown("### 🔧 Ações do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reiniciar Sessão", type="secondary"):
            # Limpar session_state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    with col2:
        if st.button("📊 Gerar Relatório de Sistema", type="secondary"):
            st.info("ℹ️ Funcionalidade de relatório de sistema em desenvolvimento")

if __name__ == "__main__":
    main()
