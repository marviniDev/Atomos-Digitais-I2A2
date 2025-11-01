"""
Upload de Documentos - Sistema Auditor Fiscal
"""
import streamlit as st
import asyncio
import sys
from pathlib import Path

# Adicionar o diretório src ao path para imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from web_interface.utils.session_manager import SessionManager
from data_loader.file_processor import FileProcessor
from data_loader.nfe_xml_processor import NFeXMLProcessor
from database.db_manager import DatabaseManager

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Upload - Auditor Fiscal",
        page_icon="📤",
        layout="wide"
    )
    
    # Inicializar gerenciador de sessão
    session_manager = SessionManager()
    
    # Header
    st.title("📤 Upload de Documentos")
    st.markdown("Carregue seus arquivos CSV ou ZIP contendo dados fiscais para análise")
    
    # Conteúdo principal
    render_upload_section()

def render_upload_section():
    """Renderiza a seção de upload de arquivos"""
    
    # Tabs para diferentes tipos de upload
    tab1, tab2 = st.tabs([ 
        "📄 Upload XML NFe", 
        "📋 Templates de Exemplo"
    ])
    
    with tab1:
        render_xml_upload()
    
    with tab2:
        render_templates_section()

def render_xml_upload():
    """Renderiza seção de upload de XML de NFe"""
    st.markdown("### 📄 Upload de arquivos XML de NFe")
    st.markdown("Faça upload de arquivos XML de Nota Fiscal Eletrônica para análise fiscal")
    
    # Upload de arquivo XML
    uploaded_xml = st.file_uploader(
        "📄 Upload de arquivo XML",
        type=['xml'],
        help="Faça upload de um arquivo XML de NFe (individual ou lote)",
        key="xml_uploader"
    )
    
    # Verificar se arquivo foi processado recentemente para evitar reprocessamento
    if uploaded_xml is not None:
        # Criar hash do conteúdo para identificar arquivo único
        file_hash_key = f"processed_file_{hash(uploaded_xml.getvalue())}"
        
        # Verificar se já foi processado nesta sessão
        if st.session_state.get(file_hash_key) != True:
            process_xml_upload(uploaded_xml, file_hash_key)
        else:
            st.info("ℹ️ Este arquivo já foi processado. Faça upload de um novo arquivo para processar novamente.")
    
    # Informações sobre formato XML
    with st.expander("ℹ️ Informações sobre formato XML"):
        st.markdown("""
        **Formatos aceitos:**
        - NFe individual (elemento raiz: `<NFe>`)
        - Lote de NFe (elemento raiz: `<enviNFe>`)
        
        **Validações realizadas:**
        - Estrutura XML válida
        - Namespace correto (`http://www.portalfiscal.inf.br/nfe`)
        - Elementos obrigatórios presentes
        - Dados inseridos nas tabelas `nfe_notas_fiscais` e `nfe_itens_nota`
        
        **Dados extraídos:**
        - Informações da nota fiscal
        - Dados do emitente e destinatário
        - Itens da nota com impostos
        - Totais e valores tributários
        """)

def render_templates_section():
    """Renderiza seção de templates de exemplo"""
    st.markdown("### 📋 Templates de Exemplo")
    st.markdown("Baixe templates de exemplo para testar o sistema")
    
    # Listar templates disponíveis
    templates_dir = Path(__file__).parent.parent / "data" / "templates"
    
    if templates_dir.exists():
        xml_files = list(templates_dir.glob("*.xml"))
        
        if xml_files:
            st.markdown("**Templates XML de NFe disponíveis:**")
            
            for xml_file in xml_files:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"📄 {xml_file.name}")
                
                with col2:
                    # Ler conteúdo do arquivo
                    try:
                        with open(xml_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        st.download_button(
                            "📥 Baixar",
                            content,
                            file_name=xml_file.name,
                            mime="application/xml",
                            key=f"download_{xml_file.name}"
                        )
                    except Exception as e:
                        st.error(f"Erro ao ler arquivo: {str(e)}")
        else:
            st.info("ℹ️ Nenhum template XML encontrado")
    else:
        st.warning("⚠️ Diretório de templates não encontrado")

def process_xml_upload(uploaded_file, file_hash_key: str):
    """Processa upload de arquivo XML"""
    try:
        # Ler conteúdo do arquivo
        content = uploaded_file.read().decode('utf-8')
        
        # Processar XML
        result = process_xml_content(content, uploaded_file.name)
        
        if result["status"] == "success":
            # Marcar arquivo como processado para evitar reprocessamento
            st.session_state[file_hash_key] = True
            
            st.success(f"✅ Arquivo {uploaded_file.name} processado com sucesso!")
            
            # Mostrar estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 Notas Processadas", result["notas_inseridas"])
            with col2:
                st.metric("📦 Itens Processados", result["itens_inseridos"])
            with col3:
                st.metric("📋 Tipo", result["tipo"])
            
            # Exibir avisos de validação se houver
            if "validation_warnings" in result and result["validation_warnings"]:
                st.warning("⚠️ Avisos de validação pós-cadastro:")
                for warning in result["validation_warnings"]:
                    st.write(f"• {warning}")
            else:
                st.info("✅ Validação pós-cadastro concluída: dados inseridos corretamente")
            
            # Não fazer rerun automático - deixar o usuário decidir quando recarregar
            st.info("💡 Arquivo processado. Para processar outro arquivo, faça upload de um novo arquivo XML.")
            
        else:
            st.error(f"❌ Erro ao processar arquivo: {result['message']}")
            if "errors" in result:
                for error in result["errors"]:
                    st.error(f"• {error}")
                    
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo XML: {str(e)}")

def process_xml_content(xml_content: str, filename: str):
    """Processa conteúdo XML"""
    try:
        # Verificar se há banco de dados
        if not st.session_state.get('db_manager'):
            return {
                "status": "error",
                "message": "Banco de dados não inicializado"
            }
        
        # Criar processador XML
        xml_processor = NFeXMLProcessor(st.session_state.db_manager)
        
        # Processar XML
        result = xml_processor.process_xml_file(xml_content, filename)
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao processar XML: {str(e)}"
        }

if __name__ == "__main__":
    main()
