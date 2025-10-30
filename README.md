## Sistema Auditor Fiscal

Aplicação web em Python (Streamlit) para auditoria fiscal de Notas Fiscais Eletrônicas (NF-e) com apoio de IA. Permite upload de CSV/XML, validação automática, análise inteligente em linguagem natural e geração de relatórios, com persistência em SQLite.

### Principais Funcionalidades
- **Upload e Processamento**: CSV, XML e ZIP com detecção automática de encoding e separador
- **Validação Automática**: Duplicatas, campos obrigatórios e conferência de totais (v2)
- **Análise com IA**: Geração de SQL e respostas em linguagem natural (CrewAI + OpenAI)
- **Dashboard Executivo**: KPIs e métricas fiscais em tempo real
- **Relatórios**: Visualizações interativas e exportações
- **Persistência**: Banco SQLite local thread-safe

### Estrutura do Projeto (pasta relevante)
```text
auditor_fiscal/
├── app.py                        # Ponto de entrada Streamlit
├── pages/                        # Páginas do Streamlit
│   ├── 1_🏠_Dashboard.py
│   ├── 2_📋_Notas.py
│   ├── 3_📤_Documentos.py
│   ├── 4_🔍_Análise_IA.py
│   ├── 5_📊_Relatórios.py
│   └── 6_⚙️_Configurações.py
├── src/
│   ├── web_interface/
│   │   ├── components/ (metrics.py, sidebar.py)
│   │   └── utils/ (session_manager.py)
│   ├── database/ (db_manager.py)
│   ├── services/ (auditor_service.py)
│   ├── ai_service/ (data_analyzer.py, fiscal_analyzer.py, fiscal_analyzer_v2.py)
│   ├── data_loader/ (file_processor.py, nfe_xml_processor.py)
│   └── config/ (settings.py, config_persistence.py)
└── data/
    ├── input/                    # CSV/XML de entrada
    └── auditor_database.db       # Banco SQLite
```

### Preparação dos Dados
Para gerar o banco de dados, os arquivos CSV devem estar configurados no caminho `auditor_fiscal/data/input/`:
- `202505_NFe_NotaFiscal.csv` - Arquivo com dados das notas fiscais
- `202505_NFe_NotaFiscalItem.csv` - Arquivo com dados dos itens das notas fiscais

**Nota**: O sistema detecta automaticamente esses arquivos na pasta `data/input/` e os carrega no banco de dados na inicialização.

### Como Executar
1) Criar ambiente e instalar dependências
```bash
cd auditor_fiscal
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
```

2) Definir a chave da OpenAI (opcional para recursos de IA)
```bash
export OPENAI_API_KEY="sua_chave_aqui"   # Linux/Mac
# setx OPENAI_API_KEY "sua_chave_aqui"   # Windows (novo terminal)
```

3) Iniciar a aplicação
```bash
streamlit run app.py
```

### Requisitos
- Python 3.8+
- Pacotes principais: `streamlit`, `pandas`, `langchain-openai`, `crewai`, `pysqlite3-binary`, `nest-asyncio`

### Referências de Arquitetura e Fluxos
- Arquitetura detalhada: `ARQUITETURA.md`
- Fluxogramas dos processos: `FLUXOGRAMAS.md`

### Licença
Este projeto está licenciado sob a Licença MIT.
