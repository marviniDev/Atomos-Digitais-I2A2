"""
Análise Fiscal com CrewAI - Agentes Especializados
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config.settings import config
from ai_service.analysis_schema import create_standardized_analysis_result

logger = logging.getLogger(__name__)

# Schemas Pydantic para output estruturado
class Inconsistencia(BaseModel):
    tipo: str = Field(description="Tipo da inconsistência")
    descricao: str = Field(description="Descrição detalhada da inconsistência")
    severidade: str = Field(description="Severidade: zero|baixa|media|alta|critica")
    evidencia: str = Field(description="Evidência específica dos dados")
    campo_afetado: Optional[str] = Field(None, description="Nome do campo afetado")
    valor_esperado: Optional[str] = Field(None, description="Valor esperado")
    valor_encontrado: Optional[str] = Field(None, description="Valor encontrado")
    recomendacao: str = Field(description="Recomendação específica")

class AuditoriaFisicaOutput(BaseModel):
    inconsistencias: List[Inconsistencia] = Field(description="Lista de inconsistências físicas")
    resumo: str = Field(description="Resumo executivo em uma frase")
    severidade_geral: str = Field(description="Severidade geral: zero|baixa|media|alta|critica")

class AuditoriaTributariaOutput(BaseModel):
    inconsistencias: List[Inconsistencia] = Field(description="Lista de irregularidades tributárias")
    resumo: str = Field(description="Resumo executivo da conformidade tributária")
    severidade_geral: str = Field(description="Severidade geral: zero|baixa|media|alta|critica")

class AnaliseRiscoOutput(BaseModel):
    inconsistencias: List[Inconsistencia] = Field(description="Lista de padrões suspeitos")
    resumo: str = Field(description="Resumo executivo dos riscos identificados")
    severidade_geral: str = Field(description="Severidade geral: zero|baixa|media|alta|critica")

class RelatorioExecutivoOutput(BaseModel):
    inconsistencias: List[Inconsistencia] = Field(description="Lista consolidada de inconsistências")
    resumo: str = Field(description="Resumo executivo consolidado")
    severidade_geral: str = Field(description="Severidade geral: zero|baixa|media|alta|critica")
    recomendacoes: List[str] = Field(description="Lista de recomendações estratégicas")
    plano_acao: List[str] = Field(description="Lista de ações prioritárias")
    impacto_estimado: str = Field(description="Descrição do impacto estimado")

class RouterOutput(BaseModel):
    tipo_analise: str = Field(description="Tipo de análise: fisica|tributaria|risco|completa")

class FiscalAnalyzer:
    """
    Analisador Fiscal com CrewAI - Sistema Multi-Agente
    
    Agentes Especializados:
    - Auditor Físico: Verifica inconsistências físicas
    - Auditor Tributário: Verifica inconsistências tributárias
    - Analista de Risco: Identifica riscos e padrões suspeitos
    - Relator Executivo: Gera relatórios consolidados
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa o analisador fiscal
        
        Args:
            api_key: Chave da API OpenAI
        """
        self.api_key = api_key
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Configurações do LLM
        openai_config = config.get_openai_config()
        self.llm = ChatOpenAI(**openai_config)
        
        # Campos essenciais para análise fiscal (reduz uso de tokens)
        self.ESSENTIAL_NOTE_FIELDS = [
            'chave_de_acesso', 'data_emissão', 'número', 'série', 'modelo',
            'cpf_cnpj_emitente', 'razão_social_emitente', 'uf_emitente', 'município_emitente',
            'cnpj_destinatário', 'nome_destinatário', 'uf_destinatário',
            'valor_nota_fiscal', 'natureza_da_operação', 'destino_da_operação',
            'consumidor_final', 'presença_do_comprador'
        ]
        
        self.ESSENTIAL_ITEM_FIELDS = [
            'número_produto', 'descrição_do_produto_serviço', 'código_ncm_sh',
            'cfop', 'quantidade', 'unidade', 'valor_unitário', 'valor_total',
            'icms_cst', 'icms_aliquota', 'icms_valor', 'ipi_cst', 'ipi_aliquota', 'ipi_valor',
            'pis_cst', 'pis_valor', 'cofins_cst', 'cofins_valor'
        ]
        
        # Tamanho do grupo para processar itens (economiza tokens)
        self.ITEMS_BATCH_SIZE = 10  # Processa 10 itens por vez
        
        # Sistema de memória para análise consolidada
        self.analysis_memory = {
            'note_data': None,
            'items_data': [],
            'total_items_value': 0.0,
            'note_total_value': 0.0,
            'items_count': 0,
            'processed_batches': 0,
            'inconsistencies_found': []
        }
        
        logger.info("FiscalAnalyzer inicializado com sucesso")
    
    def _reset_analysis_memory(self):
        """Reseta a memória de análise para nova nota"""
        self.analysis_memory = {
            'note_data': None,
            'items_data': [],
            'total_items_value': 0.0,
            'note_total_value': 0.0,
            'items_count': 0,
            'processed_batches': 0,
            'inconsistencies_found': []
        }
    
    def _update_analysis_memory(self, note_data: Dict, items_batch: List[Dict] = None):
        """Atualiza a memória de análise com dados da nota e lote de itens"""
        if note_data:
            self.analysis_memory['note_data'] = note_data
            # Extrair valor total da nota
            note_value = note_data.get('valor_nota_fiscal', '0')
            if isinstance(note_value, str):
                note_value = note_value.replace(',', '.')
            self.analysis_memory['note_total_value'] = float(note_value)
        
        if items_batch:
            self.analysis_memory['items_data'].extend(items_batch)
            self.analysis_memory['processed_batches'] += 1
            
            # Calcular total dos itens processados
            batch_total = 0.0
            for item in items_batch:
                item_value = item.get('valor_total', '0')
                if isinstance(item_value, str):
                    item_value = item_value.replace(',', '.')
                try:
                    batch_total += float(item_value)
                except (ValueError, TypeError):
                    continue
            
            self.analysis_memory['total_items_value'] += batch_total
            self.analysis_memory['items_count'] = len(self.analysis_memory['items_data'])
    
    def _get_consolidated_analysis_context(self) -> str:
        """Retorna contexto consolidado para análise com memória"""
        if not self.analysis_memory['note_data']:
            return "Nenhum dado na memória"
        
        context = f"""
ANÁLISE CONSOLIDADA COM MEMÓRIA:

DADOS DA NOTA FISCAL:
{self._prepare_note_summary(self.analysis_memory['note_data'])}

RESUMO CONSOLIDADO DOS ITENS:
- Total de itens processados: {self.analysis_memory['items_count']}
- Lotes processados: {self.analysis_memory['processed_batches']}
- Valor total da nota: R$ {self.analysis_memory['note_total_value']:.2f}
- Soma dos itens processados: R$ {self.analysis_memory['total_items_value']:.2f}
- Diferença: R$ {abs(self.analysis_memory['note_total_value'] - self.analysis_memory['total_items_value']):.2f}

ITENS PROCESSADOS:
"""
        
        # Adicionar resumo dos itens
        for i, item in enumerate(self.analysis_memory['items_data'], 1):
            item_filtered = self._filter_essential_fields(item, self.ESSENTIAL_ITEM_FIELDS)
            context += f"\nItem {i}:"
            for key, value in item_filtered.items():
                context += f"\n  {key}: {value}"
        
        return context
    
    def _detect_value_inconsistencies(self) -> List[Dict]:
        """Detecta inconsistências de valores usando memória consolidada"""
        inconsistencies = []
        
        if self.analysis_memory['note_total_value'] > 0 and self.analysis_memory['total_items_value'] > 0:
            difference = abs(self.analysis_memory['note_total_value'] - self.analysis_memory['total_items_value'])
            
            if difference >= 1.00:  # Tolerância de R$ 1,00
                severity = 'critica' if difference >= 1000 else 'alta' if difference >= 100 else 'media'
                
                inconsistencies.append({
                    'tipo': 'calculos_incorretos',
                    'descricao': f'Inconsistência de cálculo entre valor da nota e soma dos itens',
                    'severidade': severity,
                    'evidencia': f'Nota: R$ {self.analysis_memory["note_total_value"]:.2f} | Itens: R$ {self.analysis_memory["total_items_value"]:.2f}',
                    'campo_afetado': 'valor_nota_fiscal',
                    'valor_esperado': f'R$ {self.analysis_memory["total_items_value"]:.2f}',
                    'valor_encontrado': f'R$ {self.analysis_memory["note_total_value"]:.2f}',
                    'recomendacao': 'Verificar cálculos da nota fiscal e dos itens'
                })
        
        return inconsistencies
    
    def _add_memory_inconsistencies_to_results(self, results: Dict) -> Dict:
        """Adiciona inconsistências detectadas pela memória aos resultados"""
        memory_inconsistencies = self._detect_value_inconsistencies()
        
        if memory_inconsistencies and 'results' in results:
            # Verificar se results['results'] é uma lista ou tupla
            results_data = results['results']
            
            # Se for tupla, converter para lista
            if isinstance(results_data, tuple):
                results_data = list(results_data)
                results['results'] = results_data
            
            # Se for lista, processar normalmente
            if isinstance(results_data, list):
                for result in results_data:
                    # Verificar se result é um dicionário
                    if isinstance(result, dict):
                        if 'inconsistencias' in result:
                            result['inconsistencias'].extend(memory_inconsistencies)
                        else:
                            result['inconsistencias'] = memory_inconsistencies
                            
                        # Atualizar severidade geral se necessário
                        if memory_inconsistencies:
                            max_severity = max([inc.get('severidade', 'zero') for inc in memory_inconsistencies])
                            severity_order = {'zero': 0, 'baixa': 1, 'media': 2, 'alta': 3, 'critica': 4}
                            current_severity = severity_order.get(result.get('severidade_geral', 'zero'), 0)
                            new_severity = severity_order.get(max_severity, 0)
                            
                            if new_severity > current_severity:
                                result['severidade_geral'] = max_severity
            else:
                logger.warning(f"results['results'] não é uma lista ou tupla: {type(results_data)}")
        
        return results
    
    def create_fiscal_agents(self) -> Dict[str, Agent]:
        """Cria agentes especializados em análise fiscal"""
        
        # Agente 1: Auditor Físico - ESPECIALISTA EM VALIDAÇÃO DE DADOS E FORMATOS
        auditor_fisico = Agent(
            role='Auditor Físico - Especialista em Validação de Dados',
            goal='Validar formatos, integridade e consistência dos dados fiscais',
            backstory="""Você é um especialista em validação de dados fiscais com foco em:
            
            RESPONSABILIDADES ESPECÍFICAS:
            1. VALIDAÇÃO DE FORMATOS:
               - CPF/CNPJ: verificar se contém apenas números (11 para CPF, 14 para CNPJ)
               - Campos mascarados com asteriscos (*) são INCONSISTÊNCIAS CRÍTICAS
               - Campos vazios, "nan" ou "None" são inconsistências
               - Datas em formato válido
               
            2. VALIDAÇÃO DE INTEGRIDADE:
               - Valores numéricos válidos
               - Quantidades positivas
               - Campos obrigatórios preenchidos
               
            3. VALIDAÇÃO DE CONSISTÊNCIA:
               - Pequenas diferenças (menores que R$ 1,00) são normalmente por arredondamento
               - Arredondamento é ACEITO pela legislação tributária brasileira
               - Diferenças abaixo de R$ 0,50 geralmente NÃO são problemas significativos
               
            IMPORTANTE: Você NÃO analisa impostos, riscos ou padrões. Apenas valida dados e formatos.
            Se não há problemas de formato/integridade, reporte "Dados em conformidade".""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Agente 2: Auditor Tributário - ESPECIALISTA EM IMPOSTOS E LEGISLAÇÃO
        auditor_tributario = Agent(
            role='Auditor Tributário - Especialista em Impostos',
            goal='Verificar conformidade tributária e cálculos de impostos',
            backstory="""Você é especialista em legislação tributária brasileira com foco em:
            
            RESPONSABILIDADES ESPECÍFICAS:
            1. ANÁLISE DE IMPOSTOS:
               - Verificar cálculos de ICMS, IPI, PIS, COFINS
               - Validar alíquotas aplicadas
               - Verificar bases de cálculo
               
            2. CONFORMIDADE TRIBUTÁRIA:
               - Verificar CFOP correto para a operação
               - Validar NCM dos produtos
               - Verificar regime tributário aplicado
               
            3. LEGISLAÇÃO VIGENTE:
               - Aplicar regras tributárias atuais
               - Identificar possíveis evasões fiscais
               - Verificar benefícios fiscais aplicados
               
            IMPORTANTE: Você NÃO valida formatos de dados ou identifica riscos. 
            Apenas analisa aspectos tributários. Se não há irregularidades tributárias, 
            reporte "Conformidade tributária verificada".""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Agente 3: Analista de Risco - ESPECIALISTA EM DETECÇÃO DE FRAUDES E PADRÕES
        analista_risco = Agent(
            role='Analista de Risco - Especialista em Detecção de Fraudes',
            goal='Identificar padrões suspeitos e avaliar riscos de fraude',
            backstory="""Você é especialista em análise de risco e detecção de fraudes fiscais com foco em:
            
            RESPONSABILIDADES ESPECÍFICAS:
            1. DETECÇÃO DE PADRÕES SUSPEITOS:
               - Transações atípicas ou anômalas
               - Comportamentos inconsistentes
               - Valores ou quantidades suspeitas
               
            2. ANÁLISE DE RISCO:
               - Avaliar probabilidade de fraude
               - Identificar indicadores de irregularidade
               - Priorizar investigações
               
            3. CORRELAÇÃO DE DADOS:
               - Cruzar informações para detectar inconsistências
               - Identificar padrões que fogem do normal
               - Avaliar contexto das transações
               
            IMPORTANTE: Você NÃO valida formatos de dados ou analisa impostos. 
            Apenas identifica riscos e padrões suspeitos. Se não há indicativos de fraude, 
            reporte "Padrões normais identificados".""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Agente 4: Relator Executivo - ESPECIALISTA EM CONSOLIDAÇÃO E COMUNICAÇÃO
        relator_executivo = Agent(
            role='Relator Executivo - Especialista em Consolidação',
            goal='Consolidar análises e gerar relatórios executivos precisos',
            backstory="""Você é especialista em comunicação executiva e consolidação de relatórios com foco em:
            
            RESPONSABILIDADES ESPECÍFICAS:
            1. CONSOLIDAÇÃO DE ANÁLISES:
               - Agregar resultados dos outros agentes
               - Priorizar inconsistências por severidade
               - Eliminar duplicações entre análises
               
            2. COMUNICAÇÃO EXECUTIVA:
               - Transformar dados técnicos em insights acionáveis
               - Criar recomendações estratégicas
               - Elaborar planos de ação prioritários
               
            3. RELATÓRIOS FINAIS:
               - Estruturar informações de forma clara
               - Destacar pontos críticos
               - Fornecer visão consolidada
               
            IMPORTANTE: Você NÃO faz análises técnicas. Apenas consolida e comunica 
            os resultados dos outros agentes. Se não há inconsistências reportadas, 
            confirme "Dados em conformidade".""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        return {
            'auditor_fisico': auditor_fisico,
            'auditor_tributario': auditor_tributario,
            'analista_risco': analista_risco,
            'relator_executivo': relator_executivo
        }
    
    def _create_item_analysis_task(self, agents: Dict[str, Agent], note_summary: str, items_batch: List[Dict], 
                                   batch_number: int, total_batches: int, analysis_type: str) -> Task:
        """Cria uma task específica para análise de um lote de itens com contexto de memória"""
        items_summary = self._prepare_items_summary(items_batch, batch_start=0, batch_size=len(items_batch))
        
        # Contexto de memória para este lote
        memory_context = ""
        if self.analysis_memory['note_total_value'] > 0:
            memory_context = f"""
CONTEXTO DE MEMÓRIA (análise parcial):
- Valor total da nota: R$ {self.analysis_memory['note_total_value']:.2f}
- Itens processados até agora: {self.analysis_memory['items_count']}
- Soma dos itens anteriores: R$ {self.analysis_memory['total_items_value']:.2f}
- Lote atual: {batch_number} de {total_batches}
"""
        
        description = f"""
        IMPORTANTE: Analise APENAS os itens fornecidos abaixo (lote {batch_number} de {total_batches}).
        
        Dados da NOTA FISCAL:
        {note_summary}
        
        {memory_context}
        
        ITENS DO LOTE {batch_number} ({len(items_batch)} itens):
        {items_summary}
        
        Analise rigorosamente estes itens específicos:
        - Verifique valores, quantidades e cálculos
        - Verifique impostos (ICMS, IPI, PIS, COFINS)
        - Verifique NCM, CFOP e conformidade tributária
        - Identifique inconsistências REAIS
        - Considere o contexto de memória para análise parcial
        
        REGRAS CRÍTICAS:
        1. Se não há inconsistências, diga "Itens em conformidade"
        2. Baseie-se APENAS nos dados fornecidos
        3. Diferentes menores que R$ 1,00 são normalmente por arredondamento
        4. Esta é uma análise parcial - inconsistências totais serão detectadas na consolidação
        
        FORMATO DE SAÍDA:
        Retorne JSON válido com inconsistências encontradas OU confirmação de conformidade.
        """
        
        return Task(
            description=description,
            agent=agents['auditor_fisico'],  # Pode usar qualquer agente
            expected_output=f"JSON válido com análise dos itens do lote {batch_number}",
            output_json=AuditoriaFisicaOutput
        )
    
    def create_fiscal_tasks(self, agents: Dict[str, Agent], notes_data: List[Dict], analysis_type: str) -> List[Task]:
        """Cria tarefas de análise fiscal baseadas no tipo de análise, otimizada para processar itens em lotes com memória"""
        
        # Resetar memória para nova análise
        self._reset_analysis_memory()
        
        tasks = []
        
        # Verificar se há itens para processar separadamente
        note = notes_data[0]
        has_itens = 'itens_da_nota' in note or 'itens' in note
        
        if has_itens:
            # Processar itens em lotes separados
            itens = note.get('itens_da_nota') or note.get('itens', [])
            
            if isinstance(itens, list) and len(itens) > 0:
                # Preparar resumo da nota (sem todos os itens)
                note_summary = self._prepare_note_summary(note)
                
                # Dividir itens em lotes
                items_batches = self._split_items_into_batches(itens)
                total_batches = len(items_batches)
                
                # Criar task para análise geral da nota (sem todos os itens)
                note_summary_full = self._prepare_data_summary(notes_data, include_all_items=False)
                
                # Criar tasks principais (nota + resumo)
                data_summary = note_summary_full
                
                # Adicionar tasks principais primeiro
                # Tarefa 1: Auditoria Física (da nota)
                task_auditoria_fisica = Task(
                    description=f"""
                    IMPORTANTE: Analise APENAS os dados reais fornecidos abaixo. Não invente informações.
                    
                    Dados REAIS para análise (NOTA FISCAL + RESUMO DE ITENS):
                    {data_summary}
                    
                    VALIDAÇÃO DE DADOS E FORMATOS (sua especialidade):
                    - Verificar formatos de CPF/CNPJ (apenas números: 11 para CPF, 14 para CNPJ)
                    - Identificar campos mascarados com asteriscos (*) - INCONSISTÊNCIA CRÍTICA
                    - Verificar campos vazios, "nan" ou "None"
                    - Validar formatos de datas
                    - Verificar valores numéricos válidos
                    - Verificar quantidades positivas
                    - Verificar consistência entre valores da nota e soma dos itens
                    
                    REGRAS CRÍTICAS:
                    1. Campos com asteriscos (*) são SEMPRE inconsistências críticas
                    2. CPF/CNPJ deve conter apenas números
                    3. Diferenças menores que R$ 1,00 são normalmente por arredondamento
                    4. Se não há problemas de formato/integridade, diga "Dados em conformidade"
                    
                    FORMATO DE SAÍDA:
                    Retorne JSON válido com inconsistências físicas identificadas ou confirmação de conformidade.
                    """,
                    agent=agents['auditor_fisico'],
                    expected_output="JSON válido com inconsistências físicas identificadas",
                    output_json=AuditoriaFisicaOutput
                )
                tasks.append(task_auditoria_fisica)
                
                # Atualizar memória com dados da nota
                self._update_analysis_memory(note)
                
                # Criar tasks individuais para cada lote de itens
                for batch_idx, items_batch in enumerate(items_batches, 1):
                    # Atualizar memória com lote de itens
                    self._update_analysis_memory(None, items_batch)
                    
                    item_task = self._create_item_analysis_task(
                        agents, note_summary, items_batch, batch_idx, total_batches, analysis_type
                    )
                    tasks.append(item_task)
                    
                # Adicionar tasks tributária e risco (usando resumo otimizado)
                data_summary = note_summary_full
                
                # Tarefa 2: Auditoria Tributária (da nota)
                task_auditoria_tributaria = Task(
                    description=f"""
                    IMPORTANTE: Analise APENAS os dados reais fornecidos abaixo. Não invente informações.
                    
                    Dados REAIS para análise (NOTA FISCAL + RESUMO DE ITENS):
                    {data_summary}
                    
                    ANÁLISE TRIBUTÁRIA (sua especialidade):
                    - Verificar cálculos de ICMS, IPI, PIS, COFINS
                    - Validar alíquotas aplicadas
                    - Verificar bases de cálculo dos impostos
                    - Verificar CFOP correto para a operação
                    - Validar NCM dos produtos
                    - Verificar regime tributário aplicado
                    - Identificar possíveis evasões fiscais
                    
                    REGRAS CRÍTICAS:
                    1. Se não há irregularidades tributárias, diga "Conformidade tributária verificada"
                    2. Baseie-se APENAS nos dados fornecidos
                    3. Foque APENAS em aspectos tributários, não em formatos de dados
                    
                    FORMATO DE SAÍDA:
                    Retorne JSON válido com irregularidades tributárias identificadas ou confirmação de conformidade.
                    """,
                    agent=agents['auditor_tributario'],
                    expected_output="JSON válido com irregularidades tributárias identificadas",
                    output_json=AuditoriaTributariaOutput
                )
                tasks.append(task_auditoria_tributaria)
                
                # Tarefa 3: Análise de Risco (da nota)
                task_analise_risco = Task(
                    description=f"""
                    IMPORTANTE: Analise APENAS os dados reais fornecidos abaixo. Não invente informações.
                    
                    Dados REAIS para análise (NOTA FISCAL + RESUMO DE ITENS):
                    {data_summary}
                    
                    ANÁLISE DE RISCO E DETECÇÃO DE FRAUDES (sua especialidade):
                    - Identificar transações atípicas ou anômalas
                    - Detectar comportamentos inconsistentes
                    - Avaliar valores ou quantidades suspeitas
                    - Correlacionar dados para detectar inconsistências
                    - Identificar padrões que fogem do normal
                    - Avaliar contexto das transações
                    - Priorizar investigações por risco
                    
                    REGRAS CRÍTICAS:
                    1. Se não há indicativos de fraude, diga "Padrões normais identificados"
                    2. Baseie-se APENAS nos dados fornecidos
                    3. Foque APENAS em riscos e padrões, não em formatos ou impostos
                    
                    FORMATO DE SAÍDA:
                    Retorne JSON válido com padrões suspeitos identificados ou confirmação de normalidade.
                    """,
                    agent=agents['analista_risco'],
                    expected_output="JSON válido com padrões suspeitos identificados",
                    output_json=AnaliseRiscoOutput
                )
                tasks.append(task_analise_risco)
                
                # Tarefa 4: Análise Consolidada com Memória (valores e consistência)
                task_analise_consolidada = Task(
                    description=f"""
                    ANÁLISE CONSOLIDADA COM MEMÓRIA (sua especialidade):
                    
                    {self._get_consolidated_analysis_context()}
                    
                    Analise os dados consolidados com memória de todos os lotes processados:
                    - Verifique consistência entre valor total da nota e soma de TODOS os itens
                    - Identifique inconsistências que só aparecem no conjunto completo
                    - Valide cálculos totais considerando todos os itens processados
                    - Detecte padrões que só são visíveis com visão completa
                    
                    REGRAS CRÍTICAS:
                    1. Use a memória consolidada para análise completa
                    2. Foque em inconsistências que só aparecem com todos os dados
                    3. Se não há inconsistências consolidadas, diga "Análise consolidada em conformidade"
                    4. Considere tolerância de R$ 1,00 para arredondamentos
                    
                    FORMATO DE SAÍDA:
                    Retorne JSON válido com inconsistências consolidadas ou confirmação de conformidade.
                    """,
                    agent=agents['auditor_fisico'],
                    expected_output="JSON válido com análise consolidada usando memória",
                    output_json=AuditoriaFisicaOutput
                )
                tasks.append(task_analise_consolidada)
                
                # Tarefa 5: Relatório Executivo (consolidado)
                task_relatorio_executivo = Task(
                    description=f"""
                    IMPORTANTE: Consolide as análises anteriores baseado APENAS nos dados reais.
                    
                    CONSOLIDAÇÃO E RELATÓRIO EXECUTIVO (sua especialidade):
                    - Agregar resultados dos outros agentes (Auditor Físico, Tributário, Risco, Análise Consolidada)
                    - Priorizar inconsistências por severidade
                    - Eliminar duplicações entre análises
                    - Incluir análise consolidada com memória de valores
                    - Criar recomendações estratégicas
                    - Elaborar plano de ação prioritário
                    - Destacar pontos críticos
                    - Fornecer visão consolidada completa
                    
                    REGRAS CRÍTICAS:
                    1. Se não há inconsistências reportadas pelos outros agentes, diga "Dados em conformidade"
                    2. NÃO faça análises técnicas - apenas consolide resultados
                    3. Reporte APENAS o que os outros agentes realmente encontraram
                    
                    FORMATO DE SAÍDA:
                    Retorne JSON válido com relatório executivo consolidado.
                    """,
                    agent=agents['relator_executivo'],
                    expected_output="JSON válido com relatório executivo consolidado",
                    output_json=RelatorioExecutivoOutput
                )
                tasks.append(task_relatorio_executivo)
                
                return tasks
        else:
            # Caso sem itens ou estrutura diferente - usar método tradicional otimizado
            data_summary = self._prepare_data_summary(notes_data, include_all_items=False)
        
        # Tarefa 1: Auditoria Física (método tradicional para notas sem itens)
        task_auditoria_fisica = Task(
            description=f"""
            IMPORTANTE: Analise APENAS os dados reais fornecidos abaixo. Não invente informações.
            
            Dados REAIS para análise:
            {data_summary}
            
            VALIDAÇÃO DE DADOS E FORMATOS (sua especialidade):
            - Verificar formatos de CPF/CNPJ (apenas números: 11 para CPF, 14 para CNPJ)
            - Identificar campos mascarados com asteriscos (*) - INCONSISTÊNCIA CRÍTICA
            - Verificar campos vazios, "nan" ou "None"
            - Validar formatos de datas
            - Verificar valores numéricos válidos
            - Verificar quantidades positivas
            - Verificar consistência entre valores da nota e soma dos itens
            
            REGRAS CRÍTICAS:
            1. Campos com asteriscos (*) são SEMPRE inconsistências críticas
            2. CPF/CNPJ deve conter apenas números
            3. Diferenças menores que R$ 1,00 são normalmente por arredondamento
            4. Se não há problemas de formato/integridade, diga "Dados em conformidade"
            
            FORMATO DE SAÍDA OBRIGATÓRIO:
            Retorne APENAS um JSON válido com a seguinte estrutura:
            {{
                "inconsistencias": [
                    {{
                        "tipo": "arredondamento|duplicacao|campos_ausentes|calculos_incorretos|outros",
                        "descricao": "Descrição detalhada da inconsistência",
                        "severidade": "zero|baixa|media|alta|critica",
                        "evidencia": "Evidência específica dos dados",
                        "campo_afetado": "Nome do campo (se aplicável)",
                        "valor_esperado": "Valor esperado (se aplicável)",
                        "valor_encontrado": "Valor encontrado (se aplicável)",
                        "recomendacao": "Recomendação específica"
                    }}
                ],
                "resumo": "Resumo executivo em uma frase",
                "severidade_geral": "zero|baixa|media|alta|critica"
            }}
            
            Tipo de análise: {analysis_type}
            """,
            agent=agents['auditor_fisico'],
            expected_output="JSON válido com inconsistências físicas identificadas",
            output_json=AuditoriaFisicaOutput
        )
        
        # Tarefa 2: Auditoria Tributária
        task_auditoria_tributaria = Task(
            description=f"""
            IMPORTANTE: Analise APENAS os dados reais fornecidos abaixo. Não invente informações.
            
            Dados REAIS para análise:
            {data_summary}
            
            ANÁLISE TRIBUTÁRIA (sua especialidade):
            - Verificar cálculos de ICMS, IPI, PIS, COFINS
            - Validar alíquotas aplicadas
            - Verificar bases de cálculo dos impostos
            - Verificar CFOP correto para a operação
            - Validar NCM dos produtos
            - Verificar regime tributário aplicado
            - Identificar possíveis evasões fiscais
            
            REGRAS CRÍTICAS:
            1. Se não há irregularidades tributárias, diga "Conformidade tributária verificada"
            2. Baseie-se APENAS nos dados fornecidos
            3. Foque APENAS em aspectos tributários, não em formatos de dados
            
            FORMATO DE SAÍDA OBRIGATÓRIO:
            Retorne APENAS um JSON válido com a seguinte estrutura:
            {{
                "inconsistencias": [
                    {{
                        "tipo": "tributo_incorreto|cfop_incorreto|ncm_incorreto|aliquota_incorreta|outros",
                        "descricao": "Descrição detalhada da irregularidade tributária",
                        "severidade": "zero|baixa|media|alta|critica",
                        "evidencia": "Evidência específica dos dados",
                        "campo_afetado": "Nome do campo tributário",
                        "valor_esperado": "Valor/alíquota esperado",
                        "valor_encontrado": "Valor/alíquota encontrado",
                        "recomendacao": "Recomendação específica"
                    }}
                ],
                "resumo": "Resumo executivo da conformidade tributária",
                "severidade_geral": "zero|baixa|media|alta|critica"
            }}
            
            Tipo de análise: {analysis_type}
            """,
            agent=agents['auditor_tributario'],
            expected_output="JSON válido com irregularidades tributárias identificadas",
            output_json=AuditoriaTributariaOutput
        )
        
        # Tarefa 3: Análise de Risco
        task_analise_risco = Task(
            description=f"""
            IMPORTANTE: Analise APENAS os dados reais fornecidos abaixo. Não invente informações.
            
            Dados REAIS para análise:
            {data_summary}
            
            ANÁLISE DE RISCO E DETECÇÃO DE FRAUDES (sua especialidade):
            - Identificar transações atípicas ou anômalas
            - Detectar comportamentos inconsistentes
            - Avaliar valores ou quantidades suspeitas
            - Correlacionar dados para detectar inconsistências
            - Identificar padrões que fogem do normal
            - Avaliar contexto das transações
            - Priorizar investigações por risco
            
            REGRAS CRÍTICAS:
            1. Se não há indicativos de fraude, diga "Padrões normais identificados"
            2. Baseie-se APENAS nos dados fornecidos
            3. Foque APENAS em riscos e padrões, não em formatos ou impostos
            
            FORMATO DE SAÍDA OBRIGATÓRIO:
            Retorne APENAS um JSON válido com a seguinte estrutura:
            {{
                "inconsistencias": [
                    {{
                        "tipo": "padrao_suspeito|comportamento_anomalo|possivel_fraude|risco_fiscal|outros",
                        "descricao": "Descrição detalhada do padrão suspeito",
                        "severidade": "zero|baixa|media|alta|critica",
                        "evidencia": "Evidência específica dos dados",
                        "campo_afetado": "Campo relacionado ao risco",
                        "valor_esperado": "Comportamento esperado",
                        "valor_encontrado": "Comportamento encontrado",
                        "recomendacao": "Recomendação específica"
                    }}
                ],
                "resumo": "Resumo executivo dos riscos identificados",
                "severidade_geral": "zero|baixa|media|alta|critica"
            }}
            
            Tipo de análise: {analysis_type}
            """,
            agent=agents['analista_risco'],
            expected_output="JSON válido com padrões suspeitos identificados",
            output_json=AnaliseRiscoOutput
        )
        
        # Tarefa 4: Relatório Executivo (consolidado)
        task_relatorio_executivo = Task(
            description=f"""
            IMPORTANTE: Consolide as análises anteriores baseado APENAS nos dados reais.
            
            CONSOLIDAÇÃO E RELATÓRIO EXECUTIVO (sua especialidade):
            - Agregar resultados dos outros agentes (Auditor Físico, Tributário, Risco)
            - Priorizar inconsistências por severidade
            - Eliminar duplicações entre análises
            - Criar recomendações estratégicas
            - Elaborar plano de ação prioritário
            - Destacar pontos críticos
            - Fornecer visão consolidada
            
            REGRAS CRÍTICAS:
            1. Se não há inconsistências reportadas pelos outros agentes, diga "Dados em conformidade"
            2. NÃO faça análises técnicas - apenas consolide resultados
            3. Reporte APENAS o que os outros agentes realmente encontraram
            
            Dados das análises anteriores:
            {data_summary}
            
            FORMATO DE SAÍDA OBRIGATÓRIO:
            Retorne APENAS um JSON válido com a seguinte estrutura:
            {{
                "inconsistencias": [
                    {{
                        "tipo": "tipo_da_inconsistencia",
                        "descricao": "Descrição detalhada consolidada",
                        "severidade": "zero|baixa|media|alta|critica",
                        "evidencia": "Evidência consolidada",
                        "campo_afetado": "Campo afetado",
                        "valor_esperado": "Valor esperado",
                        "valor_encontrado": "Valor encontrado",
                        "recomendacao": "Recomendação consolidada"
                    }}
                ],
                "resumo": "Resumo executivo consolidado",
                "severidade_geral": "zero|baixa|media|alta|critica",
                "recomendacoes": [
                    "Recomendação estratégica 1",
                    "Recomendação estratégica 2"
                ],
                "plano_acao": [
                    "Ação prioritária 1",
                    "Ação prioritária 2"
                ],
                "impacto_estimado": "Descrição do impacto estimado"
            }}
            
            Crie um relatório executivo claro, preciso e baseado nos dados reais analisados.
            """,
            agent=agents['relator_executivo'],
            expected_output="JSON válido com relatório executivo consolidado",
            output_json=RelatorioExecutivoOutput
        )
        
        return [
            task_auditoria_fisica,
            task_auditoria_tributaria,
            task_analise_risco,
            task_relatorio_executivo
        ]
    
    def _filter_essential_fields(self, data: Dict, essential_fields: List[str]) -> Dict:
        """Filtra apenas campos essenciais de um dicionário"""
        filtered = {}
        for field in essential_fields:
            if field in data:
                value = data[field]
                if value and str(value) not in ['nan', '', 'None', None, 'NaN']:
                    filtered[field] = value
        return filtered
    
    def _prepare_note_summary(self, note: Dict) -> str:
        """Prepara resumo otimizado de uma nota fiscal com apenas campos essenciais"""
        note_filtered = self._filter_essential_fields(note, self.ESSENTIAL_NOTE_FIELDS)
        
        summary_lines = []
        for key, value in note_filtered.items():
            summary_lines.append(f"{key}: {value}")
        
        return "\n".join(summary_lines)
    
    def _prepare_items_summary(self, items: List[Dict], batch_start: int = 0, batch_size: int = None) -> str:
        """Prepara resumo otimizado de um lote de itens com apenas campos essenciais"""
        if batch_size is None:
            batch_size = self.ITEMS_BATCH_SIZE
        
        batch_items = items[batch_start:batch_start + batch_size]
        
        summary_lines = []
        for idx, item in enumerate(batch_items, batch_start + 1):
            item_filtered = self._filter_essential_fields(item, self.ESSENTIAL_ITEM_FIELDS)
            summary_lines.append(f"\nItem {idx}:")
            for key, value in item_filtered.items():
                summary_lines.append(f"  {key}: {value}")
        
        return "\n".join(summary_lines)
    
    def _split_items_into_batches(self, items: List[Dict]) -> List[List[Dict]]:
        """Divide itens em lotes para processamento otimizado"""
        batches = []
        for i in range(0, len(items), self.ITEMS_BATCH_SIZE):
            batches.append(items[i:i + self.ITEMS_BATCH_SIZE])
        return batches
    
    def _prepare_data_summary(self, notes_data: List[Dict], include_all_items: bool = False) -> str:
        """
        Prepara resumo otimizado dos dados para análise usando apenas campos essenciais
        
        Args:
            notes_data: Lista de notas fiscais
            include_all_items: Se True, inclui todos os itens. Se False, inclui apenas resumo.
        """
        if not notes_data:
            return "Nenhum dado disponível"
        
        total = len(notes_data)
        note = notes_data[0]
        has_itens = 'itens_da_nota' in note or 'itens' in note
        
        # Criar resumo estruturado otimizado
        summary_lines = [
            f"Total de NOTAS FISCAIS: {total}"
        ]
        
        if has_itens:
            itens = note.get('itens_da_nota') or note.get('itens', [])
            total_itens = len(itens) if isinstance(itens, list) else 0
            summary_lines.append(f"Total de ITENS: {total_itens}")
        
        # ADVERTÊNCIA IMPORTANTE
        if total == 1:
            summary_lines.append("\n⚠️ Há EXATAMENTE 1 NOTA FISCAL nesta análise.")
            if has_itens:
                summary_lines.append("Os itens fazem PARTE desta nota, NÃO são notas separadas.")
        
        # Dados da nota com apenas campos essenciais
        note_summary = self._prepare_note_summary(note)
        summary_lines.append(f"\nNOTA FISCAL - CAMPOS ESSENCIAIS:")
        summary_lines.append(note_summary)
        
        # Processar itens se existirem (apenas resumo se não include_all_items)
        if has_itens:
            itens = note.get('itens_da_nota') or note.get('itens', [])
            if isinstance(itens, list) and len(itens) > 0:
                if include_all_items:
                    # Incluir todos os itens (usado quando processamos em lote)
                    items_summary = self._prepare_items_summary(itens, batch_size=len(itens))
                    summary_lines.append(f"\nITENS DA NOTA ({len(itens)} itens):")
                    summary_lines.append(items_summary)
                else:
                    # Apenas resumo (número de itens e primeiros 3)
                    summary_lines.append(f"\nITENS DA NOTA: {len(itens)} itens encontrados")
                    if len(itens) > 0:
                        items_summary = self._prepare_items_summary(itens[:min(3, len(itens))], batch_size=3)
                        summary_lines.append(f"\nPrimeiros 3 itens:")
                        summary_lines.append(items_summary)
                        if len(itens) > 3:
                            summary_lines.append(f"\n... e mais {len(itens) - 3} itens (serão analisados separadamente)")
        
        return "\n".join(summary_lines)

    def _create_router_agent(self) -> Agent:
        """Cria agente especializado em classificação de tarefas"""
        return Agent(
            role='Router de Tarefas',
            goal='Classificar automaticamente o tipo de análise fiscal necessária',
            backstory="""Você é um especialista em classificação inteligente de tarefas fiscais.
            Você analisa solicitações e identifica qual tipo de análise é mais apropriado:
            - FÍSICA: Para verificar dados, valores, quantidades, datas
            - TRIBUTÁRIA: Para verificar impostos, alíquotas, conformidade fiscal
            - RISCO: Para detectar fraudes, padrões suspeitos, irregularidades
            - COMPLETA: Para análise abrangente de tudo
            Você sempre escolhe o tipo mais específico adequado.""",
            llm=self.llm,
            verbose=False,
            allow_delegation=False
        )
    
    def route_analysis_task(self, notes_data: List[Dict], user_request: str = None) -> str:
        """
        Router de tarefas com IA - identifica o tipo de análise necessária
        
        Returns:
            Tipo de análise identificado: 'fisica', 'tributaria', 'risco', 'completa'
        """
        if not notes_data:
            return 'completa'
        
        if not user_request:
            return 'completa'
        
        try:
            # Criar agente router
            router_agent = self._create_router_agent()
            
            # Criar task de classificação
            routing_task = Task(
                description=f"""
                Analise a seguinte solicitação do usuário e identifique o tipo de análise mais apropriado:
                
                Solicitação: "{user_request}"
                
                Tipos disponíveis:
                - fisica: Para verificar dados, valores, quantidades, datas, campos obrigatórios
                - tributaria: Para verificar impostos (ICMS, IPI, PIS, COFINS), alíquotas, conformidade fiscal
                - risco: Para detectar fraudes, padrões suspeitos, irregularidades, comportamentos anômalos
                - completa: Para análise abrangente que inclui tudo acima
                
                Responda APENAS com uma das opções: fisica, tributaria, risco ou completa
                """,
                agent=router_agent,
                expected_output="Uma única palavra: fisica, tributaria, risco ou completa",
                output_json=RouterOutput
            )
            
            # Executar classificação
            crew = Crew(
                agents=[router_agent],
                tasks=[routing_task],
                process=Process.sequential,
                verbose=False
            )
            
            result = crew.kickoff()
            
            # Extrair tipo de análise do resultado estruturado
            if hasattr(result, 'raw') and hasattr(result.raw, 'tipo_analise'):
                analysis_type = result.raw.tipo_analise.lower().strip()
            elif hasattr(result, 'raw') and isinstance(result.raw, dict):
                analysis_type = result.raw.get('tipo_analise', 'completa').lower().strip()
            else:
                # Fallback para string
                analysis_type = str(result).lower().strip()
            
            # Validar resultado
            valid_types = ['fisica', 'tributaria', 'risco', 'completa']
            if analysis_type in valid_types:
                logger.info(f"Router IA identificou tipo: {analysis_type}")
                return analysis_type
            else:
                logger.warning(f"Tipo inválido do router IA: {analysis_type}, usando 'completa'")
                return 'completa'
                
        except Exception as e:
            logger.error(f"Erro no router IA: {str(e)}, usando análise completa")
            return 'completa'
    
    def analyze_fiscal_notes(
        self,
        notes_data: List[Dict],
        analysis_type: str = "completa",
        user_request: str = None
    ) -> Dict[str, Any]:
        """
        Analisa notas fiscais usando agentes especializados
        
        Args:
            notes_data: Lista de notas fiscais para análise
            analysis_type: Tipo de análise ('fisica', 'tributaria', 'risco', 'completa')
            user_request: Solicitação específica do usuário
        
        Returns:
            Dicionário com resultados da análise
        """
        try:
            # Router de tarefas com IA
            if not analysis_type or analysis_type == "auto" or analysis_type == "inteligente":
                analysis_type = self.route_analysis_task(notes_data, user_request)
                logger.info(f"Router IA escolheu tipo de análise: {analysis_type}")
            
            logger.info(f"Iniciando análise fiscal - Tipo: {analysis_type}")
            
            # Criar agentes
            agents = self.create_fiscal_agents()
            
            # Criar tarefas
            tasks = self.create_fiscal_tasks(agents, notes_data, analysis_type)
            
            # Criar e executar crew
            crew = Crew(
                agents=list(agents.values()),
                tasks=tasks,
                process=Process.sequential,
                verbose=True
            )
            
            # Executar análise
            start_time = datetime.now()
            crew_results = crew.kickoff()
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            # Calcular valores totais
            total_items = 0
            total_value = 0.0
            
            # Verificar se notes_data tem itens
            if notes_data and isinstance(notes_data[0], dict):
                if 'itens_da_nota' in notes_data[0]:
                    total_items = len(notes_data[0].get('itens_da_nota', []))
                # Tentar extrair valor total
                for note in notes_data:
                    if 'valor_nota_fiscal' in note:
                        val_str = str(note['valor_nota_fiscal'])
                        try:
                            total_value += float(val_str.replace(',', '.'))
                        except:
                            pass
            
            # Processar resultados (compatibilidade retroativa)
            analysis_result = {
                "status": "success",
                "analysis_type": analysis_type,
                "timestamp_analysis": datetime.now().isoformat(),
                "processing_time": processing_time,
                "total_notes": len(notes_data) if notes_data else 0,
                "total_items": total_items,
                "total_value": total_value,
                "results": crew_results
            }
            
            # Adicionar inconsistências detectadas pela memória
            analysis_result = self._add_memory_inconsistencies_to_results(analysis_result)
            
            # Log de informações de memória para debug
            if self.analysis_memory['note_total_value'] > 0:
                logger.info(f"Memória de análise - Nota: R$ {self.analysis_memory['note_total_value']:.2f}, "
                          f"Itens: R$ {self.analysis_memory['total_items_value']:.2f}, "
                          f"Diferença: R$ {abs(self.analysis_memory['note_total_value'] - self.analysis_memory['total_items_value']):.2f}")

            print(crew_results)

            return analysis_result
            
        except Exception as e:
            logger.error(f"Erro na análise fiscal: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "analysis_type": analysis_type,
                "total_notes": len(notes_data) if notes_data else 0
            }

