"""
Módulo de geração de relatórios Excel
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Any
from config import config

logger = logging.getLogger(__name__)

class ExcelReportGenerator:
    """Classe responsável por gerar relatórios Excel"""
    
    def __init__(self):
        self.output_folder = config.get_output_path()
    
    def generate_validation_report(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """
        Gera relatório de validações
        
        Args:
            df_final: DataFrame final com dados processados
            
        Returns:
            pd.DataFrame: Relatório de validações
        """
        validations = []
        
        # Validações críticas
        for idx, row in df_final.iterrows():
            matricula = row.get("Matricula", "N/A")
            dias_vr = row.get("Dias_VR", 0)
            vr_total = row.get("VR_Total", 0)
            
            # Dias zerados com valor > 0
            if dias_vr == 0 and vr_total > 0:
                validations.append({
                    "Matricula": matricula,
                    "Problema": "Dias zerados com valor > 0",
                    "Severidade": "CRÍTICO",
                    "Valor": vr_total
                })
            
            # Sem valor mesmo com dias > 0
            elif dias_vr > 0 and vr_total == 0:
                validations.append({
                    "Matricula": matricula,
                    "Problema": "Sem valor mesmo com dias > 0",
                    "Severidade": "CRÍTICO",
                    "Valor": dias_vr
                })
            
            # Dias negativos
            elif dias_vr < 0:
                validations.append({
                    "Matricula": matricula,
                    "Problema": "Dias negativos",
                    "Severidade": "CRÍTICO",
                    "Valor": dias_vr
                })
            
            # Valor VR negativo
            elif vr_total < 0:
                validations.append({
                    "Matricula": matricula,
                    "Problema": "Valor VR negativo",
                    "Severidade": "CRÍTICO",
                    "Valor": vr_total
                })
            
            # Dias maiores que possível no mês
            elif dias_vr > 31:
                validations.append({
                    "Matricula": matricula,
                    "Problema": "Dias maiores que possível no mês",
                    "Severidade": "ALERTA",
                    "Valor": dias_vr
                })
            
            # Poucos dias trabalhados
            elif dias_vr > 0 and dias_vr < 5:
                validations.append({
                    "Matricula": matricula,
                    "Problema": "Poucos dias trabalhados",
                    "Severidade": "ALERTA",
                    "Valor": dias_vr
                })
            
            # OK
            else:
                validations.append({
                    "Matricula": matricula,
                    "Problema": "ok",
                    "Severidade": "OK",
                    "Valor": vr_total
                })
        
        return pd.DataFrame(validations)
    
    def generate_statistics_report(self, df_final: pd.DataFrame, exclusoes_aplicadas: List[str]) -> pd.DataFrame:
        """
        Gera relatório de estatísticas
        
        Args:
            df_final: DataFrame final com dados processados
            exclusoes_aplicadas: Lista de exclusões aplicadas
            
        Returns:
            pd.DataFrame: Relatório de estatísticas
        """
        stats = [
            {"Métrica": "Total Funcionários", "Valor": len(df_final)},
            {"Métrica": "Total VR", "Valor": f"R$ {df_final['VR_Total'].sum():,.2f}"},
            {"Métrica": "Total Empresa (80%)", "Valor": f"R$ {df_final['%_Empresa'].sum():,.2f}"},
            {"Métrica": "Total Colaborador (20%)", "Valor": f"R$ {df_final['%_Colaborador'].sum():,.2f}"},
            {"Métrica": "Média Dias por Funcionário", "Valor": f"{df_final['Dias_VR'].mean():.1f}"},
            {"Métrica": "Funcionários com Problemas", "Valor": len(df_final[df_final['VR_Total'] <= 0])}
        ]
        
        # Adicionar exclusões aplicadas
        for exclusao in exclusoes_aplicadas:
            stats.append({"Métrica": "Exclusões", "Valor": exclusao})
        
        return pd.DataFrame(stats)
    
    def generate_insights_report(self, insights_ia: Dict[str, Any]) -> pd.DataFrame:
        """
        Gera relatório de insights da IA
        
        Args:
            insights_ia: Insights gerados pela IA
            
        Returns:
            pd.DataFrame: Relatório de insights
        """
        insights_data = []
        
        # Resumo geral
        if "resumo_geral" in insights_ia:
            insights_data.append({
                "Categoria": "Resumo Geral",
                "Informação": insights_ia["resumo_geral"]
            })
        
        # Alertas
        if "alertas" in insights_ia and insights_ia["alertas"]:
            for alerta in insights_ia["alertas"]:
                insights_data.append({
                    "Categoria": "Alertas",
                    "Informação": alerta
                })
        
        # Sugestões
        if "sugestoes" in insights_ia and insights_ia["sugestoes"]:
            for sugestao in insights_ia["sugestoes"]:
                insights_data.append({
                    "Categoria": "Sugestões",
                    "Informação": sugestao
                })
        
        # Estatísticas
        if "estatisticas" in insights_ia and insights_ia["estatisticas"]:
            for key, value in insights_ia["estatisticas"].items():
                insights_data.append({
                    "Categoria": "Estatísticas",
                    "Informação": f"{key}: {value}"
                })
        
        return pd.DataFrame(insights_data)
    
    def save_complete_report(self, 
                           df_final: pd.DataFrame, 
                           df_resumo: pd.DataFrame, 
                           df_validacoes: pd.DataFrame, 
                           df_insights: pd.DataFrame,
                           df_statistics: pd.DataFrame,
                           filename: str) -> str:
        """
        Salva relatório completo em Excel
        
        Args:
            df_final: DataFrame final com dados processados
            df_resumo: Resumo por sindicato
            df_validacoes: Validações
            df_insights: Insights da IA
            df_statistics: Estatísticas
            filename: Nome do arquivo
            
        Returns:
            str: Caminho do arquivo salvo
        """
        output_path = self.output_folder / filename
        
        logger.info(f"Salvando relatório completo: {output_path}")
        
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Aba principal conforme modelo "VR Mensal 05.2025"
            df_final.to_excel(writer, sheet_name="VR_Mensal", index=False)
            
            # Aba de resumo por sindicato
            df_resumo.to_excel(writer, sheet_name="resumo_sindicato", index=False)
            
            # Aba de validações
            df_validacoes.to_excel(writer, sheet_name="validações", index=False)
            
            # Aba com dados completos
            df_final.to_excel(writer, sheet_name="VR_Completo", index=False)
            
            # Aba com insights da IA
            df_insights.to_excel(writer, sheet_name="insights_ia", index=False)
            
            # Aba com estatísticas
            df_statistics.to_excel(writer, sheet_name="estatisticas", index=False)
        
        logger.info(f"✅ Relatório salvo com sucesso: {output_path}")
        return str(output_path)
