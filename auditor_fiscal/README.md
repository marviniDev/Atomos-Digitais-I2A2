# 🔍 Atomize Auditoria Fiscal

Sistema inteligente de auditoria fiscal automatizada desenvolvido em Python (Streamlit) para análise e auditoria de Notas Fiscais Eletrônicas (NF-e) utilizando Inteligência Artificial.

---

## 📋 Descrição do Projeto

O **Atomize Auditoria Fiscal** é uma aplicação web completa que automatiza o processo de auditoria fiscal, utilizando inteligência artificial para detectar irregularidades, validar documentos e gerar insights valiosos sobre dados fiscais. O sistema oferece uma interface intuitiva para upload, processamento, análise e geração de relatórios de dados fiscais.

### 🎯 Principais Objetivos

- **Automatizar** a auditoria fiscal através de IA
- **Detectar** irregularidades e inconsistências automaticamente
- **Validar** documentos fiscais de forma rápida e precisa
- **Gerar** relatórios e métricas fiscais em tempo real
- **Facilitar** a tomada de decisões baseada em dados

---

## 🚀 Funcionalidades Principais

### 📊 Dashboard Executivo
- Métricas fiscais em tempo real
- KPIs e indicadores visuais
- Status das auditorias ativas
- Alertas de irregularidades
- Histórico de análises

### 📋 Gerenciamento de Notas Fiscais
- Listagem completa de notas fiscais carregadas
- Filtros e busca avançada
- Detalhamento de cada nota e seus itens
- Análise de inconsistências por nota

### 📤 Upload e Processamento
- **Arquivos CSV**: Upload individual ou em lote
- **Arquivos ZIP**: Extração automática de múltiplos CSVs
- **Arquivos XML**: Processamento direto de NF-e
- Detecção automática de encoding e separadores
- Validação de estrutura de dados
- Preview dos dados carregados

### 🔍 Análise Inteligente com IA
- **Consultas em linguagem natural**: Faça perguntas sobre seus dados fiscais
- **Geração automática de SQL**: IA converte perguntas em consultas SQL
- **Respostas formatadas**: Resultados explicativos e quantitativos
- **Histórico de consultas**: Todas as análises são salvas
- **Análise fiscal especializada**: Detecção de padrões e irregularidades

### ✅ Validação Automática
- **Duplicatas**: Detecção de notas duplicadas
- **Campos obrigatórios**: Validação de campos necessários
- **Cálculos fiscais**: Verificação de totais e valores
- **Validação híbrida**: Automática (SQL) + IA quando necessário

### 📈 Relatórios e Visualizações
- Dashboard executivo interativo
- Gráficos interativos (Plotly)
- Análise estatística
- Exportação de dados
- Métricas de auditoria

### ⚙️ Configurações
- Configuração de API OpenAI
- Gerenciamento de dados
- Informações do sistema
- Logs e debug

---

## 🛠️ Tecnologias Utilizadas

### Frontend
- **[Streamlit](https://streamlit.io/)** - Framework web para aplicações Python

### Backend
- **[Python 3.8+](https://www.python.org/)** - Linguagem principal
- **[SQLite](https://www.sqlite.org/)** - Banco de dados local thread-safe
- **[Pandas](https://pandas.pydata.org/)** - Processamento de dados

### Inteligência Artificial
- **[OpenAI GPT](https://openai.com/)** - Modelos de linguagem para análise
- **[CrewAI](https://github.com/joaomdmoura/crewAI)** - Sistema multi-agente
- **[LangChain](https://github.com/langchain-ai/langchain)** - Orquestração de LLMs

### Visualização
- **[Plotly](https://plotly.com/)** - Gráficos interativos

### Utilitários
- **python-dotenv** - Variáveis de ambiente
- **pysqlite3-binary** - Driver SQLite otimizado
- **nest-asyncio** - Operações assíncronas

---

## 📦 Estrutura do Projeto

```
auditor_fiscal/
├── app.py                          # Ponto de entrada Streamlit
├── 0_Inicio.py                     # Página inicial de boas-vindas
├── pages/                           # Páginas do Streamlit
│   ├── 1_🏠_Dashboard.py           # Dashboard com métricas fiscais
│   ├── 2_📋_Notas.py               # Listagem de notas fiscais
│   ├── 3_📤_Documentos.py          # Upload de documentos
│   ├── 4_🔍_Análise_IA.py          # Análise com IA
│   ├── 5_📊_Relatórios.py          # Relatórios e visualizações
│   └── 6_⚙️_Configurações.py       # Configurações do sistema
├── src/
│   ├── web_interface/              # Componentes de interface
│   │   ├── components/
│   │   │   ├── metrics.py          # Componentes de métricas
│   │   │   └── sidebar.py          # Menu lateral
│   │   └── utils/
│   │       └── session_manager.py  # Gerenciamento de sessão
│   ├── database/                   # Gerenciamento de banco
│   │   └── db_manager.py           # DatabaseManager SQLite
│   ├── services/                   # Serviços de negócio
│   │   └── auditor_service.py      # Serviço de auditoria fiscal
│   ├── ai_service/                  # Serviços de IA
│   │   ├── data_analyzer.py        # Análise de dados com IA
│   │   ├── fiscal_analyzer.py      # Analisador fiscal v1
│   │   └── fiscal_analyzer_v2.py   # Analisador fiscal v2 (validador automático)
│   ├── data_loader/                # Carregamento de dados
│   │   ├── file_processor.py       # Processamento de arquivos
│   │   ├── nfe_xml_parser.py       # Parser de XML NFe
│   │   └── nfe_xml_processor.py   # Processador completo de XML
│   └── config/                      # Configurações
│       ├── settings.py              # Configurações gerais
│       └── config_persistence.py    # Persistência de configurações
├── data/
│   ├── input/                       # Dados de entrada (CSV/XML)
│   └── auditor_database.db         # Banco SQLite
└── requirements.txt                 # Dependências do projeto
```

---

## 🚀 Como Executar

### 1. Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### 2. Clone e Configure

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/Atomos-Digitais-I2A2.git
cd Atomos-Digitais-I2A2/auditor_fiscal

# Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 3. Preparação dos Dados

Para gerar o banco de dados, os arquivos CSV devem estar configurados no caminho `auditor_fiscal/data/input/`:
- `202505_NFe_NotaFiscal.csv` - Arquivo com dados das notas fiscais
- `202505_NFe_NotaFiscalItem.csv` - Arquivo com dados dos itens das notas fiscais

**Nota**: O sistema detecta automaticamente esses arquivos na pasta `data/input/` e os carrega no banco de dados na inicialização.

### 4. Configurar API OpenAI (Opcional)

Para usar as funcionalidades de análise com IA, configure sua chave da API OpenAI:

```bash
export OPENAI_API_KEY="sua_chave_aqui"   # Linux/Mac
# setx OPENAI_API_KEY "sua_chave_aqui"   # Windows (novo terminal)
```

Ou configure diretamente na página de Configurações da aplicação.

### 5. Execute a Aplicação

```bash
streamlit run app.py
```

A aplicação será aberta automaticamente no seu navegador em `http://localhost:8501`.

---

## 📖 Como Usar

### 1. Primeiros Passos

1. **Configure sua chave da API OpenAI** (opcional, na página de Configurações)
2. **Acesse a página 'Documentos'** para carregar seus dados CSV, ZIP ou XML
3. **Visualize as notas** na página de Notas para análise detalhada
4. **Use a página 'Análise IA'** para fazer consultas inteligentes em linguagem natural
5. **Gere relatórios** na página de Relatórios com visualizações interativas

### 2. Upload de Dados

- **CSV**: Faça upload individual de arquivos CSV
- **ZIP**: Compacte múltiplos CSVs e faça upload do ZIP
- **XML**: Faça upload direto de arquivos XML de NF-e

### 3. Análise com IA

Faça perguntas em linguagem natural como:
- "Quantas notas fiscais temos?"
- "Qual o valor total das notas emitidas em maio?"
- "Quais notas têm inconsistências fiscais?"
- "Mostre as notas com maior valor de ICMS"

### 4. Visualização de Resultados

- Acesse o **Dashboard** para ver métricas gerais
- Use a página de **Notas** para listar e filtrar notas fiscais
- Gere **Relatórios** para análises detalhadas e exportação

---

## 📚 Documentação Adicional

Para mais informações técnicas sobre o projeto, consulte:

- **Arquitetura**: Documentação detalhada da arquitetura do sistema
  - Localização: Ver arquivos `ARQUITETURA.md` na raiz do repositório
- **Fluxogramas**: Diagramas de fluxo dos principais processos
  - Localização: Ver arquivos `FLUXOGRAMAS.md` na raiz do repositório
- **Documentação Técnica**: Documentação específica em `src/docs/`
  - `ARQUITETURA_AUDITOR_FISCAL.md`
  - `FLUXOGRAMAS_AUDITOR_FISCAL.md`

---

## 🔧 Arquitetura do Sistema

O sistema segue uma **Arquitetura em Camadas** bem definida:

- **Camada de Apresentação**: Streamlit Multi-page App
- **Camada de Aplicação**: Orquestradores e Gerenciadores de Sessão
- **Camada de Serviços**: AuditorService, DataAnalyzer, FiscalAnalyzer
- **Camada de Dados**: DatabaseManager com SQLite
- **Camada de Configuração**: Settings e Config Persistence

Para mais detalhes, consulte a documentação de arquitetura completa.

---

## 🎯 Casos de Uso

### Para Empresas
- Auditoria de notas fiscais recebidas
- Análise de conformidade fiscal
- Gestão de riscos tributários
- Detecção de inconsistências

### Para Contadores e Escritórios
- Análise de clientes em lote
- Identificação de inconsistências
- Geração de relatórios executivos
- Consultas inteligentes sobre dados fiscais

### Para Órgãos Fiscais
- Triagem de documentos suspeitos
- Análise de padrões
- Auditoria preventiva

---

## 🤝 Contribuindo

Sinta-se à vontade para explorar, contribuir e sugerir melhorias!

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT**.

---

## 👥 Equipe

**Átomos Digitais I2A2**

Projeto desenvolvido para o desafio I2A2, promovendo inovação e colaboração em análise de dados com IA.

---

> **Atomize Auditoria Fiscal** - Transformando dados fiscais em insights inteligentes. 🔍
