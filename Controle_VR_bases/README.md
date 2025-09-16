# 📚 Documentação do Agente VR/VA Refatorado

## 🎯 Visão Geral

O **Agente VR/VA Refatorado** é um sistema de automação completo para processamento de Vale Refeição (VR) e Vale Alimentação (VA) com arquitetura modular, limpa e profissional.

## 📁 Estrutura da Documentação

- **[README.md](README.md)** - Este arquivo (visão geral)
- **[architecture.md](architecture.md)** - Documentação da arquitetura
- **[api.md](api.md)** - Documentação da API
- **[deployment.md](deployment.md)** - Guia de deploy
- **[troubleshooting.md](troubleshooting.md)** - Solução de problemas

## 🚀 Início Rápido

### 1. Configuração do Ambiente

```bash
# Clonar o repositório
git clone <repository-url>
cd agente-vr-refatorado

# Executar script de configuração
python scripts/setup.py

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações
```

### 2. Executar o Sistema

```bash
# Interface Web (Recomendado)
streamlit run src/web_interface.py

# Interface de Linha de Comando
python src/vr_agent.py
```

## 🏗️ Arquitetura

O sistema utiliza uma arquitetura modular com separação clara de responsabilidades:

```
src/
├── config/          # Configurações centralizadas
├── data_loader/     # Carregamento de dados
├── validator/       # Validação de dados
├── calculator/      # Cálculos de VR/VA
├── ai_service/      # Serviços de IA
├── report_generator/ # Geração de relatórios
├── vr_agent.py      # Classe principal
└── web_interface.py # Interface web
```

## 📊 Funcionalidades

- ✅ **Consolidação de dados** - Reúne múltiplas planilhas em uma base única
- ✅ **Validação automática** - Detecta inconsistências e problemas
- ✅ **Cálculos inteligentes** - Aplica regras de negócio automaticamente
- ✅ **Integração com IA** - Análises e insights usando OpenAI
- ✅ **Relatórios completos** - Gera planilhas prontas para operadora
- ✅ **Interface amigável** - Web e linha de comando

## 🔧 Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENAI_API_KEY` | Chave da API OpenAI (OBRIGATÓRIA) | Obrigatória |
| `VR_DATA_FOLDER` | Pasta de dados de entrada | `data/input` |
| `VR_OUTPUT_FOLDER` | Pasta de saída | `output/reports` |
| `VR_COMPANY_PERCENTAGE` | % da empresa | `0.8` |
| `VR_EMPLOYEE_PERCENTAGE` | % do colaborador | `0.2` |

### Planilhas Obrigatórias

O sistema espera as seguintes planilhas na pasta `data/input/`:

1. **Ativos.xlsx** - Lista de funcionários ativos
2. **Dias_Uteis.xlsx** - Dias úteis por sindicato
3. **Sindicatos.xlsx** - Valores de VR por sindicato

### Planilhas Opcionais

- **Afastados.xlsx** - Funcionários afastados
- **Ferias.xlsx** - Dados de férias
- **Desligados.xlsx** - Funcionários desligados
- **Admissoes.xlsx** - Novas admissões
- **Estagio.xlsx** - Estagiários
- **Aprendiz.xlsx** - Aprendizes
- **Exterior.xlsx** - Funcionários no exterior

## �� Uso

### Interface Web

1. Acesse `http://localhost:8501`
2. Configure sua chave da API OpenAI
3. Digite o comando: `processar setembro 2025`
4. Baixe o arquivo processado

### Interface CLI

```bash
python src/vr_agent.py

# Comandos disponíveis:
# - processar [mês] [ano]
# - consultar [pergunta]
# - sair
```

### Uso Programático

```python
from src.vr_agent import VRAgentRefactored

# Inicializar agente
agente = VRAgentRefactored(openai_api_key="sua_chave")

# Processar VR
resultado = agente.process_vr_complete(2025, 9)

# Consultar IA
resposta = agente.consult_ai("Quantos funcionários foram excluídos?")
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=src

# Executar testes específicos
pytest tests/unit/test_calculator.py
```

## 📦 Deploy

### Desenvolvimento

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements/dev.txt

# Executar em modo desenvolvimento
streamlit run src/web_interface.py --server.port 8501
```

### Produção

```bash
# Instalar dependências de produção
pip install -r requirements/prod.txt

# Executar com Gunicorn
gunicorn src.web_interface:app --bind 0.0.0.0:8000
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/empresa/agente-vr-refatorado/issues)
- **Documentação**: [docs/](docs/)
- **Email**: dev@empresa.com

---

*Desenvolvido com ❤️ seguindo princípios de Clean Code e arquitetura limpa*
