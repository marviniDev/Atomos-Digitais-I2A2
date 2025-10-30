"""
Análise com IA - Sistema Auditor Fiscal
"""
import streamlit as st
import asyncio
import datetime
import pandas as pd
import sys
from pathlib import Path

# Adicionar o diretório src ao path para imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from web_interface.utils.session_manager import SessionManager
from ai_service.data_analyzer import DataAnalyzer

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Análise IA - Auditor Fiscal",
        page_icon="🔍",
        layout="wide"
    )
    
    # Inicializar gerenciador de sessão
    session_manager = SessionManager()
    
    # Header
    st.title("🔍 Análise Inteligente com IA")
    st.markdown("Use inteligência artificial para analisar dados fiscais e detectar irregularidades")
    st.markdown("---")
    
    # Verificar se há banco de dados carregado
    if not st.session_state.get('db_manager'):
        st.warning("⚠️ Nenhum banco de dados carregado")
        st.info("💡 Acesse a página 'Documentos' para carregar dados CSV primeiro")
        return
    
    # Conteúdo principal
    render_analysis_interface()

def render_analysis_interface():
    """Renderiza a interface de análise com IA"""
    
    # Verificar se API key está configurada
    if not st.session_state.get('api_key'):
        st.error("❌ Chave da API OpenAI não configurada")
        st.info("💡 Configure sua chave da API nas configurações")
        return
    
    # Input da pergunta
    st.subheader("💬 Faça sua pergunta sobre os dados")
    
    # Configurações de limite
    col1, col2 = st.columns([3, 1])
    
    with col1:
        question = st.text_area(
            "Digite sua pergunta sobre os dados fiscais...",
            placeholder="Ex: Quais são os fornecedores com maior valor de compras em janeiro?",
            help="Faça perguntas sobre os dados carregados. A IA irá gerar consultas SQL e analisar os resultados.",
            height=100
        )
    
    with col2:
        max_results = st.number_input(
            "Máximo de resultados",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            help="Limite de registros retornados (evita sobrecarga do sistema)"
        )
    
    # Botão de análise
    if question and st.button("🤖 Analisar com IA", type="primary", use_container_width=True):
        with st.spinner("🧠 Analisando dados com IA..."):
            try:
                # Processar consulta
                sql_query, query_results, answer = asyncio.run(
                    _process_query(question, st.session_state.api_key, max_results)
                )
                
                # Adicionar ao histórico
                query_result = {
                    "question": question,
                    "sql": sql_query,
                    "results": query_results,
                    "answer": answer,
                    "timestamp": datetime.datetime.now()
                }
                
                if 'query_history' not in st.session_state:
                    st.session_state.query_history = []
                st.session_state.query_history.append(query_result)
                
                # Exibir resultados
                _display_query_results(answer, sql_query, query_results, max_results)
                
            except Exception as e:
                st.error(f"❌ Erro ao processar pergunta: {str(e)}")
    
    # Histórico de consultas
    _render_query_history()
    
    # Sugestões de perguntas
    _render_suggested_questions()

async def _process_query(question: str, api_key: str, max_results: int = 100) -> tuple:
    """
    Processa uma consulta do usuário
    
    Args:
        question: Pergunta do usuário
        api_key: Chave da API OpenAI
        
    Returns:
        Tupla com (sql_query, results, answer)
    """
    try:
        # Verificar se banco existe
        if 'db_manager' not in st.session_state:
            raise Exception("❌ Nenhum banco de dados carregado. Faça upload de arquivos primeiro.")
        
        # Inicializar analisador
        analyzer = DataAnalyzer(api_key)
        
        # Obter schema do banco existente
        schema_info = st.session_state.db_manager.get_schema_info()
        
        if not schema_info:
            raise Exception("❌ Banco de dados vazio. Faça upload de arquivos primeiro.")
        
        # Gerar consulta SQL
        sql_query = await analyzer.generate_sql_query(question, schema_info, max_results)
        
        # Executar consulta no banco existente
        query_results = st.session_state.db_manager.execute_query(sql_query)
        
        answer = await analyzer.generate_answer(question, sql_query, query_results)
        
        return sql_query, query_results, answer
        
    except Exception as e:
        raise Exception(f"Erro ao processar consulta: {str(e)}")

def _display_query_results(answer: str, sql_query: str, results: list, max_results: int = 100):
    """Exibe os resultados da consulta"""
    
    # Resposta da IA
    st.subheader("🧠 Análise da IA")
    st.markdown(answer)
    
    # Consulta SQL
    with st.expander("🔍 Consulta SQL Executada", expanded=False):
        st.code(sql_query, language="sql")
    
    # Resultados
    st.subheader("📊 Resultados")
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        
        # Verificar se há limitação de resultados
        if len(results) == max_results:
            st.warning(f"⚠️ **Resultado limitado a {max_results} registros**")
            st.info("💡 Para ver mais resultados, refine sua pergunta ou use filtros mais específicos")
        
        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📈 Linhas", len(results))
        with col2:
            st.metric("📋 Colunas", len(df.columns))
        with col3:
            st.metric("💾 Memória", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
        with col4:
            if len(results) == max_results:
                st.metric("🔒 Limite", f"{max_results}/∞")
            else:
                st.metric("🔒 Limite", f"{len(results)}/∞")

    else:
        st.info("ℹ️ Nenhum resultado encontrado.")

def _render_query_history():
    """Renderiza o histórico de consultas"""
    if not st.session_state.get('query_history'):
        return
    
    st.markdown("---")
    st.subheader("📜 Histórico de Consultas")
    
    for i, query in enumerate(reversed(st.session_state.query_history[-10:])):  # Últimas 10
        with st.expander(f"❓ {query['question'][:50]}... ({query['timestamp'].strftime('%H:%M:%S')})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("**🧠 Resposta da IA:**")
                st.markdown(query['answer'])
            
            with col2:
                st.markdown("**📊 Detalhes:**")
                st.write(f"**Resultados:** {len(query['results'])} linhas")
            
            with st.expander("🔍 Consulta SQL", expanded=False):
                st.code(query['sql'], language="sql")
            
            with st.expander("📊 Dados", expanded=False):
                if query['results']:
                    st.dataframe(pd.DataFrame(query['results']))
                else:
                    st.info("Nenhum resultado.")

def _render_suggested_questions():
    """Renderiza sugestões de perguntas"""
    st.markdown("---")
    st.subheader("💡 Sugestões de Perguntas")
    
    suggestions = [
        "Quais são os fornecedores com maior valor de compras?",
        "Existem valores duplicados ou suspeitos nos dados?",
        "Qual a distribuição de valores por período?",
        "Quais documentos têm inconsistências?",
        "Existem padrões anômalos nos dados?",
        "Qual o total de impostos por categoria?",
        "Quais são os maiores valores individuais?",
        "Existem registros com campos obrigatórios vazios?"
    ]
    
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(f"💬 {suggestion}", key=f"suggestion_{i}"):
                st.session_state.suggested_question = suggestion
                st.rerun()
    
    # Aplicar pergunta sugerida se selecionada
    if 'suggested_question' in st.session_state:
        st.text_area(
            "Pergunta sugerida selecionada:",
            value=st.session_state.suggested_question,
            key="suggested_question_input"
        )
        del st.session_state.suggested_question

if __name__ == "__main__":
    main()
