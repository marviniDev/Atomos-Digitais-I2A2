"""
Listagem de Notas Fiscais - Sistema Auditor Fiscal
"""
import streamlit as st
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict
import pandas as pd
from datetime import datetime

# Logger
logger = logging.getLogger(__name__)

# Adicionar o diretório src ao path para imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from web_interface.utils.session_manager import SessionManager
from ai_service.fiscal_analyzer import FiscalAnalyzer
from ai_service.fiscal_analyzer_v2 import FiscalAnalyzerV2
from services.auditor_service import AuditorService

def _count_inconsistencies_from_analysis_result(analysis_result: Dict) -> int:
    """
    Conta inconsistências de um resultado de análise, processando JSON aninhado
    
    Args:
        analysis_result: Resultado da análise fiscal
        
    Returns:
        Número de inconsistências encontradas
    """
    import json
    
    inconsistencies_count = 0
    
    # Obter dados de results
    results_data = analysis_result.get('results', [])
    
    # Se results é uma string JSON, converter para objeto
    if isinstance(results_data, str):
        try:
            results_data = json.loads(results_data)
        except json.JSONDecodeError:
            st.warning("⚠️ Erro ao processar JSON dos resultados")
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
    
    # Fallback: tentar inconsistencies_count direto
    if inconsistencies_count == 0:
        inconsistencies_count = analysis_result.get('inconsistencies_count', 0)
    
    return inconsistencies_count

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Notas Fiscais - Auditor Fiscal",
        page_icon="📋",
        layout="wide"
    )
    
    # Inicializar gerenciador de sessão
    session_manager = SessionManager()
    
    # Header
    st.title("📋 Listagem de Notas Fiscais")
    st.markdown("Selecione as notas fiscais que deseja analisar")
    
    # Verificar se há banco de dados - o auto-inicialização já deve ter carregado
    if not st.session_state.get('db_manager'):
        st.warning("⚠️ Nenhum banco de dados disponível")
        st.info("💡 O banco de dados será inicializado automaticamente quando disponível")
        st.info("💡 Acesse a página 'Documentos' para carregar dados CSV")
        return
    
    # Conteúdo principal
    render_notes_list()

def render_notes_list():
    """Renderiza a lista de notas fiscais com paginação otimizada no banco de dados"""
    
    # Verificar se deve iniciar análise
    if st.session_state.get('start_fiscal_analysis') and st.session_state.get('notes_to_analyze'):
        st.session_state['start_fiscal_analysis'] = False  # Reset flag
        
        # Executar análise
        notes_data = st.session_state['notes_to_analyze'].get('data', [])
        if notes_data:
            perform_fiscal_analysis(notes_data)
            return  # Pausar renderização enquanto análise roda
    
    # Usar especificamente a tabela nfe_notas_fiscais para a listagem principal
    selected_table_name = "nfe_notas_fiscais"
    
    # Verificar se a tabela existe no banco de dados
    tables_info = st.session_state.get('tables_info', {})
    
    if not tables_info:
        st.warning("⚠️ Nenhuma tabela carregada")
        st.info("💡 O banco de dados será inicializado automaticamente se existir")
        st.info("💡 Caso contrário, carregue arquivos CSV ou XML na página 'Documentos'")
        return
    
    # Verificar se a tabela nfe_notas_fiscais existe
    if selected_table_name not in tables_info:
        st.error(f"⚠️ Tabela '{selected_table_name}' não encontrada")
        st.info(f"💡 Tabelas disponíveis: {list(tables_info.keys())}")
        st.info("💡 Carregue arquivos XML na página 'Documentos' para criar as tabelas")
        return
    
    # Obter total de registros sem carregar todos os dados
    count_query = f"SELECT COUNT(*) as total FROM \"{selected_table_name}\""
    count_result = st.session_state.db_manager.execute_query(count_query)
    total_records = count_result[0].get('total', 0) if count_result else 0
    
    if total_records == 0:
        st.warning("⚠️ Nenhum dado encontrado na tabela selecionada")
        return
    
    # Configurar paginação
    page_key = f"notes_page_{selected_table_name}"
    items_per_page_key = f"items_per_page_{selected_table_name}"
    
    # Opções de itens por página
    items_per_page_options = [10, 25, 50, 100]
    
    # Inicializar items_per_page no session_state se não existir
    if items_per_page_key not in st.session_state:
        st.session_state[items_per_page_key] = 10
    
    # Obter o index atual baseado no valor salvo
    current_items_per_page = st.session_state.get(items_per_page_key, 10)
    try:
        current_index = items_per_page_options.index(current_items_per_page)
    except ValueError:
        current_index = 0
        st.session_state[items_per_page_key] = 10
    
    # Verificar se houve mudança no items_per_page ANTES de criar o selectbox
    previous_items_per_page = st.session_state.get(items_per_page_key, 10)
    
    items_per_page = st.selectbox(
        "📄 Itens por página:",
        options=items_per_page_options,
        index=current_index,
        key=items_per_page_key,
        width=200
    )
    
    # Se mudou o items_per_page, resetar para primeira página
    if items_per_page != previous_items_per_page:
        st.session_state[page_key] = 0
    
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
    
    # Calcular paginação
    total_pages = (total_records + items_per_page - 1) // items_per_page if items_per_page > 0 else 1
    current_page = st.session_state[page_key]
    
    # Garantir que current_page não exceda total_pages
    if total_pages > 0 and current_page >= total_pages:
        current_page = max(0, total_pages - 1)
        st.session_state[page_key] = current_page
    
    # Calcular índices para a página atual
    offset = current_page * items_per_page
    
    # Log para debug (pode ser removido depois)
    logger.debug(f"Paginação: current_page={current_page}, items_per_page={items_per_page}, offset={offset}, total_pages={total_pages}")
    
    # Carregar apenas os dados da página atual do banco de dados
    page_query = f"SELECT * FROM \"{selected_table_name}\" LIMIT {items_per_page} OFFSET {offset}"
    page_data = st.session_state.db_manager.execute_query(page_query)

    if not page_data:
        st.warning("⚠️ Nenhum dado encontrado nesta página")
        return
    
    # Converter para DataFrame apenas os dados da página atual
    df_page = pd.DataFrame(page_data)
    
    # Mostrar informações da página
    st.caption(f"Mostrando registros {offset + 1} a {min(offset + items_per_page, total_records)} de {total_records}")
    
    # Mostrar DataFrame
    st.dataframe(
        df_page,
        use_container_width=True,
        hide_index=False,
        height=400
    )

        # Controles de paginação
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1], vertical_alignment="center", gap="large", width="stretch")
        
    with col1:
        if st.button("⏮️ Primeira", disabled=current_page == 0, key="first_page"):
            st.session_state[page_key] = 0
            st.rerun()
    
    with col2:
        if st.button("◀️ Anterior", disabled=current_page == 0, key="prev_page"):
            st.session_state[page_key] = max(0, current_page - 1)
            st.rerun()
    
    with col3:
        st.write(f"**Página {current_page + 1} de {total_pages}**")
        st.caption(f"{total_records} notas no total")
    
    with col4:
        if st.button("Próxima ▶️", disabled=current_page >= total_pages - 1, key="next_page"):
            st.session_state[page_key] = min(total_pages - 1, current_page + 1)
            st.rerun()
    
    with col5:
        if st.button("Última ⏭️", disabled=current_page >= total_pages - 1, key="last_page"):
            st.session_state[page_key] = total_pages - 1
            st.rerun()

    # Busca por chave de acesso
    st.markdown("---")
    st.subheader("🔐 Análise por Chave de Acesso")
    
    st.markdown("**Busque uma nota fiscal específica pela chave de acesso para análise completa com itens**")
    
    
    access_key = st.text_input(
        "Digite a chave de acesso da nota fiscal:",
        placeholder="Ex: 35250412345678000149550010000001231234567890",
        key="access_key_search"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔍 Buscar e Analisar", type="primary", use_container_width=True, key="btn_search_key"):
            if access_key:
                # Guardar na sessão que devemos exibir os resultados
                st.session_state['show_analysis_by_key'] = True
                st.session_state['current_access_key'] = access_key
                st.session_state['current_table_for_search'] = selected_table_name
                st.rerun()
            else:
                st.warning("Digite uma chave de acesso")
    
    # Exibir resultados da busca se existe flag
    if st.session_state.get('show_analysis_by_key', False):
        # Adicionar botão para limpar busca
        col1, col2 = st.columns([10, 1])
        with col2:
            if st.button("❌", key="btn_clear_search"):
                st.session_state['show_analysis_by_key'] = False
                st.rerun()
        
        analyze_by_access_key(
            st.session_state.get('current_access_key', ''), 
            st.session_state.get('current_table_for_search', selected_table_name)
        )
    

def analyze_by_access_key(access_key: str, table_name: str):
    """
    Busca e analisa uma nota fiscal pela chave de acesso junto com seus itens
    
    Args:
        access_key: Chave de acesso da nota fiscal
        table_name: Nome da tabela de notas fiscais
    """
    try:
        db_manager = st.session_state.db_manager
        
        # Buscar colunas da chave de acesso (pode ter diferentes nomes)
        column_key_candidates = ['chave_de_acesso', 'chave_acesso', 'chaveacesso', 'chave_nfe', 'chavenfe', 
                                 'cdchaveacesso', 'cd_chave_acesso', 'chave_fiscal']
        
        # Primeiro, tentar obter o schema da tabela
        schema_info = db_manager.get_table_info(table_name)
        available_columns = [col.lower() for col in schema_info.get('columns', [])]
        
        # Encontrar a coluna correta da chave de acesso
        access_key_column = None
        for candidate in column_key_candidates:
            if candidate in available_columns:
                # Encontrar o nome exato com case correct
                for col in schema_info.get('columns', []):
                    if col.lower() == candidate:
                        access_key_column = col
                        break
                if access_key_column:
                    break
        
        if not access_key_column:
            st.error("❌ Coluna de chave de acesso não encontrada na tabela")
            st.info("💡 Colunas disponíveis: " + ", ".join(schema_info.get('columns', []))[:100])
            return
        
        # Buscar a nota fiscal
        note_query = f'SELECT * FROM "{table_name}" WHERE "{access_key_column}" = ?'
        notes_result = []
        try:
            conn, cursor = db_manager._get_connection()
            cursor.execute(note_query, (access_key,))
            columns = [description[0] for description in cursor.description] if cursor.description else []
            notes_result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            st.error(f"❌ Erro ao buscar nota: {str(e)}")
            return
        
        if not notes_result:
            st.warning(f"⚠️ Nenhuma nota fiscal encontrada com a chave de acesso: {access_key}")
            return
        
        note_data = notes_result[0]
        st.success(f"✅ Nota fiscal encontrada!")
        
        # Exibir dados da nota
        with st.expander("📄 Dados da Nota Fiscal", expanded=True):
            st.json(note_data)
        
        # Buscar itens da nota usando especificamente a tabela nfe_itens_nota
        items_table_name = "nfe_itens_nota"
        items_data = []
        
        # Verificar se existe a tabela de itens
        tables_info = st.session_state.get('tables_info', {})
        
        if items_table_name in tables_info:
            try:
                items_schema = db_manager.get_table_info(items_table_name)
                items_columns = items_schema.get('columns', [])
                
                # Buscar coluna de chave de acesso na tabela de itens
                relation_column = None
                relation_value = access_key
                
                # Procurar coluna de chave de acesso
                for col in items_columns:
                    if col.lower() in ['chave_de_acesso', 'chave_acesso', 'chaveacesso', 'chave_nfe', 'chavenfe', 
                                       'cdchaveacesso', 'cd_chave_acesso', 'chave_fiscal']:
                        relation_column = col
                        logger.info(f"Usando {col} = {access_key} para buscar itens")
                        break
                
                # Se não encontrou coluna de chave, tentar nota_id como fallback
                if not relation_column and 'nota_id' in items_columns:
                    nota_id = note_data.get('id')
                    if nota_id:
                        relation_column = 'nota_id'
                        relation_value = nota_id
                        logger.info(f"Fallback: usando nota_id {nota_id} para buscar itens")
                
                if relation_column and relation_value is not None:
                    items_query = f'SELECT * FROM "{items_table_name}" WHERE "{relation_column}" = ?'
                    try:
                        conn, cursor = db_manager._get_connection()
                        cursor.execute(items_query, (relation_value,))
                        items_columns_desc = [description[0] for description in cursor.description] if cursor.description else []
                        items_data = [dict(zip(items_columns_desc, row)) for row in cursor.fetchall()]
                        
                        if items_data:
                            st.success(f"✅ {len(items_data)} itens encontrados!")
                            logger.info(f"Encontrados {len(items_data)} itens usando {relation_column} = {relation_value}")
                        else:
                            st.warning(f"⚠️ Nenhum item encontrado para esta nota na tabela {items_table_name}")
                            st.info(f"**Query executada:** `{items_query}`")
                            st.info(f"**Valor buscado:** `{relation_value}`")
                            st.info(f"**Coluna usada:** `{relation_column}`")
                            
                            # Debug: mostrar alguns itens da tabela para verificar
                            debug_query = f'SELECT chave_de_acesso, descrição_do_produto_serviço FROM "{items_table_name}" LIMIT 3'
                            try:
                                cursor.execute(debug_query)
                                debug_items = cursor.fetchall()
                                if debug_items:
                                    st.info("**Debug - Primeiros itens na tabela:**")
                                    for item in debug_items:
                                        st.write(f"- Chave: {item[0][:20]}... | Produto: {item[1][:50]}...")
                            except Exception as debug_e:
                                st.write(f"Erro no debug: {debug_e}")
                    except Exception as e:
                        st.warning(f"⚠️ Erro ao buscar itens: {str(e)}")
                        st.write(f"**Query:** `{items_query}` | **Valor:** `{relation_value}`")
                else:
                    st.warning(f"⚠️ Não foi possível encontrar coluna de relacionamento na tabela {items_table_name}")
                    st.info(f"💡 Colunas disponíveis: {', '.join(items_columns[:10])}")
                    st.info(f"💡 nota_id da nota: {note_data.get('id')}")
                    st.info(f"💡 chave_de_acesso: {access_key}")
            except Exception as e:
                st.error(f"❌ Erro ao buscar schema de itens: {str(e)}")
        else:
            st.info(f"ℹ️ Tabela {items_table_name} não encontrada no banco de dados")
        
        # Exibir itens se encontrados
        if items_data:
            with st.expander(f"📦 Itens da Nota ({len(items_data)} itens)", expanded=False):
                df_items = pd.DataFrame(items_data)
                st.dataframe(df_items, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Nenhum item encontrado ou tabela de itens não disponível")
        
        # Preparar dados para análise
        analysis_data = {
            'nota': note_data,
            'itens': items_data,
            'total_itens': len(items_data)
        }
        
        # Preparar para análise com IA
        st.markdown("---")
        st.subheader("🤖 Análise com Inteligência Artificial")
        
        if items_data:
            st.success(f"✅ Pronto para análise: 1 nota fiscal + {len(items_data)} itens")
        else:
            st.warning(f"⚠️ Apenas a nota fiscal será analisada (nenhum item encontrado)")
        
        # Botão para iniciar análise
        if st.button("🚀 Iniciar Análise Completa com IA", type="primary", use_container_width=True, key=f"btn_analysis_{access_key}"):
            # Verificar API key
            api_key = st.session_state.get('api_key')
            if not api_key:
                st.error("❌ Chave da API OpenAI não configurada")
                st.info("💡 Configure sua chave na barra lateral")
            else:
                # Verificar se já existe análise para esta chave de acesso antes de executar
                existing_analysis = None
                try:
                    if st.session_state.get('db_manager'):
                        auditor_service = AuditorService(st.session_state.db_manager)
                        auditor_service.initialize_results_table()
                        
                        # Verificar diretamente por access_key igual à chave da nota
                        conn, cursor = st.session_state.db_manager._get_connection()
                        check_sql = """
                            SELECT * FROM auditor_results 
                            WHERE access_key = ?
                            ORDER BY timestamp DESC
                            LIMIT 1
                        """
                        cursor.execute(check_sql, (access_key,))
                        result = cursor.fetchone()
                        
                        if result:
                            columns = [desc[0] for desc in cursor.description]
                            existing_analysis = dict(zip(columns, result))
                
                except Exception as check_error:
                    logger.warning(f"Erro ao verificar análise existente: {str(check_error)}")
                    existing_analysis = None
                
                if existing_analysis:
                    st.warning(f"⚠️ Já existe uma análise para esta nota fiscal!")
                    st.info(f"📊 Análise realizada em: {existing_analysis.get('timestamp', 'N/A')}")
                    st.info(f"🔑 ID da análise: {existing_analysis.get('id', 'N/A')}")
                    
                    # Mostrar análise existente
                    with st.expander("📊 Ver Análise Existente", expanded=True):
                        st.json(existing_analysis)
                    
                    st.error("❌ Não é permitido realizar nova análise. Cada nota fiscal pode ter apenas uma análise.")
                    return  # Parar execução - não permite criar nova análise
                
                # Executar análise
                with st.spinner("🤖 Realizando análise com Crew AI... Isso pode levar alguns minutos"):
                    try:
                        fiscal_analyzer = FiscalAnalyzer(api_key)
                        
                        # Preparar dados combinados
                        nota = analysis_data['nota']
                        itens = analysis_data.get('itens', [])
                        
                        combined_data = [nota]
                        if itens:
                            combined_data.extend(itens)
                        
                        start_time = datetime.now()
                        
                        # Criar contexto RICO para análise com dados relevantes de auditoria
                        contexto = f"""
============================================
ANÁLISE FISCAL - NOTA FISCAL E ITENS
============================================

CHAVE DE ACESSO: {access_key}

============================================
DADOS DA NOTA FISCAL
============================================
"""
                        # Adicionar dados da nota de forma estruturada
                        for key, value in nota.items():
                            if value and str(value) not in ['nan', '', None]:
                                contexto += f"{key}: {value}\n"
                        
                        # Adicionar análise de itens com estatísticas
                        contexto += f"\n============================================\nITENS DA NOTA FISCAL\n============================================\n"
                        contexto += f"Total de Itens: {len(itens)}\n"
                        
                        if itens:
                            # Extrair informações relevantes dos itens
                            items_df = pd.DataFrame(itens)
                            
                            # Estatísticas de valores
                            value_cols = [col for col in items_df.columns if 'valor' in col.lower() or 'vl' in col.lower() or 'preco' in col.lower()]
                            if value_cols:
                                try:
                                    values = pd.to_numeric(items_df[value_cols[0]].astype(str).str.replace(',', '.'), errors='coerce')
                                    sum_values = values.sum()
                                    avg_value = values.mean()
                                    contexto += f"Valor Total dos Itens: R$ {sum_values:,.2f}\n"
                                    contexto += f"Valor Médio por Item: R$ {avg_value:,.2f}\n"
                                except:
                                    pass
                            
                            # CFOP mais comum
                            cfop_cols = [col for col in items_df.columns if 'cfop' in col.lower()]
                            if cfop_cols:
                                cfop_counts = items_df[cfop_cols[0]].value_counts()
                                contexto += f"\nCFOP mais frequente: {cfop_counts.index[0]} ({cfop_counts.iloc[0]} ocorrências)\n"
                            
                            # NCM mais comum
                            ncm_cols = [col for col in items_df.columns if 'ncm' in col.lower() or 'codigo_ncm' in col.lower()]
                            if ncm_cols:
                                ncm_counts = items_df[ncm_cols[0]].value_counts().head(5)
                                contexto += f"\nPrincipais NCMs:\n"
                                for ncm, count in ncm_counts.items():
                                    contexto += f"  - {ncm}: {count} itens\n"
                            
                            # Quantidades
                            qty_cols = [col for col in items_df.columns if 'quantidade' in col.lower() or 'qtd' in col.lower()]
                            if qty_cols:
                                try:
                                    quantities = pd.to_numeric(items_df[qty_cols[0]].astype(str).str.replace(',', '.'), errors='coerce')
                                    total_qty = quantities.sum()
                                    contexto += f"\nQuantidade Total: {total_qty:,.2f} unidades\n"
                                except:
                                    pass
                            
                            # Descrições dos produtos
                            desc_cols = [col for col in items_df.columns if 'descricao' in col.lower() or 'produto' in col.lower()]
                            if desc_cols:
                                contexto += f"\nPrincipais Produtos/Serviços:\n"
                                for idx, item in enumerate(itens[:5], 1):
                                    desc = item.get(desc_cols[0], 'N/A')
                                    contexto += f"  Item {idx}: {desc[:50]}...\n"
                        
                        contexto += "\n============================================\n"
                        
                        # Criar dados estruturados para análise: NOTA + ITENS como um objeto composto
                        # Passar itens de forma que a IA entenda que são PARTE da nota, não notas separadas
                        
                        # Criar um objeto de dados composto
                        analysis_data_complete = {
                            **nota,  # Todos os campos da nota
                            'itens_da_nota': itens,  # Adicionar itens como campo da nota
                            'total_itens': len(itens) if itens else 0,
                            '_metadata': {
                                'tipo': 'nota_fiscal_com_itens',
                                'numero_de_notas': 1,
                                'numero_de_itens': len(itens) if itens else 0,
                                'instrucao': 'Os itens listados são PARTE desta nota, não são notas duplicadas'
                            }
                        }
                        
                        # Executar análise com objeto composto
                        analysis_result = fiscal_analyzer.analyze_fiscal_notes(
                            notes_data=[analysis_data_complete],  # Objeto completo: nota + itens
                            analysis_type="completa",
                            user_request=f"""Análise completa de auditoria fiscal.

ESTRUTURA DOS DADOS:
- Você está analisando EXATAMENTE 1 NOTA FISCAL
- Esta nota possui {len(itens)} ITENS (produtos/serviços)
- Os itens são PARTE da nota, não notas separadas

IMPORTANTE:
- NÃO mencione "duplicação" ou "múltiplos documentos"
- É normal que todos os itens tenham a mesma chave de acesso da nota
- Analise: a nota fiscal completa (dados da nota + análise dos itens)

DADOS COMPLETOS PARA ANÁLISE:
{contexto}

FOCO DA ANÁLISE:
1. Verificar consistência entre valores da nota e soma dos itens
2. Validar CFOP e NCM dos itens
3. Verificar conformidade fiscal e tributária
4. Identificar inconsistências nos valores e quantidades
5. Detectar possíveis fraudes ou irregularidades
6. Analisar padrões suspeitos nos itens
7. Verificar se há discrepâncias entre nota e itens
"""
                        )
                        
                        end_time = datetime.now()
                        processing_time = (end_time - start_time).total_seconds()
                        
                        # Salvar resultado no banco de dados
                        try:
                            if st.session_state.get('db_manager'):
                                auditor_service = AuditorService(st.session_state.db_manager)
                                auditor_service.initialize_results_table()
                                
                                # Usar a própria chave de acesso da nota como identificador da análise
                                # Isso garante que não haverá análises duplicadas para a mesma nota
                                access_key_result = access_key
                                
                                # Garantir que a chave de acesso da nota esteja no resultado da análise
                                if isinstance(analysis_result, dict):
                                    analysis_result['nota_chave_acesso'] = access_key
                                elif hasattr(analysis_result, '__dict__'):
                                    analysis_result.__dict__['nota_chave_acesso'] = access_key
                                
                                # Extrair valor total
                                total_value = 0.0
                                if isinstance(analysis_result, dict):
                                    total_value = analysis_result.get('total_value', 0.0)
                                elif hasattr(analysis_result, 'total_value'):
                                    total_value = analysis_result.total_value
                                
                                result_id = auditor_service.save_audit_result(
                                    access_key=access_key_result,
                                    document_count=1,
                                    total_value=float(total_value),
                                    processing_time_seconds=processing_time,
                                    analysis_type='crew_ai_completa',
                                    ai_result=analysis_result,
                                    status='completed'
                                )
                                
                                if result_id:
                                    st.success(f"✅ Análise concluída e salva no banco de dados (ID: {result_id})")
                                    st.info(f"🔑 Chave de acesso para consulta: `{access_key_result}`")
                                    st.info(f"⏱️ Tempo de processamento: {processing_time:.2f}s")
                                    logger.info(f"Resultado da análise salvo no banco (ID: {result_id})")
                        except ValueError as ve:
                            # Análise já existe
                            logger.warning(f"Tentativa de criar análise duplicada: {str(ve)}")
                            st.error(f"❌ {str(ve)}")
                            st.info("💡 Não é permitido criar mais de uma análise para a mesma chave de acesso de nota fiscal.")
                        except Exception as db_error:
                            logger.error(f"Erro ao salvar resultado no banco: {str(db_error)}")
                            st.warning(f"⚠️ Resultado não foi salvo no banco: {str(db_error)}")
                        
                    except Exception as e:
                        st.error(f"❌ Erro na análise: {str(e)}")
                        st.exception(e)
    
    except Exception as e:
        st.error(f"❌ Erro ao buscar nota: {str(e)}")
        logger.error(f"Erro na função analyze_by_access_key: {str(e)}")

def perform_fiscal_analysis(notes_data: List[Dict]):
    """
    Executa análise fiscal completa das notas selecionadas
    
    Args:
        notes_data: Lista de notas fiscais para análise
    """
    try:
        # Verificar se há API key configurada
        api_key = st.session_state.get('api_key')
        if not api_key:
            st.error("❌ Chave da API OpenAI não configurada")
            st.info("💡 Configure sua chave na barra lateral")
            return
        
        # Contar total de itens para decidir qual analisador usar
        total_items = 0
        for note in notes_data:
            if 'itens' in note:
                total_items += len(note['itens'])
            elif isinstance(note, dict):
                # Contar campos que parecem ser itens
                item_fields = [k for k in note.keys() if 'item' in k.lower() or 'produto' in k.lower()]
                total_items += len(item_fields)
        
        # Decidir qual analisador usar
        use_v2 = total_items > 10
        
        if use_v2:
            st.info(f"📊 Detectados {total_items} itens - usando FiscalAnalyzerV2 (validação automática)")
            # Criar analisador V2
            fiscal_analyzer = FiscalAnalyzerV2(st.session_state.db_manager, api_key)
            
            # Executar análise com V2
            with st.spinner("🔍 Realizando validação automática... Isso é mais rápido e preciso."):
                start_time = datetime.now()
                
                # Processar cada nota individualmente
                results = []
                for note in notes_data:
                    result = fiscal_analyzer.analyze_with_auto_validation(note)
                    results.append(result)
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # Converter para formato compatível
                analysis_result = {
                    "status": "success",
                    "analysis_type": "fiscal_analyzer_v2",
                    "timestamp_analysis": datetime.now().isoformat(),
                    "processing_time": processing_time,
                    "total_notes": len(notes_data),
                    "total_items": total_items,
                    "total_value": sum(float(note.get('valor_nota_fiscal', '0').replace(',', '.')) for note in notes_data if 'valor_nota_fiscal' in note),
                    "results": results
                }
        else:
            st.info(f"📊 Detectados {total_items} itens - usando FiscalAnalyzer (análise com IA)")
            # Criar analisador tradicional
            fiscal_analyzer = FiscalAnalyzer(api_key)
            
            # Perguntar ao usuário sobre o tipo de análise
            with st.spinner("🤖 Preparando análise com IA..."):
                user_request = st.text_input(
                    "💬 Descreva o que você gostaria de verificar:",
                    placeholder="Ex: Verificar inconsistências fiscais e possíveis fraudes",
                    key="analysis_request"
                )
                
                analysis_type = "inteligente"  # Deixar router decidir
            
            # Executar análise
            with st.spinner("🔍 Realizando análise fiscal com IA... Isso pode levar alguns minutos."):
                start_time = datetime.now()
                
                # Realizar análise
                analysis_result = fiscal_analyzer.analyze_fiscal_notes(
                    notes_data=notes_data,
                    analysis_type=analysis_type,
                    user_request=user_request if user_request else "Análise completa de conformidade fiscal"
                )
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
        
        # Calcular métricas (compatível com ambos os analisadores)
        inconsistencies_count = _count_inconsistencies_from_analysis_result(analysis_result)
        
        # Calcular valor total
        total_value = analysis_result.get('total_value', 0.0)
        if total_value == 0.0:
            # Fallback: calcular a partir dos dados
            total_value = sum(float(note.get('valor_nota_fiscal', '0').replace(',', '.')) for note in notes_data if 'valor_nota_fiscal' in note)
        
        # Salvar resultado no banco de dados
        if st.session_state.get('db_manager'):
            auditor_service = AuditorService(st.session_state.db_manager)
            auditor_service.initialize_results_table()
            
            # Gerar chave de acesso
            access_key = auditor_service.generate_access_key()
            
            # Salvar resultado
            try:
                result_id = auditor_service.save_audit_result(
                    access_key=access_key,
                    document_count=len(notes_data),
                    total_value=float(total_value),
                    processing_time_seconds=processing_time,
                    analysis_type=analysis_result.get('analysis_type', 'fiscal_analyzer_v2' if use_v2 else 'completa'),
                    ai_result=analysis_result,
                    status='completed'
                )
                
                if result_id:
                    st.success(f"✅ Análise concluída e salva no banco de dados (ID: {result_id})")
                    
                    # Armazenar resultado na sessão
                    st.session_state['last_analysis_result'] = {
                        'result_id': result_id,
                        'analysis_result': analysis_result,
                        'access_key': access_key
                    }
                else:
                    st.warning("⚠️ Análise concluída mas não foi possível salvar no banco")
            except ValueError as ve:
                # Análise já existe (improvável com chave gerada, mas possível)
                logger.warning(f"Tentativa de criar análise duplicada: {str(ve)}")
                st.error(f"❌ {str(ve)}")
                st.info("💡 Não é permitido criar mais de uma análise para a mesma chave de acesso.")
            except Exception as e:
                logger.error(f"Erro ao salvar resultado: {str(e)}")
                st.warning(f"⚠️ Análise concluída mas não foi possível salvar no banco: {str(e)}")
        else:
            st.warning("⚠️ Banco de dados não disponível")
            
            # Exibir resultados
            st.success(f"✅ Análise concluída em {processing_time:.2f} segundos")
            
            # Mostrar resumo
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 Notas Analisadas", len(notes_data))
            
            with col2:
                st.metric("🚨 Inconsistências", inconsistencies_count)
            
            with col3:
                st.metric("⏱️ Tempo", f"{processing_time:.2f}s")
            
            with col4:
                if use_v2:
                    # Para V2, mostrar tipo de análise
                    st.metric("🔧 Tipo", "Validação Automática")
                else:
                    # Para analisador tradicional
                    risk_level = analysis_result.get('risk_level', 'INDETERMINADO')
                    st.metric("⚠️ Nível de Risco", risk_level)
            
            # Exibir detalhes da análise
            st.markdown("---")
            st.subheader("📊 Resultados da Análise")
            
            # Mostrar tipo de análise usado
            if use_v2:
                st.info(f"🔧 **Análise realizada com:** FiscalAnalyzerV2 (Validação Automática)")
                st.info(f"📊 **Total de itens processados:** {total_items}")
            else:
                st.info(f"🤖 **Análise realizada com:** FiscalAnalyzer (Inteligência Artificial)")
                st.info(f"📊 **Total de itens processados:** {total_items}")
            
            # Análise por tipo
            if 'results' in analysis_result:
                st.write("**Resultado da Análise:**")
                st.json(analysis_result['results'])
            
            # Recomendações
            if inconsistencies_count > 0:
                st.warning(f"⚠️ Foram encontradas {inconsistencies_count} inconsistências que requerem atenção!")
                st.info("💡 Consulte o relatório completo na página de Relatórios")
            else:
                st.success("✅ Nenhuma inconsistência encontrada!")
            
            # Botão para ver relatório completo
            if st.button("📄 Ver Relatório Completo", type="primary"):
                st.session_state['show_analysis_results'] = True
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Erro na análise fiscal: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()
