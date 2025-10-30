"""
Sistema Auditor Fiscal - Aplicação Principal
"""
import streamlit as st
import sys
import logging
from pathlib import Path

# Configurar logging ANTES de importar outros módulos
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Adicionar o diretório src ao path para imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.web_interface.utils.session_manager import SessionManager

# Logger principal
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 50)
    logger.info("🚀 Sistema Auditor Fiscal - Iniciando")
    logger.info("=" * 50)
    # Configuração global da página
    st.set_page_config(
        page_title="Sistema Auditor Fiscal",
        page_icon="👮‍♂️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inicializar gerenciador de sessão
    session_manager = SessionManager()
    
    # Header principal
    st.title("👮‍♂️ Sistema Auditor Fiscal")
    st.markdown("Sistema inteligente para análise e auditoria de dados fiscais")
    st.markdown("---")
    
    # Mensagem de boas-vindas
    st.markdown("""
    ## 👋 Bem-vindo ao Sistema Auditor Fiscal
    
    Este sistema oferece ferramentas avançadas para análise e auditoria de dados fiscais, 
    utilizando inteligência artificial para detectar irregularidades e gerar insights valiosos.
    
    ### 🚀 Funcionalidades Principais
    
    - **🏠 Dashboard**: Visão geral do sistema e métricas principais
    - **📤 Upload de Documentos**: Carregamento e processamento de arquivos CSV/ZIP
    - **🔍 Análise com IA**: Consultas inteligentes e detecção de irregularidades
    - **📊 Relatórios**: Geração de relatórios detalhados e visualizações
    - **⚙️ Configurações**: Configuração do sistema e gerenciamento de dados
    
    ### 📋 Como Começar
    
    1. **Configure sua chave da API OpenAI** na barra lateral
    2. **Acesse a página 'Documentos'** para carregar seus dados CSV
    3. **Use a página 'Análise IA'** para fazer consultas inteligentes
    4. **Gere relatórios** na página de Relatórios
    
    ### 💡 Dicas
    
    - Use o menu lateral para navegar entre as páginas
    - O sistema detecta automaticamente arquivos CSV na pasta `data/input`
    - Todas as consultas são salvas no histórico para referência futura
    """)
    
    # Status do sistema
    st.markdown("---")
    st.subheader("📊 Status do Sistema")
    
    # Verificar status
    system_metrics = session_manager.get_system_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if system_metrics["database_loaded"]:
            st.success("✅ Banco de Dados")
        else:
            st.warning("⚠️ Banco de Dados")
    
    with col2:
        if system_metrics["api_key_configured"]:
            st.success("✅ API Configurada")
        elif not system_metrics["api_key_configured"]:
            st.warning("⚠️ API Não Configurada")
        else:
            st.warning("⚠️ API Não Configurada")
    
    with col3:
        if system_metrics["tables_count"] > 0:
            st.success(f"✅ {system_metrics['tables_count']} Tabelas")
        else:
            st.info("ℹ️ Nenhuma Tabela")
    
    with col4:
        if system_metrics["queries_count"] > 0:
            st.info(f"🔍 {system_metrics['queries_count']} Consultas")
        else:
            st.info("ℹ️ Nenhuma Consulta")
    
    # Informações adicionais
    st.markdown("---")
    st.subheader("ℹ️ Informações do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🔧 Tecnologias Utilizadas**
        - Streamlit para interface web
        - SQLite para banco de dados
        - OpenAI GPT para análise com IA
        - Pandas para processamento de dados
        - Plotly para visualizações
        """)
    
    with col2:
        st.markdown("""
        **📞 Suporte**
        - Documentação: Disponível em cada página
        - Logs: Acesse a página de Configurações
        - Debug: Use o painel de debug nas configurações
        """)

if __name__ == "__main__":
    main()