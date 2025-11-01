"""
Esquema JSON padronizado para resultados de análise fiscal
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class SeverityLevel(str, Enum):
    """Níveis de severidade de inconsistências"""
    ZERO = "zero"
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class InconsistencyType(str, Enum):
    """Tipos de inconsistências fiscais"""
    DUPLICACAO = "duplicacao"
    CAMPOS_AUSENTES = "campos_ausentes"
    CALCULOS_INCORRETOS = "calculos_incorretos"
    ARREDONDAMENTO = "arredondamento"
    DATAS_INVALIDAS = "datas_invalidas"
    CFOP_INCORRETO = "cfop_incorreto"
    NCM_INCORRETO = "ncm_incorreto"
    TRIBUTO_INCORRETO = "tributo_incorreto"
    OUTROS = "outros"

@dataclass
class Inconsistency:
    """Representa uma inconsistência encontrada"""
    tipo: str
    descricao: str
    severidade: str
    evidencia: Optional[str] = None
    campo_afetado: Optional[str] = None
    valor_esperado: Optional[str] = None
    valor_encontrado: Optional[str] = None
    recomendacao: Optional[str] = None

@dataclass
class AnalysisSummary:
    """Resumo executivo da análise"""
    total_notas: int
    total_itens: int
    valor_total: float
    qtd_inconsistencias: int
    risco_fiscal: str
    conclusao: str

@dataclass
class AnalysisResult:
    """Resultado completo de uma análise fiscal em formato padronizado"""
    # Metadados
    timestamp: str
    status: str
    analysis_type: str
    processing_time: float
    
    # Resumo
    summary: AnalysisSummary
    
    # Inconsistências
    inconsistencies: List[Dict[str, Any]]
    
    # Recomendações
    recomendacoes: List[str]
    
    # Plano de ação
    plano_acao: List[str]
    
    # Impacto
    impacto_estimado: Optional[str] = None


def create_standardized_analysis_result(
    raw_result: Any,
    total_notes: int,
    total_items: int = 0,
    total_value: float = 0.0,
    processing_time: float = 0.0
) -> Dict[str, Any]:
    """
    Cria resultado de análise em formato JSON padronizado
    
    Args:
        raw_result: Resultado bruto da IA (pode ser JSON dos agentes ou texto)
        total_notes: Total de notas analisadas
        total_items: Total de itens analisados
        total_value: Valor total fiscalizado
        processing_time: Tempo de processamento
        
    Returns:
        Dict com resultado padronizado
    """
    # Converter resultado bruto para string
    if hasattr(raw_result, 'raw'):
        texto_analise = str(raw_result.raw)
    elif hasattr(raw_result, 'output'):
        texto_analise = str(raw_result.output)
    else:
        texto_analise = str(raw_result)
    
    # Tentar extrair JSON dos agentes primeiro
    agent_results = _extract_agent_json_results(texto_analise)
    
    if agent_results:
        # Usar resultados JSON dos agentes
        inconsistencies = _consolidate_agent_inconsistencies(agent_results)
        recomendacoes = _consolidate_agent_recommendations(agent_results)
        plano_acao = _consolidate_agent_action_plans(agent_results)
        severidade_geral = _determine_overall_severity_from_agents(agent_results)
        conclusao = _extract_conclusion_from_agents(agent_results)
    else:
        # Fallback: extrair do texto tradicional
        inconsistencies = _extract_inconsistencies(texto_analise)
        recomendacoes = _extract_recommendations(texto_analise)
        plano_acao = _extract_action_plan(texto_analise)
        severidade_geral = _determine_overall_severity(inconsistencies)
        conclusao = _extract_conclusion(texto_analise)
    
    # Criar resumo
    summary = {
        'total_notas': total_notes,
        'total_itens': total_items,
        'valor_total': total_value,
        'inconsistencias_encontradas': len(inconsistencies),
        'severidade_geral': severidade_geral,
        'conclusao': conclusao
    }
    
    # Estrutura JSON padronizada
    result = {
        'timestamp': datetime.now().isoformat(),
        'status': 'completed',
        'analysis_type': 'completa',
        'processing_time': processing_time,
        'summary': summary,
        'inconsistencies': inconsistencies,
        'recomendacoes': recomendacoes,
        'plano_acao': plano_acao
    }
    
    return result


def _extract_agent_json_results(texto: str) -> List[Dict[str, Any]]:
    """Extrai resultados JSON dos agentes do texto"""
    import json
    import re
    
    agent_results = []
    
    # Buscar por blocos JSON no texto - padrão mais flexível
    json_patterns = [
        r'\{[^{}]*"inconsistencias"[^{}]*\}',  # Padrão original
        r'\{[^{}]*"resumo"[^{}]*\}',           # Padrão com resumo
        r'\{[^{}]*"severidade_geral"[^{}]*\}', # Padrão com severidade
    ]
    
    for pattern in json_patterns:
        json_matches = re.findall(pattern, texto, re.DOTALL)
        
        for match in json_matches:
            try:
                # Tentar limpar e parsear JSON
                cleaned = match.strip()
                if cleaned.startswith('{') and cleaned.endswith('}'):
                    parsed = json.loads(cleaned)
                    # Aceitar qualquer JSON que tenha pelo menos um campo esperado
                    if any(field in parsed for field in ['inconsistencias', 'resumo', 'severidade_geral']):
                        agent_results.append(parsed)
            except json.JSONDecodeError:
                continue
    
    return agent_results


def _consolidate_agent_inconsistencies(agent_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Consolida inconsistências de todos os agentes"""
    all_inconsistencies = []
    
    for result in agent_results:
        if 'inconsistencias' in result:
            for inc in result['inconsistencias']:
                # Garantir que tem todos os campos necessários
                standardized_inc = {
                    'tipo': inc.get('tipo', 'outros'),
                    'descricao': inc.get('descricao', ''),
                    'severidade': inc.get('severidade', 'zero'),
                    'evidencia': inc.get('evidencia', ''),
                    'campo_afetado': inc.get('campo_afetado'),
                    'valor_esperado': inc.get('valor_esperado'),
                    'valor_encontrado': inc.get('valor_encontrado'),
                    'recomendacao': inc.get('recomendacao')
                }
                all_inconsistencies.append(standardized_inc)
    
    return all_inconsistencies


def _consolidate_agent_recommendations(agent_results: List[Dict[str, Any]]) -> List[str]:
    """Consolida recomendações de todos os agentes"""
    all_recommendations = []
    
    for result in agent_results:
        if 'recomendacoes' in result and isinstance(result['recomendacoes'], list):
            all_recommendations.extend(result['recomendacoes'])
    
    # Remover duplicatas mantendo ordem
    seen = set()
    unique_recommendations = []
    for rec in all_recommendations:
        if rec not in seen:
            seen.add(rec)
            unique_recommendations.append(rec)
    
    return unique_recommendations


def _consolidate_agent_action_plans(agent_results: List[Dict[str, Any]]) -> List[str]:
    """Consolida planos de ação de todos os agentes"""
    all_actions = []
    
    for result in agent_results:
        if 'plano_acao' in result and isinstance(result['plano_acao'], list):
            all_actions.extend(result['plano_acao'])
    
    # Remover duplicatas mantendo ordem
    seen = set()
    unique_actions = []
    for action in all_actions:
        if action not in seen:
            seen.add(action)
            unique_actions.append(action)
    
    return unique_actions


def _determine_overall_severity_from_agents(agent_results: List[Dict[str, Any]]) -> str:
    """Determina severidade geral baseado nos agentes"""
    severidades = []
    
    for result in agent_results:
        if 'severidade_geral' in result:
            severidades.append(result['severidade_geral'])
    
    if not severidades:
        return SeverityLevel.ZERO
    
    # Usar a severidade mais alta encontrada
    if SeverityLevel.CRITICA in severidades:
        return SeverityLevel.CRITICA
    elif SeverityLevel.ALTA in severidades:
        return SeverityLevel.ALTA
    elif SeverityLevel.MEDIA in severidades:
        return SeverityLevel.MEDIA
    elif SeverityLevel.BAIXA in severidades:
        return SeverityLevel.BAIXA
    else:
        return SeverityLevel.ZERO


def _extract_conclusion_from_agents(agent_results: List[Dict[str, Any]]) -> str:
    """Extrai conclusão dos agentes"""
    conclusions = []
    
    for result in agent_results:
        if 'resumo' in result:
            conclusions.append(result['resumo'])
    
    if conclusions:
        # Usar o último resumo (geralmente do relator executivo)
        return conclusions[-1]
    
    return "Análise concluída"


def _extract_inconsistencies(texto: str) -> List[Dict[str, Any]]:
    """Extrai inconsistências do texto da análise"""
    inconsistencies = []
    
    # Buscar por padrões no texto
    lines = texto.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Detectar tipos comuns de inconsistências
        if 'duplicação' in line_lower or 'duplicado' in line_lower:
            inconsistencies.append({
                'tipo': InconsistencyType.DUPLICACAO,
                'descricao': line.strip(),
                'severidade': _extract_severity(line),
                'evidencia': _get_context(lines, i)
            })
        elif 'ausente' in line_lower or 'faltando' in line_lower:
            inconsistencies.append({
                'tipo': InconsistencyType.CAMPOS_AUSENTES,
                'descricao': line.strip(),
                'severidade': _extract_severity(line),
                'evidencia': _get_context(lines, i)
            })
        elif 'cálculo' in line_lower or 'calcular' in line_lower:
            inconsistencies.append({
                'tipo': InconsistencyType.CALCULOS_INCORRETOS,
                'descricao': line.strip(),
                'severidade': _extract_severity(line),
                'evidencia': _get_context(lines, i)
            })
    
    return inconsistencies


def _extract_recommendations(texto: str) -> List[str]:
    """Extrai recomendações do texto"""
    recomendacoes = []
    lines = texto.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['recomend', 'sugerir', 'aconselhar', 'propõe']):
            if ':' in line:
                recomendacoes.append(line.split(':', 1)[1].strip())
            else:
                recomendacoes.append(line.strip())
    
    return recomendacoes


def _extract_action_plan(texto: str) -> List[str]:
    """Extrai plano de ação do texto"""
    plano = []
    lines = texto.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['ação', 'action', 'prioridade']):
            if '-' in line or '•' in line:
                item = line.split('-', 1)[-1].split('•', 1)[-1].strip()
                if item:
                    plano.append(item)
    
    return plano


def _extract_conclusion(texto: str) -> str:
    """Extrai conclusão do texto"""
    if 'Conclusão:' in texto:
        conclusion_section = texto.split('Conclusão:')[-1].strip()
        # Pegar primeiro parágrafo
        return conclusion_section.split('\n\n')[0].strip()
    elif '**Conclusão**' in texto:
        conclusion_section = texto.split('**Conclusão**')[-1].strip()
        return conclusion_section.split('\n')[0].strip()
    
    return "Análise concluída"


def _extract_severity(line: str) -> str:
    """Extrai severidade de uma linha"""
    line_lower = line.lower()
    
    if 'crítica' in line_lower or 'crítico' in line_lower:
        return SeverityLevel.CRITICA
    elif 'alta' in line_lower:
        return SeverityLevel.ALTA
    elif 'média' in line_lower or 'media' in line_lower:
        return SeverityLevel.MEDIA
    elif 'baixa' in line_lower:
        return SeverityLevel.BAIXA
    else:
        return SeverityLevel.ZERO


def _determine_overall_severity(inconsistencies: List[Dict[str, Any]]) -> str:
    """Determina severidade geral baseado nas inconsistências"""
    if not inconsistencies:
        return SeverityLevel.ZERO
    
    severidades = [inc.get('severidade', SeverityLevel.ZERO) for inc in inconsistencies]
    
    if SeverityLevel.CRITICA in severidades:
        return SeverityLevel.CRITICA
    elif SeverityLevel.ALTA in severidades:
        return SeverityLevel.ALTA
    elif SeverityLevel.MEDIA in severidades:
        return SeverityLevel.MEDIA
    elif SeverityLevel.BAIXA in severidades:
        return SeverityLevel.BAIXA
    else:
        return SeverityLevel.ZERO


def _get_context(lines: List[str], index: int, window: int = 2) -> str:
    """Obtém contexto ao redor de uma linha"""
    start = max(0, index - window)
    end = min(len(lines), index + window + 1)
    return '\n'.join(lines[start:end])


def to_json_structure(result: Dict[str, Any]) -> str:
    """
    Converte resultado para string JSON
    
    Args:
        result: Dicionário com resultado padronizado
        
    Returns:
        String JSON
    """
    import json
    return json.dumps(result, indent=2, ensure_ascii=False)

