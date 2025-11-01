# 📊 Fluxogramas - Sistema Auditor Fiscal

Este documento contém fluxogramas detalhados dos principais processos do Sistema Auditor Fiscal, organizados por funcionalidade e fluxo de dados.

---

## 📁 Índice de Fluxogramas

1. [Fluxo Geral do Sistema](#1-fluxo-geral-do-sistema)
2. [Fluxo de Inicialização](#2-fluxo-de-inicialização)
3. [Dashboard - Métricas Fiscais](#3-dashboard---métricas-fiscais)
4. [Listagem de Notas Fiscais](#4-listagem-de-notas-fiscais)
5. [Upload e Processamento de Documentos](#5-upload-e-processamento-de-documentos)
6. [Processamento de XML NFe](#6-processamento-de-xml-nfe)
7. [Análise com IA - Consulta Inteligente](#7-análise-com-ia---consulta-inteligente)
8. [Auditoria Automática de Notas Fiscais](#8-auditoria-automática-de-notas-fiscais)
9. [Validação Automática (FiscalAnalyzer v2)](#9-validação-automática-fiscalanalyzer-v2)
10. [Geração de Métricas Fiscais](#10-geração-de-métricas-fiscais)
11. [Fluxo de Tratamento de Erros](#11-fluxo-de-tratamento-de-erros)
12. [Geração de Relatórios](#12-geração-de-relatórios)

---

## 1. Fluxo Geral do Sistema

```mermaid
flowchart TD
    START([🚀 Início do Sistema Auditor Fiscal]) --> LOAD_CONFIG[📋 Carregar Configurações]
    
    LOAD_CONFIG --> INIT_SESSION[📝 Inicializar SessionManager]
    INIT_SESSION --> CHECK_DB{Banco de<br/>Dados<br/>Existe?}
    
    CHECK_DB -->|Não| CREATE_DB[💾 Criar Novo Banco SQLite]
    CHECK_DB -->|Sim| LOAD_DB[💾 Carregar Banco Existente]
    
    CREATE_DB --> INIT_DB_MANAGER[🗄️ Inicializar DatabaseManager]
    LOAD_DB --> INIT_DB_MANAGER
    
    INIT_DB_MANAGER --> AUTO_LOAD{Auto-carregar<br/>CSV da<br/>pasta input?}
    
    AUTO_LOAD -->|Sim| SCAN_INPUT[📁 Escanear pasta data/input]
    SCAN_INPUT --> HAS_CSV{Arquivos<br/>CSV<br/>Encontrados?}
    
    HAS_CSV -->|Sim| PROCESS_CSV[⚙️ Processar Arquivos CSV]
    PROCESS_CSV --> LOAD_TO_DB[💾 Carregar no Banco]
    HAS_CSV -->|Não| INIT_UI
    
    AUTO_LOAD -->|Não| INIT_UI[🌐 Inicializar Interface Streamlit]
    LOAD_TO_DB --> INIT_UI
    
    INIT_UI --> READY([✅ Sistema Pronto])
    READY --> USER_ACTION{Ação do<br/>Usuário}
    
    USER_ACTION -->|Dashboard| DASHBOARD[🏠 Exibir Dashboard]
    USER_ACTION -->|Notas| NOTES_FLOW[📋 Listar Notas]
    USER_ACTION -->|Upload| UPLOAD_FLOW[📤 Fluxo de Upload]
    USER_ACTION -->|Análise IA| AI_FLOW[🔍 Análise com IA]
    USER_ACTION -->|Relatórios| REPORTS_FLOW[📊 Gerar Relatórios]
    USER_ACTION -->|Config| CONFIG_FLOW[⚙️ Configurações]
    
    DASHBOARD --> USER_ACTION
    UPLOAD_FLOW --> USER_ACTION
    NOTES_FLOW --> USER_ACTION
    AI_FLOW --> USER_ACTION
    REPORTS_FLOW --> USER_ACTION
    CONFIG_FLOW --> USER_ACTION
    
    USER_ACTION -->|Sair| CLEANUP[🧹 Limpeza]
    CLEANUP --> CLOSE_DB[💾 Fechar Banco]
    CLOSE_DB --> END([🛑 Sistema Encerrado])
    
    style START fill:#e8f5e9
    style READY fill:#e8f5e9
    style END fill:#ffebee
```

---

## 2. Fluxo de Inicialização

```mermaid
flowchart TD
    START([🚀 Iniciar Aplicação]) --> PARSE_ARGS[📝 Parsear Argumentos da CLI]
    
    PARSE_ARGS --> LOAD_ENV[🔐 Carregar Variáveis de Ambiente .env]
    LOAD_ENV --> LOAD_SETTINGS[📋 Carregar settings.py]
    
    LOAD_SETTINGS --> VALIDATE_CONFIG{Configurações<br/>Válidas?}
    
    VALIDATE_CONFIG -->|Não| ERROR_CONFIG[❌ Erro: Configuração Inválida]
    ERROR_CONFIG --> END([🛑 Encerrar])
    
    VALIDATE_CONFIG -->|Sim| SETUP_LOGGING[📝 Configurar Sistema de Logging]
    
    SETUP_LOGGING --> INIT_SESSION_MANAGER[📝 Inicializar SessionManager]
    INIT_SESSION_MANAGER --> CHECK_DB_PATH{Arquivo de<br/>Banco<br/>Existe?}
    
    CHECK_DB_PATH -->|Não| CREATE_DB_DIR[📁 Criar Diretório data/]
    CREATE_DB_DIR --> CREATE_DB_FILE[💾 Criar auditor_database.db]
    CREATE_DB_FILE --> INIT_DB_MANAGER
    
    CHECK_DB_PATH -->|Sim| CHECK_DB_HAS_DATA{Banco tem<br/>dados?}
    
    CHECK_DB_HAS_DATA -->|Não| INIT_DB_MANAGER[🗄️ Inicializar DatabaseManager]
    CHECK_DB_HAS_DATA -->|Sim| LOAD_EXISTING_DB[💾 Carregar Banco Existente]
    LOAD_EXISTING_DB --> INIT_DB_MANAGER
    
    INIT_DB_MANAGER --> SCAN_INPUT_DIR[📁 Escanear data/input/]
    SCAN_INPUT_DIR --> FIND_CSV{Arquivos<br/>CSV<br/>Encontrados?}
    
    FIND_CSV -->|Sim| CHECK_CACHE{Arquivos<br/>já<br/>processados?}
    
    CHECK_CACHE -->|Sim| USE_CACHE[✅ Usar Cache do Banco]
    CHECK_CACHE -->|Não| PROCESS_FILES[⚙️ Processar Arquivos CSV]
    
    FIND_CSV -->|Não| SKIP_LOAD[⏭️ Pular Carregamento]
    
    PROCESS_FILES --> LOAD_TO_DB[💾 Carregar no Banco]
    LOAD_TO_DB --> UPDATE_CACHE[💾 Atualizar Cache]
    
    USE_CACHE --> INIT_UI
    UPDATE_CACHE --> INIT_UI[🌐 Inicializar Interface Streamlit]
    SKIP_LOAD --> INIT_UI
    
    INIT_UI --> REGISTER_HANDLERS[🔧 Registrar Event Handlers]
    REGISTER_HANDLERS --> SET_PAGE_CONFIG[📄 Configurar Página Streamlit]
    SET_PAGE_CONFIG --> RENDER_INITIAL[🎨 Renderizar Página Inicial]
    
    RENDER_INITIAL --> READY([✅ Sistema Inicializado e Pronto])
    
    style START fill:#e8f5e9
    style READY fill:#e8f5e9
    style ERROR_CONFIG fill:#ffebee
```

---

## 3. Dashboard - Métricas Fiscais

```mermaid
flowchart TD
    START([🏠 Acessar Dashboard]) --> LOAD_SESSION[📝 Carregar SessionManager]
    
    LOAD_SESSION --> CHECK_DB{Banco de<br/>Dados<br/>Carregado?}
    
    CHECK_DB -->|Não| NO_DATA[⚠️ Nenhum Dado Disponível]
    NO_DATA --> SUGGEST_UPLOAD[💡 Sugerir Upload de Dados]
    SUGGEST_UPLOAD --> END([🛑 Voltar ao Menu])
    
    CHECK_DB -->|Sim| GET_AUDITOR_SERVICE[📊 Obter AuditorService]
    
    GET_AUDITOR_SERVICE --> QUERY_METRICS[📈 Consultar Métricas Fiscais]
    QUERY_METRICS --> CALC_TOTALS[🧮 Calcular Totais]
    
    CALC_TOTALS --> CALC_DOCS[📄 Total de Documentos]
    CALC_DOCS --> CALC_VALUES[💰 Valor Total Fiscalizado]
    CALC_VALUES --> CALC_INCONSISTENCIES[⚠️ Total de Inconsistências]
    CALC_INCONSISTENCIES --> CALC_TIME[⏱️ Tempo de Processamento]
    
    CALC_TIME --> GET_RECENT[📅 Obter Auditorias Recentes]
    GET_RECENT --> GET_ACTIVE[🟢 Obter Auditorias Ativas]
    GET_ACTIVE --> PREPARE_METRICS[📋 Preparar Métricas]
    
    PREPARE_METRICS --> DISPLAY_CARDS[🎴 Exibir Cards de Métricas]
    DISPLAY_CARDS --> DISPLAY_CHARTS[📊 Exibir Gráficos]
    DISPLAY_CHARTS --> DISPLAY_ALERTS[🚨 Exibir Alertas]
    
    DISPLAY_ALERTS --> QUICK_ACTIONS[🚀 Ações Rápidas]
    QUICK_ACTIONS --> NAVIGATE{Usuário<br/>Navega?}
    
    NAVIGATE -->|Upload| UPLOAD_PAGE[📤 Ir para Upload]
    NAVIGATE -->|Análise| ANALYSIS_PAGE[🔍 Ir para Análise]
    NAVIGATE -->|Relatórios| REPORTS_PAGE[📊 Ir para Relatórios]
    NAVIGATE -->|Permanecer| DISPLAY_CARDS
    
    UPLOAD_PAGE --> END
    ANALYSIS_PAGE --> END
    REPORTS_PAGE --> END
    
    style START fill:#e8f5e9
    style NO_DATA fill:#fff3e0
    style END fill:#e8f5e9
```

---

## 4. Listagem de Notas Fiscais

```mermaid
flowchart TD
    START([📋 Acessar Lista de Notas]) --> LOAD_SESSION[📝 Carregar SessionManager]
    
    LOAD_SESSION --> CHECK_DB{Banco de<br/>Dados<br/>Carregado?}
    
    CHECK_DB -->|Não| NO_DATA[⚠️ Nenhum Dado Disponível]
    NO_DATA --> SUGGEST_UPLOAD[💡 Sugerir Upload de Dados]
    SUGGEST_UPLOAD --> END([🛑 Voltar ao Menu])
    
    CHECK_DB -->|Sim| QUERY_NOTES[📄 Consultar Notas Fiscais]
    
    QUERY_NOTES --> GET_NOTES_DATA[📊 Obter Dados das Notas]
    GET_NOTES_DATA --> APPLY_FILTERS{Usuário<br/>Aplicou<br/>Filtros?}
    
    APPLY_FILTERS -->|Sim| FILTER_DATA[🔍 Filtrar Dados]
    APPLY_FILTERS -->|Não| DISPLAY_TABLE
    
    FILTER_DATA --> DISPLAY_TABLE[📋 Exibir Tabela de Notas]
    
    DISPLAY_TABLE --> SHOW_COLUMNS[📊 Mostrar Colunas Principais]
    SHOW_COLUMNS --> ADD_PAGINATION[📄 Adicionar Paginação]
    ADD_PAGINATION --> ADD_SEARCH[🔍 Adicionar Busca]
    
    ADD_SEARCH --> USER_SELECT{Usuário<br/>Seleciona<br/>Nota?}
    
    USER_SELECT -->|Sim| SHOW_DETAILS[📋 Mostrar Detalhes da Nota]
    USER_SELECT -->|Não| WAIT_ACTION[⏳ Aguardar Ação]
    
    SHOW_DETAILS --> SHOW_ITEMS[📦 Mostrar Itens da Nota]
    SHOW_ITEMS --> SHOW_ANALYSIS[🔍 Mostrar Análise de Inconsistências]
    SHOW_ANALYSIS --> ADD_ACTIONS[⚡ Adicionar Ações]
    
    ADD_ACTIONS --> AUDIT_NOTE{Usuário<br/>Solicita<br/>Auditoria?}
    
    AUDIT_NOTE -->|Sim| TRIGGER_AUDIT[🔍 Acionar Auditoria]
    AUDIT_NOTE -->|Não| WAIT_ACTION
    
    TRIGGER_AUDIT --> FISCAL_ANALYZER[🤖 Usar FiscalAnalyzer]
    FISCAL_ANALYZER --> SAVE_RESULT[💾 Salvar Resultado]
    SAVE_RESULT --> UPDATE_DISPLAY[🔄 Atualizar Exibição]
    
    WAIT_ACTION --> USER_SELECT
    UPDATE_DISPLAY --> WAIT_ACTION
    
    style START fill:#e8f5e9
    style NO_DATA fill:#fff3e0
    style END fill:#e8f5e9
    style TRIGGER_AUDIT fill:#e3f2fd
```

---

## 5. Upload e Processamento de Documentos

```mermaid
flowchart TD
    START([👤 Usuário Seleciona Upload]) --> SELECT_TYPE{Tipo de<br/>Upload?}
    
    SELECT_TYPE -->|CSV| CSV_UPLOAD[📄 Upload Arquivo CSV]
    SELECT_TYPE -->|ZIP| ZIP_UPLOAD[📦 Upload Arquivo ZIP]
    SELECT_TYPE -->|XML| XML_UPLOAD[📋 Upload Arquivo XML]
    
    CSV_UPLOAD --> VALIDATE_CSV{CSV<br/>Válido?}
    VALIDATE_CSV -->|Não| ERROR_CSV[❌ Erro: CSV Inválido]
    VALIDATE_CSV -->|Sim| DETECT_ENCODING[🔍 Detectar Encoding Automático]
    
    DETECT_ENCODING --> DETECT_SEP[🔍 Detectar Separador]
    DETECT_SEP --> READ_PANDAS[📖 Ler com Pandas]
    
    ZIP_UPLOAD --> EXTRACT_ZIP[📦 Extrair Arquivos do ZIP]
    EXTRACT_ZIP --> FIND_FILES{Arquivos<br/>Extraídos}
    
    FIND_FILES -->|CSV| CSV_UPLOAD
    FIND_FILES -->|XML| XML_UPLOAD
    FIND_FILES -->|Outros| SKIP_FILE[⏭️ Ignorar Arquivo]
    
    XML_UPLOAD --> VALIDATE_XML{XML<br/>Válido?}
    VALIDATE_XML -->|Não| ERROR_XML[❌ Erro: XML Inválido]
    VALIDATE_XML -->|Sim| PARSE_XML[🔨 Parsear XML com ElementTree]
    
    PARSE_XML --> VALIDATE_SCHEMA{Schema<br/>NFe<br/>Válido?}
    VALIDATE_SCHEMA -->|Não| WARN_SCHEMA[⚠️ Alerta: Schema Inválido]
    VALIDATE_SCHEMA -->|Sim| EXTRACT_NFE[📋 Extrair Dados NFe]
    
    WARN_SCHEMA --> EXTRACT_NFE
    
    READ_PANDAS --> EXTRACT_DATA[📊 Extrair Dados]
    EXTRACT_NFE --> EXTRACT_DATA
    
    EXTRACT_DATA --> SANITIZE[🧹 Sanitizar Nomes de Colunas]
    SANITIZE --> PREPARE_DATA[📋 Preparar Dados para Inserção]
    
    PREPARE_DATA --> GET_TABLE_NAME[📝 Gerar Nome da Tabela]
    GET_TABLE_NAME --> CHECK_TABLE{Tabela<br/>Existe?}
    
    CHECK_TABLE -->|Não| CREATE_TABLE[🏗️ Criar Nova Tabela SQLite]
    CHECK_TABLE -->|Sim| CHECK_DUPLICATE{Forçar<br/>Recarga?}
    
    CHECK_DUPLICATE -->|Sim| TRUNCATE_TABLE[🗑️ Limpar Tabela Existente]
    CHECK_DUPLICATE -->|Não| INSERT_DIRECT
    
    CREATE_TABLE --> ADD_NFE_FIELDS{É Tabela<br/>NFe?}
    TRUNCATE_TABLE --> INSERT_DIRECT[💾 Inserir Dados]
    
    ADD_NFE_FIELDS -->|Sim| ADD_AUDIT_FIELDS[➕ Adicionar Campos de Auditoria]
    ADD_NFE_FIELDS -->|Não| INSERT_DIRECT
    ADD_AUDIT_FIELDS --> INSERT_DIRECT
    
    INSERT_DIRECT --> VALIDATE_INSERT{Inserção<br/>OK?}
    
    VALIDATE_INSERT -->|Erro| HANDLE_ERROR[🔧 Tratar Erro]
    HANDLE_ERROR --> LOG_ERROR[📝 Registrar no Log]
    LOG_ERROR --> ERROR_END
    
    VALIDATE_INSERT -->|OK| COMMIT[💾 Commit Transação]
    COMMIT --> UPDATE_METRICS[📊 Atualizar Métricas]
    UPDATE_METRICS --> UPDATE_SESSION[📝 Atualizar Session State]
    UPDATE_SESSION --> SUCCESS([✅ Upload Concluído])
    
    ERROR_CSV --> ERROR_END[🛑 Retornar ao Usuário]
    ERROR_XML --> ERROR_END
    SKIP_FILE --> EXTRACT_DATA
    
    SUCCESS --> DISPLAY_RESULT[🌐 Exibir Resultado na Interface]
    
    style START fill:#e8f5e9
    style SUCCESS fill:#e8f5e9
    style ERROR_CSV fill:#ffebee
    style ERROR_XML fill:#ffebee
    style ERROR_END fill:#ffebee
    style WARN_SCHEMA fill:#fff3e0
```

---

## 6. Processamento de XML NFe

```mermaid
flowchart TD
    START([📋 Iniciar Processamento XML NFe]) --> VALIDATE_FILE{Arquivo<br/>XML<br/>Válido?}
    
    VALIDATE_FILE -->|Não| ERROR_FILE[❌ Erro: Arquivo Inválido]
    ERROR_FILE --> END([🛑 Encerrar])
    
    VALIDATE_FILE -->|Sim| PARSE_XML[🔨 Parsear XML com ElementTree]
    
    PARSE_XML --> FIND_ROOT{Encontrar<br/>NFe<br/>Root?}
    
    FIND_ROOT -->|Não| ERROR_STRUCTURE[❌ Erro: Estrutura XML Inválida]
    ERROR_STRUCTURE --> END
    
    FIND_ROOT -->|Sim| EXTRACT_INFNFE[📋 Extrair infNFe]
    
    EXTRACT_INFNFE --> EXTRACT_IDE[📝 Extrair Dados de Identificação IDE]
    EXTRACT_IDE --> EXTRACT_EMIT[🏢 Extrair Dados do Emitente]
    EXTRACT_EMIT --> EXTRACT_DEST[👤 Extrair Dados do Destinatário]
    
    EXTRACT_DEST --> EXTRACT_TOTALS[💰 Extrair Totais]
    EXTRACT_TOTALS --> EXTRACT_ITEMS[📦 Extrair Itens]
    
    EXTRACT_ITEMS --> FOR_EACH_ITEM{Para cada<br/>Item}
    
    FOR_EACH_ITEM --> EXTRACT_PROD[📋 Extrair Produto]
    EXTRACT_PROD --> EXTRACT_IMPOSTO[📊 Extrair Impostos]
    EXTRACT_IMPOSTO --> EXTRACT_ICMS[🧾 Extrair ICMS]
    EXTRACT_ICMS --> EXTRACT_IPI[📝 Extrair IPI]
    EXTRACT_IPI --> EXTRACT_PIS[📄 Extrair PIS]
    EXTRACT_PIS --> EXTRACT_COFINS[📑 Extrair COFINS]
    
    EXTRACT_COFINS --> NEXT_ITEM{Próximo<br/>Item?}
    NEXT_ITEM -->|Sim| FOR_EACH_ITEM
    NEXT_ITEM -->|Não| PREPARE_NOTES_TABLE[📊 Preparar Dados Nota Fiscal]
    
    PREPARE_NOTES_TABLE --> PREPARE_ITEMS_TABLE[📦 Preparar Dados Itens]
    
    PREPARE_ITEMS_TABLE --> VALIDATE_DATA{Validar<br/>Dados<br/>Extraídos?}
    
    VALIDATE_DATA -->|Não| HANDLE_MISSING[⚠️ Tratar Dados Faltantes]
    HANDLE_MISSING --> CONTINUE_PROCESS
    
    VALIDATE_DATA -->|Sim| CONTINUE_PROCESS[▶️ Continuar Processamento]
    
    CONTINUE_PROCESS --> MAP_TO_DB[🗺️ Mapear para Estrutura do Banco]
    MAP_TO_DB --> INSERT_NOTES[💾 Inserir na Tabela nfe_notas_fiscais]
    
    INSERT_NOTES --> GET_NOTES_ID[🔑 Obter ID da Nota]
    GET_NOTES_ID --> INSERT_ITEMS[💾 Inserir Itens na Tabela nfe_itens_nota]
    
    INSERT_ITEMS --> COMMIT[💾 Commit Transação]
    COMMIT --> UPDATE_METRICS[📊 Atualizar Métricas]
    UPDATE_METRICS --> SUCCESS([✅ XML Processado com Sucesso])
    
    style START fill:#e8f5e9
    style SUCCESS fill:#e8f5e9
    style ERROR_FILE fill:#ffebee
    style ERROR_STRUCTURE fill:#ffebee
    style HANDLE_MISSING fill:#fff3e0
```

---

## 7. Análise com IA - Consulta Inteligente

```mermaid
sequenceDiagram
    participant U as 👤 Usuário
    participant UI as 🌐 Interface Streamlit
    participant SM as 📝 SessionManager
    participant DA as 🤖 DataAnalyzer
    participant AI as 🧠 CrewAI Agents
    participant DB as 💾 DatabaseManager
    
    U->>UI: Faz pergunta em linguagem natural
    UI->>SM: Verificar sessão e configurações
    SM-->>UI: Status da sessão
    
    UI->>SM: Verificar API key configurada
    SM-->>UI: API key status
    
    alt API não configurada
        UI-->>U: ⚠️ Configure a API Key primeiro
    else API configurada
        UI->>SM: Verificar banco de dados carregado
        SM-->>UI: Status do banco
        
        alt Banco não carregado
            UI-->>U: ⚠️ Carregue dados primeiro
        else Banco carregado
            UI->>DA: analyze_question(pergunta, api_key)
            
            DA->>DB: get_schema_info()
            DB-->>DA: Schema completo do banco
            
            DA->>AI: create_sql_analyst_agent()
            AI-->>DA: SQL Analyst Agent criado
            
            DA->>AI: generate_sql_query(pergunta, schema)
            
            Note over AI: CrewAI Agent analisa pergunta<br/>Gera SQL otimizado para SQLite
            
            AI-->>DA: Consulta SQL gerada
            
            DA->>DA: Validar sintaxe SQL
            
            alt SQL inválido
                DA->>AI: Retry com mais contexto
                AI-->>DA: Nova consulta SQL
            end
            
            DA->>DB: execute_query(sql_query)
            DB-->>DA: Resultados da consulta
            
            alt Resultados vazios
                DA-->>UI: ℹ️ Nenhum resultado encontrado
                UI-->>U: Mensagem informativa
            else Resultados encontrados
                DA->>AI: create_data_analyst_agent()
                AI-->>DA: Data Analyst Agent criado
                
                DA->>AI: format_result(pergunta, sql, resultados)
                
                Note over AI: CrewAI Agent analisa resultados<br/>Formata resposta em linguagem natural
                
                AI-->>DA: Resposta formatada
                
                DA-->>UI: (sql_query, resultados, resposta)
                
                UI->>SM: Salvar consulta no histórico
                SM-->>UI: Histórico atualizado
                
                UI-->>U: Exibir resposta formatada<br/>com dados e visualizações
            end
        end
    end
```

```mermaid
flowchart TD
    START([🔍 Iniciar Análise com IA]) --> CHECK_API{API Key<br/>Configurada?}
    
    CHECK_API -->|Não| ERROR_API[❌ Erro: API não configurada]
    ERROR_API --> END([🛑 Encerrar])
    
    CHECK_API -->|Sim| CHECK_DB{Banco de<br/>Dados<br/>Carregado?}
    
    CHECK_DB -->|Não| ERROR_DB[❌ Erro: Banco não carregado]
    ERROR_DB --> END
    
    CHECK_DB -->|Sim| GET_SCHEMA[📋 Obter Schema do Banco]
    GET_SCHEMA --> INIT_DATA_ANALYZER[🤖 Inicializar DataAnalyzer]
    
    INIT_DATA_ANALYZER --> BUILD_Schema[📝 Construir Descrição do Schema]
    BUILD_Schema --> CREATE_SQL_AGENT[🤖 Criar SQL Analyst Agent]
    
    CREATE_SQL_AGENT --> PREPARE_TASK[📝 Preparar Task para CrewAI]
    PREPARE_TASK --> EXECUTE_CREW[🚀 Executar CrewAI]
    
    EXECUTE_CREW --> GET_SQL[📝 Obter SQL Gerado]
    GET_SQL --> VALIDATE_SQL{SQL<br/>Válido?}
    
    VALIDATE_SQL -->|Não| RETRY[🔄 Retry com Mais Contexto]
    RETRY --> EXECUTE_CREW
    
    VALIDATE_SQL -->|Sim| EXECUTE_QUERY[💾 Executar Query no Banco]
    EXECUTE_QUERY --> GET_RESULTS[📊 Obter Resultados]
    
    GET_RESULTS --> HAS_RESULTS{Tem<br/>Resultados?}
    
    HAS_RESULTS -->|Não| NO_RESULTS[ℹ️ Informar: Sem Resultados]
    NO_RESULTS --> SAVE_HISTORY
    
    HAS_RESULTS -->|Sim| CREATE_DATA_AGENT[🤖 Criar Data Analyst Agent]
    CREATE_DATA_AGENT --> FORMAT_TASK[📝 Preparar Task de Formatação]
    
    FORMAT_TASK --> EXECUTE_FORMAT_CREW[🚀 Executar CrewAI para Formatação]
    EXECUTE_FORMAT_CREW --> FORMATTED_ANSWER[✅ Resposta Formatada]
    
    FORMATTED_ANSWER --> SAVE_HISTORY[💾 Salvar no Histórico]
    NO_RESULTS --> SAVE_HISTORY
    
    SAVE_HISTORY --> DISPLAY_RESULT[🌐 Exibir Resultado]
    DISPLAY_RESULT --> SUCCESS([✅ Análise Concluída])
    
    style START fill:#e8f5e9
    style SUCCESS fill:#e8f5e9
    style ERROR_API fill:#ffebee
    style ERROR_DB fill:#ffebee
    style NO_RESULTS fill:#fff3e0
```

---

## 8. Auditoria Automática de Notas Fiscais

```mermaid
flowchart TD
    START([🔍 Iniciar Auditoria de Nota Fiscal]) --> SELECT_KEY[🔑 Selecionar Chave de Acesso NFe]
    
    SELECT_KEY --> CHECK_FISCAL_ANALYZER{Versão do<br/>Analisador?}
    
    CHECK_FISCAL_ANALYZER -->|v1| FISCAL_V1[🤖 Usar FiscalAnalyzer v1]
    CHECK_FISCAL_ANALYZER -->|v2| FISCAL_V2[⚙️ Usar FiscalAnalyzer v2]
    
    FISCAL_V1 --> AI_ANALYSIS[🤖 Análise Direta com IA]
    AI_ANALYSIS --> GET_AI_RESULT[📊 Obter Resultado da IA]
    GET_AI_RESULT --> SAVE_RESULT
    
    FISCAL_V2 --> AUTO_VALIDATE[✅ Validação Automática SQL]
    
    AUTO_VALIDATE --> VALIDATE_DUP[🔍 Validar Duplicatas]
    VALIDATE_DUP --> VALIDATE_REQUIRED[✅ Validar Campos Obrigatórios]
    VALIDATE_REQUIRED --> VALIDATE_CALC[🧮 Validar Cálculos]
    
    VALIDATE_CALC --> AGGREGATE_VALIDATION[📊 Agregar Resultados]
    AGGREGATE_VALIDATION --> HAS_ISSUES{Problemas<br/>Encontrados?}
    
    HAS_ISSUES -->|Não| NO_ISSUES[✅ Nenhum Problema Detectado]
    NO_ISSUES --> CREATE_CLEAN_RESULT[📝 Criar Resultado Limpo]
    CREATE_CLEAN_RESULT --> SAVE_RESULT
    
    HAS_ISSUES -->|Sim| TRIGGER_AI[🤖 Acionar Análise IA]
    TRIGGER_AI --> AI_DEEP_ANALYSIS[🧠 Análise Profunda com IA]
    AI_DEEP_ANALYSIS --> GET_AI_RESULT
    
    GET_AI_RESULT --> FACT_CHECK[🔍 Fato-verificação dos Resultados IA]
    FACT_CHECK --> VALIDATE_AI{IA<br/>Correto?}
    
    VALIDATE_AI -->|Não| CORRECT_AI[🔧 Corrigir Resultado IA]
    CORRECT_AI --> MERGE_RESULTS
    VALIDATE_AI -->|Sim| MERGE_RESULTS[📊 Combinar Resultados]
    
    MERGE_RESULTS --> PREPARE_RESULT[📋 Preparar Resultado Final]
    PREPARE_RESULT --> SAVE_RESULT[💾 Salvar Resultado]
    
    SAVE_RESULT --> CALCULATE_METRICS[📊 Calcular Métricas]
    CALCULATE_METRICS --> UPDATE_DASHBOARD[📈 Atualizar Dashboard]
    UPDATE_DASHBOARD --> SUCCESS([✅ Auditoria Concluída])
    
    style START fill:#e8f5e9
    style SUCCESS fill:#e8f5e9
    style NO_ISSUES fill:#e8f5e9
    style HAS_ISSUES fill:#fff3e0
```

---

## 9. Validação Automática (FiscalAnalyzer v2)

```mermaid
flowchart TD
    START([✅ Iniciar Validação Automática]) --> INIT_AUTO_VALIDATOR[⚙️ Inicializar AutoValidator]
    
    INIT_AUTO_VALIDATOR --> VALIDATE_DUPLICATES[🔍 Validar Duplicatas]
    
    VALIDATE_DUPLICATES --> CHECK_DUP_SQL[📝 Query SQL: COUNT chave_acesso]
    CHECK_DUP_SQL --> DUP_RESULT[📊 Resultado da Query]
    DUP_RESULT --> HAS_DUP{Duplicatas<br/>Encontradas?}
    
    HAS_DUP -->|Sim| MARK_DUP[⚠️ Marcar como Duplicata]
    HAS_DUP -->|Não| VALIDATE_REQUIRED
    
    MARK_DUP --> VALIDATE_REQUIRED[✅ Validar Campos Obrigatórios]
    
    VALIDATE_REQUIRED --> CHECK_REQUIRED_SQL[📝 Query SQL: SELECT campos obrigatórios]
    CHECK_REQUIRED_SQL --> REQUIRED_RESULT[📊 Resultado da Query]
    REQUIRED_RESULT --> CHECK_NULL{Campos<br/>NULL ou<br/>vazios?}
    
    CHECK_NULL -->|Sim| MARK_MISSING[⚠️ Marcar Campos Faltantes]
    CHECK_NULL -->|Não| VALIDATE_CALCULATIONS
    
    MARK_MISSING --> VALIDATE_CALCULATIONS[🧮 Validar Cálculos Fiscais]
    
    VALIDATE_CALCULATIONS --> CHECK_TOTALS_SQL[📝 Query SQL: Comparar totais]
    CHECK_TOTALS_SQL --> TOTALS_RESULT[📊 Resultado da Comparação]
    TOTALS_RESULT --> CHECK_MATCH{Totais<br/>Batem?}
    
    CHECK_MATCH -->|Não| MARK_CALC_ERROR[⚠️ Marcar Erro de Cálculo]
    CHECK_MATCH -->|Sim| AGGREGATE_RESULTS
    
    MARK_CALC_ERROR --> AGGREGATE_RESULTS[📊 Agregar Todos os Resultados]
    
    AGGREGATE_RESULTS --> COUNT_ISSUES[🔢 Contar Problemas]
    COUNT_ISSUES --> HAS_ISSUES{Tem<br/>Problemas?}
    
    HAS_ISSUES -->|Não| RETURN_CLEAN[✅ Retornar: Validação OK]
    HAS_ISSUES -->|Sim| RETURN_ISSUES[⚠️ Retornar: Lista de Problemas]
    
    RETURN_CLEAN --> END([✅ Validação Concluída])
    RETURN_ISSUES --> END
    
    style START fill:#e8f5e9
    style RETURN_CLEAN fill:#e8f5e9
    style END fill:#e8f5e9
    style MARK_DUP fill:#fff3e0
    style MARK_MISSING fill:#fff3e0
    style MARK_CALC_ERROR fill:#fff3e0
    style RETURN_ISSUES fill:#fff3e0
```

---

## 10. Geração de Métricas Fiscais

```mermaid
flowchart TD
    START([📊 Gerar Métricas Fiscais]) --> GET_AUDIT_SERVICE[📝 Obter AuditorService]
    
    GET_AUDIT_SERVICE --> GET_ALL_RESULTS[💾 Obter Todos os Resultados de Auditoria]
    
    GET_ALL_RESULTS --> QUERY_DB[📝 Query: SELECT * FROM auditor_results]
    QUERY_DB --> RESULTS[📊 Resultados do Banco]
    
    RESULTS --> AGGREGATE_TOTALS[🧮 Agregar Totais]
    
    AGGREGATE_TOTALS --> CALC_DOC_COUNT[🔢 Calcular: Total de Documentos]
    CALC_DOC_COUNT --> CALC_TOTAL_VALUE[💰 Calcular: Valor Total Fiscalizado]
    CALC_TOTAL_VALUE --> CALC_INCONSISTENCIES[⚠️ Calcular: Total de Inconsistências]
    
    CALC_INCONSISTENCIES --> CALC_AVG_TIME[⏱️ Calcular: Tempo Médio de Processamento]
    CALC_AVG_TIME --> CALC_SUCCESS_RATE[📈 Calcular: Taxa de Sucesso]
    
    CALC_SUCCESS_RATE --> GROUP_BY_STATUS[📊 Agrupar por Status]
    GROUP_BY_STATUS --> COUNT_BY_STATUS[🔢 Contar por Status]
    
    COUNT_BY_STATUS --> GROUP_BY_TYPE[📊 Agrupar por Tipo de Análise]
    GROUP_BY_TYPE --> COUNT_BY_TYPE[🔢 Contar por Tipo]
    
    COUNT_BY_TYPE --> GET_RECENT[📅 Obter Auditorias Recentes]
    GET_RECENT --> GET_ACTIVE[🟢 Obter Auditorias Ativas]
    
    GET_ACTIVE --> PREPARE_METRICS[📋 Preparar Dicionário de Métricas]
    
    PREPARE_METRICS --> RETURN_METRICS[📊 Retornar Métricas]
    RETURN_METRICS --> DISPLAY_DASHBOARD[🌐 Exibir no Dashboard]
    
    DISPLAY_DASHBOARD --> SUCCESS([✅ Métricas Geradas])
    
    style START fill:#e8f5e9
    style SUCCESS fill:#e8f5e9
```

---

## 11. Fluxo de Tratamento de Erros

```mermaid
flowchart TD
    ERROR([❌ Erro Detectado]) --> CLASSIFY{Classificar<br/>Tipo de<br/>Erro}
    
    CLASSIFY -->|Validação| VALIDATION_ERROR[🔴 Erro de Validação]
    CLASSIFY -->|Processamento| PROCESS_ERROR[🟠 Erro de Processamento]
    CLASSIFY -->|IA/API| API_ERROR[🟡 Erro de API/IA]
    CLASSIFY -->|Banco| DB_ERROR[🔵 Erro de Banco de Dados]
    CLASSIFY -->|Sistema| SYSTEM_ERROR[⚫ Erro de Sistema]
    
    VALIDATION_ERROR --> LOG_VALIDATION[📝 Log: Erro de Validação]
    LOG_VALIDATION --> NOTIFY_USER_VAL[👤 Notificar: Dados Inválidos]
    NOTIFY_USER_VAL --> RECOVERABLE_VAL{Pode<br/>Recuperar?}
    
    RECOVERABLE_VAL -->|Sim| TRY_CORRECT[🔧 Tentar Corrigir Dados]
    TRY_CORRECT --> VALIDATE_AGAIN{Correção<br/>OK?}
    VALIDATE_AGAIN -->|Sim| CONTINUE_PROC[▶️ Continuar Processamento]
    VALIDATE_AGAIN -->|Não| ROLLBACK_VAL[↩️ Rollback]
    
    RECOVERABLE_VAL -->|Não| ROLLBACK_VAL
    
    PROCESS_ERROR --> LOG_PROCESS[📝 Log: Erro de Processamento]
    LOG_PROCESS --> NOTIFY_USER_PROC[👤 Notificar: Erro no Processamento]
    NOTIFY_USER_PROC --> RETRY_PROC{Retry<br/>Disponível?}
    
    RETRY_PROC -->|Sim| RETRY[🔄 Tentar Novamente]
    RETRY --> MAX_RETRIES{Excedeu<br/>Limite?}
    MAX_RETRIES -->|Não| CONTINUE_PROC
    MAX_RETRIES -->|Sim| ABORT[🛑 Abortar Operação]
    
    RETRY_PROC -->|Não| ABORT
    
    API_ERROR --> LOG_API[📝 Log: Erro de API]
    LOG_API --> CHECK_API_STATUS{API<br/>Disponível?}
    
    CHECK_API_STATUS -->|Sim| RETRY_API[🔄 Retry Chamada API]
    CHECK_API_STATUS -->|Não| FALLBACK[🔄 Usar Modo Sem IA]
    
    RETRY_API --> CONTINUE_PROC
    FALLBACK --> NOTIFY_FALLBACK[👤 Notificar: Modo Limitado]
    NOTIFY_FALLBACK --> CONTINUE_PROC
    
    DB_ERROR --> LOG_DB[📝 Log: Erro de Banco]
    LOG_DB --> CHECK_DB_CONN{Conexão<br/>OK?}
    
    CHECK_DB_CONN -->|Sim| RETRY_DB[🔄 Retry Operação DB]
    CHECK_DB_CONN -->|Não| RECONNECT[🔌 Reconectar ao Banco]
    
    RETRY_DB --> CONTINUE_PROC
    RECONNECT --> RECONNECT_OK{Conexão<br/>Restabelecida?}
    RECONNECT_OK -->|Sim| CONTINUE_PROC
    RECONNECT_OK -->|Não| ABORT
    
    SYSTEM_ERROR --> LOG_SYSTEM[📝 Log: Erro de Sistema]
    LOG_SYSTEM --> NOTIFY_ADMIN[👨‍💼 Notificar Administrador]
    NOTIFY_ADMIN --> ABORT
    
    ROLLBACK_VAL --> CLEANUP[🧹 Limpeza]
    ABORT --> CLEANUP
    CONTINUE_PROC --> SUCCESS[✅ Processamento Continua]
    
    CLEANUP --> END([🛑 Processamento Encerrado])
    
    style ERROR fill:#ffebee
    style END fill:#ffebee
    style ABORT fill:#ff5252
    style VALIDATION_ERROR fill:#ef5350
    style PROCESS_ERROR fill:#ff9800
    style API_ERROR fill:#ffc107
    style DB_ERROR fill:#2196f3
    style SYSTEM_ERROR fill:#424242
    style SUCCESS fill:#4caf50
    style CONTINUE_PROC fill:#e8f5e9
```

---

## 12. Geração de Relatórios

```mermaid
flowchart TD
    START([📊 Gerar Relatório]) --> SELECT_REPORT_TYPE{Tipo de<br/>Relatório?}
    
    SELECT_REPORT_TYPE -->|Dashboard Executivo| EXEC_DASHBOARD[📈 Dashboard Executivo]
    SELECT_REPORT_TYPE -->|Relatório Detalhado| DETAILED_REPORT[📋 Relatório Detalhado]
    SELECT_REPORT_TYPE -->|Análise Estatística| STAT_ANALYSIS[📊 Análise Estatística]
    
    EXEC_DASHBOARD --> GET_METRICS[📊 Obter Métricas Fiscais]
    GET_METRICS --> PREPARE_EXEC_DATA[📝 Preparar Dados Executivos]
    
    PREPARE_EXEC_DATA --> CREATE_CHARTS[📈 Criar Gráficos Plotly]
    CREATE_CHARTS --> CHART_TOTALS[💰 Gráfico: Totais]
    CHART_TOTALS --> CHART_TIMELINE[📅 Gráfico: Timeline]
    CHART_TIMELINE --> CHART_INCONSISTENCIES[⚠️ Gráfico: Inconsistências]
    
    CHART_INCONSISTENCIES --> DISPLAY_EXEC[🌐 Exibir Dashboard]
    
    DETAILED_REPORT --> GET_AUDIT_DATA[📋 Obter Dados de Auditoria]
    GET_AUDIT_DATA --> FILTER_DATA{Aplicar<br/>Filtros?}
    
    FILTER_DATA -->|Sim| APPLY_FILTERS[🔍 Aplicar Filtros]
    APPLY_FILTERS --> PREPARE_DETAILED
    FILTER_DATA -->|Não| PREPARE_DETAILED[📝 Preparar Dados Detalhados]
    
    PREPARE_DETAILED --> CREATE_TABLE[📊 Criar Tabela de Dados]
    CREATE_TABLE --> ADD_SUMMARY[📊 Adicionar Resumo]
    ADD_SUMMARY --> DISPLAY_DETAILED[🌐 Exibir Relatório Detalhado]
    
    STAT_ANALYSIS --> GET_STAT_DATA[📊 Obter Dados Estatísticos]
    GET_STAT_DATA --> CALC_STATS[🧮 Calcular Estatísticas]
    
    CALC_STATS --> CALC_MEAN[📊 Média]
    CALC_MEAN --> CALC_MEDIAN[📊 Mediana]
    CALC_MEDIAN --> CALC_STD[📊 Desvio Padrão]
    CALC_STD --> CALC_DISTRIBUTION[📊 Distribuição]
    
    CALC_DISTRIBUTION --> CREATE_STAT_CHARTS[📈 Criar Gráficos Estatísticos]
    CREATE_STAT_CHARTS --> DISPLAY_STAT[🌐 Exibir Análise Estatística]
    
    DISPLAY_EXEC --> EXPORT_OPTION{Exportar?}
    DISPLAY_DETAILED --> EXPORT_OPTION
    DISPLAY_STAT --> EXPORT_OPTION
    
    EXPORT_OPTION -->|Sim| SELECT_EXPORT_FORMAT{Formato?}
    EXPORT_OPTION -->|Não| SUCCESS
    
    SELECT_EXPORT_FORMAT -->|CSV| EXPORT_CSV[📄 Exportar CSV]
    SELECT_EXPORT_FORMAT -->|Excel| EXPORT_EXCEL[📊 Exportar Excel]
    SELECT_EXPORT_FORMAT -->|PDF| EXPORT_PDF[📑 Exportar PDF]
    
    EXPORT_CSV --> SUCCESS
    EXPORT_EXCEL --> SUCCESS
    EXPORT_PDF --> SUCCESS([✅ Relatório Gerado])
    
    style START fill:#e8f5e9
    style SUCCESS fill:#e8f5e9
```

---

**Última atualização**: 2025-01-27
**Versão da Documentação**: 1.1
**Sistema**: Auditor Fiscal
