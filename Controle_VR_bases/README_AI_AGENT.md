# 🤖 Agente IA - Automação de Compra VR/VA

Este projeto implementa um agente de inteligência artificial usando OpenAI para **automatizar completamente o processo mensal de compra de VR (Vale Refeição)**, atendendo a todos os requisitos especificados.

## 🎯 Objetivo

Automatizar o processo mensal de compra de VR, garantindo que cada colaborador receba o valor correto, considerando:
- ✅ Ausências e férias
- ✅ Datas de admissão ou desligamento  
- ✅ Calendário de feriados
- ✅ Regras dos acordos coletivos por sindicato
- ✅ Folha ponto

## 🚀 Funcionalidades Implementadas

### ✨ **Base Única Consolidada**
- Reúne e consolida informações de 5 bases separadas em uma única base final
- **Bases integradas:** Ativos, Férias, Desligados, Admissões, Sindicatos, Dias Úteis

### 🚫 **Tratamento de Exclusões Automático**
- **Diretores, estagiários e aprendizes** (por cargo)
- **Afastados em geral** (licença maternidade, etc.)
- **Profissionais no exterior**
- **Estagiários e aprendizes** (por planilha específica)
- Exclusão baseada na matrícula nas planilhas

### 🔍 **Validação e Correção Inteligente**
- **Datas inconsistentes ou "quebradas"**
- **Campos faltantes**
- **Férias mal preenchidas**
- **Feriados estaduais e municipais** corretamente aplicados
- **Validações automáticas** conforme aba "validações"

### 📊 **Cálculo Automatizado do Benefício**
- **Quantidade de dias úteis por colaborador** (considerando sindicato, férias, afastamentos)
- **Regra de desligamento:** 
  - Comunicado até dia 15 → não considerar para pagamento
  - Comunicado após dia 15 → compra proporcional
- **Valor total de VR** por colaborador conforme valor do sindicato
- **Cálculo correto e vigente** baseado nos acordos coletivos

### 📋 **Entrega Final para Operadora**
- **Planilha final** conforme modelo "VR Mensal 05.2025"
- **Valor de VR** a ser concedido
- **Valor a ser pago pela empresa** (80%)
- **Valor a ser descontado do profissional** (20%)
- **Todas as validações** da aba "validações"

## 📋 Pré-requisitos

1. **Python 3.8+**
2. **Chave da API OpenAI** - Obtenha em: https://platform.openai.com/api-keys
3. **Planilhas de dados** na pasta `dados/` com estrutura específica

## 🛠️ Instalação

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Configurar API Key:**
```bash
# Windows
set OPENAI_API_KEY=sua_chave_aqui

# Linux/Mac
export OPENAI_API_KEY=sua_chave_aqui
```

## 🎯 Como Usar

### Interface Web (Recomendado)
```bash
streamlit run vr_ai_web.py
```
Acesse: http://localhost:8501

### Interface de Linha de Comando
```bash
python vr_ai_agent.py
```

### Exemplo de Uso
```bash
python exemplo_uso_ai.py
```

## 📊 Estrutura de Dados

### Planilhas Obrigatórias
- **Ativos.xlsx**: Lista de funcionários ativos (Matricula, Empresa, Cargo, Situação, Sindicato)
- **Dias_Uteis.xlsx**: Mapeamento de dias úteis por sindicato
- **Sindicatos.xlsx**: Informações sobre sindicatos e valores por dia

### Planilhas de Exclusão
- **Afastados.xlsx**: Funcionários afastados (licença maternidade, etc.)
- **Exterior.xlsx**: Funcionários no exterior
- **Estagio.xlsx**: Estagiários
- **Aprendiz.xlsx**: Aprendizes

### Planilhas de Regras
- **Ferias.xlsx**: Dados de férias (Matricula, Dias_Ferias, Dias_Comprados)
- **Desligados.xlsx**: Funcionários desligados (Data_Desligamento, Data_Comunicado_Desligamento)
- **Admissoes.xlsx**: Novas admissões (Data_Admissao)

## 🤖 Exemplos de Uso

### Processamento Completo
```python
from vr_ai_agent import VRAIAgent

# Inicializar agente
agente = VRAIAgent()

# Processar dados completos
resultado = agente.processar_vr_completo(2025, 9)  # Setembro 2025

if resultado["sucesso"]:
    print(f"Arquivo salvo: {resultado['arquivo_saida']}")
    print(f"Funcionários inicial: {resultado['total_funcionarios_inicial']}")
    print(f"Funcionários final: {resultado['total_funcionarios_final']}")
    print(f"Total VR: R$ {resultado['total_vr']:,.2f}")
    print(f"Total Empresa (80%): R$ {resultado['total_empresa']:,.2f}")
    print(f"Total Colaborador (20%): R$ {resultado['total_colaborador']:,.2f}")
```

### Consultas Inteligentes
```python
# Fazer perguntas sobre os dados
resposta = agente.consultar_ia("Quantos funcionários foram excluídos?")
print(resposta)

resposta = agente.consultar_ia("Quais sindicatos têm mais VR?")
print(resposta)

resposta = agente.consultar_ia("Há problemas com datas de desligamento?")
print(resposta)
```

### Interface Web - Comandos
- **Processar**: "processar setembro 2025"
- **Consultar**: "quantos funcionários foram excluídos?"
- **Consultar**: "quais sindicatos têm mais VR?"

## 📈 Saídas Geradas

### Arquivo Excel com Abas:
1. **VR_Mensal**: Dados principais para operadora (conforme modelo)
2. **resumo_sindicato**: Resumo por sindicato
3. **validações**: Validações e problemas detectados
4. **VR_Completo**: Dados completos processados
5. **insights_ia**: Análises e insights da IA
6. **estatisticas**: Métricas gerais do processamento

### Insights da IA:
- **Resumo geral** dos dados encontrados
- **Alertas** sobre inconsistências
- **Sugestões** de melhoria
- **Estatísticas** relevantes
- **Validações** específicas para o processo

## 🔍 Validações Automáticas

A IA detecta automaticamente:
- ✅ **Estrutura correta** das planilhas
- ⚠️ **Inconsistências** nos dados
- 🔍 **Valores fora do padrão**
- 📊 **Tendências anômalas**
- 📅 **Datas inconsistentes**
- 💰 **Cálculos incorretos**
- 🚫 **Exclusões aplicadas**

## 🚨 Tratamento de Erros

O agente trata automaticamente:
- **Planilhas** com estrutura incorreta
- **Dados faltantes** ou inválidos
- **Inconsistências** entre planilhas
- **Problemas de conectividade** com a API
- **Datas mal formatadas**
- **Valores ausentes**

## 💡 Regras de Negócio Implementadas

### Exclusões Automáticas
- **Diretores, estagiários, aprendizes** (por cargo)
- **Afastados** (licença maternidade, etc.)
- **Profissionais no exterior**
- **Estagiários e aprendizes** (por planilha)

### Cálculos por Sindicato
- **Dias úteis** específicos por sindicato
- **Valor por dia** conforme acordo coletivo
- **Regras específicas** de cada sindicato

### Regras de Férias
- **Desconto de dias** de férias
- **Dias comprados** não descontados
- **Cálculo proporcional** quando necessário

### Regras de Desligamento
- **Comunicado até dia 15** → não pagar
- **Comunicado após dia 15** → pagamento proporcional
- **Verificação de elegibilidade** ao benefício

### Regras de Admissão
- **Admissão no meio do mês** → cálculo proporcional
- **Dias trabalhados** considerados

### Percentuais de Custo
- **80% empresa** (custo para empresa)
- **20% colaborador** (desconto do funcionário)

## 🔧 Configurações Avançadas

### Personalizar Percentuais
```python
agente = VRAIAgent()
agente.percentual_empresa = 0.8  # 80% empresa
agente.percentual_colaborador = 0.2  # 20% colaborador
```

### Alterar Pastas
```python
agente.pasta_dados = "meus_dados"
agente.pasta_output = "resultados"
```

### Adicionar Cargos de Exclusão
```python
agente.cargos_exclusao = ["DIRETOR", "ESTAGIÁRIO", "APRENDIZ", "NOVO_CARGO"]
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique se a API Key está configurada
2. Confirme se as planilhas estão na pasta correta
3. Revise os logs de erro no console
4. Teste com dados de exemplo primeiro
5. Execute `python exemplo_uso_ai.py` para diagnóstico

## 🔄 Comparação com Sistema Original

| Recurso | Sistema Original | Agente IA Completo |
|---------|------------------|-------------------|
| Processamento | ✅ Básico | ✅ Completo com todas as regras |
| Validação | ❌ Manual | ✅ Automática com IA |
| Exclusões | ⚠️ Limitadas | ✅ Todas as regras implementadas |
| Cálculos | ⚠️ Básicos | ✅ Completos (férias, desligamentos, etc.) |
| Insights | ❌ Limitados | ✅ Avançados com IA |
| Consultas | ❌ Não disponível | ✅ Linguagem natural |
| Detecção de erros | ⚠️ Básica | ✅ IA avançada |
| Interface | ⚠️ Simples | ✅ Moderna e completa |
| Entrega final | ⚠️ Manual | ✅ Automática para operadora |

## 🎉 Benefícios

- **Automação completa** do processo de compra VR/VA
- **Todas as regras de negócio** implementadas automaticamente
- **Validação inteligente** de dados com IA
- **Exclusões automáticas** conforme especificado
- **Cálculos precisos** considerando todas as variáveis
- **Entrega final** pronta para operadora
- **Insights automáticos** para tomada de decisão
- **Interface amigável** e intuitiva
- **Consultas em linguagem natural**
- **Detecção proativa** de problemas
- **Relatórios enriquecidos** com análises

## 🏆 Atendimento aos Requisitos

✅ **Base única consolidada** - Implementado  
✅ **Tratamento de exclusões** - Implementado  
✅ **Validação e correção** - Implementado  
✅ **Cálculo automatizado** - Implementado  
✅ **Entrega final** - Implementado  
✅ **Observar validações** - Implementado  

---

*Desenvolvido com ❤️ usando OpenAI GPT para automação completa do processo de compra VR/VA*
