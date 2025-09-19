"""
Gerador da planilha final de VR conforme modelo VR Mensal 05.2025
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)

class VRFinalGenerator:
    """Gerador da planilha final de VR conforme modelo específico"""
    
    def __init__(self):
        self.output_folder = config.get_output_path()
        self.company_percentage = config.company_percentage
        self.employee_percentage = config.employee_percentage
    
    def generate_vr_final_sheet(self, df_final: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
        """
        Gera a planilha final de VR conforme modelo VR Mensal 05.2025
        
        Args:
            df_final: DataFrame com dados processados
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            pd.DataFrame: Planilha final formatada
        """
        logger.info(f"Gerando planilha final de VR para {mes:02d}/{ano}")
        
        # Criar DataFrame baseado no modelo
        vr_final = pd.DataFrame()
        
        # Colunas conforme modelo VR Mensal 05.2025
        vr_final['Matricula'] = df_final['matricula'].astype(str)
        vr_final['Admissão'] = df_final.get('data_admissao', '')
        vr_final['Sindicato do Colaborador'] = df_final['sindicato']
        vr_final['Competência'] = f"{ano}-{mes:02d}-01"
        vr_final['Dias'] = df_final['dias_vr'].astype(int)
        vr_final['VALOR DIÁRIO VR'] = df_final['valor_dia'].round(2)
        vr_final['TOTAL'] = df_final['vr_total'].round(2)
        vr_final['Custo empresa'] = df_final['%_empresa'].round(2)
        vr_final['Desconto profissional'] = df_final['%_colaborador'].round(2)
        vr_final['OBS GERAL'] = df_final.get('observacao', '')
        
        # Adicionar linha de total
        total_row = pd.DataFrame({
            'Matricula': ['TOTAL'],
            'Admissão': [''],
            'Sindicato do Colaborador': [''],
            'Competência': [''],
            'Dias': [df_final['dias_vr'].sum()],
            'VALOR DIÁRIO VR': [''],
            'TOTAL': [df_final['vr_total'].sum()],
            'Custo empresa': [df_final['%_empresa'].sum()],
            'Desconto profissional': [df_final['%_colaborador'].sum()],
            'OBS GERAL': ['']
        })
        
        vr_final = pd.concat([vr_final, total_row], ignore_index=True)
        
        logger.info(f"Planilha final gerada com {len(vr_final)-1} funcionários")
        return vr_final
    
    def generate_validation_sheet(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """
        Gera aba de validações conforme modelo
        
        Args:
            df_final: DataFrame com dados processados
            
        Returns:
            pd.DataFrame: Aba de validações
        """
        validations = []
        
        # Validações conforme modelo
        validations.append({
            'Validações': 'Afastados / Licenças',
            'Check': 'OK' if df_final[df_final.get('situacao', '').str.contains('afastado|licença', case=False, na=False)].empty else 'VERIFICAR'
        })
        
        validations.append({
            'Validações': 'DESLIGADOS GERAL',
            'Check': 'OK' if df_final[df_final.get('situacao', '').str.contains('desligado', case=False, na=False)].empty else 'VERIFICAR'
        })
        
        validations.append({
            'Validações': 'Admitidos mês',
            'Check': 'OK' if df_final[df_final.get('observacao', '').str.contains('admissão', case=False, na=False)].any() else 'VERIFICAR'
        })
        
        validations.append({
            'Validações': 'Férias aplicadas',
            'Check': 'OK' if df_final[df_final.get('observacao', '').str.contains('férias', case=False, na=False)].any() else 'VERIFICAR'
        })
        
        validations.append({
            'Validações': 'Valores por sindicato',
            'Check': 'OK' if df_final['valor_dia'].notna().all() else 'VERIFICAR'
        })
        
        validations.append({
            'Validações': 'Dias úteis aplicados',
            'Check': 'OK' if df_final['dias_vr'].between(0, 22).all() else 'VERIFICAR'
        })
        
        validations.append({
            'Validações': 'Cálculos de VR',
            'Check': 'OK' if (df_final['vr_total'] == df_final['dias_vr'] * df_final['valor_dia']).all() else 'VERIFICAR'
        })
        
        validations.append({
            'Validações': 'Percentuais empresa/colaborador',
            'Check': 'OK' if ((df_final['%_empresa'] + df_final['%_colaborador']).round(2) == df_final['vr_total'].round(2)).all() else 'VERIFICAR'
        })
        
        return pd.DataFrame(validations)
    
    def generate_summary_by_sindicato(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """
        Gera resumo por sindicato
        
        Args:
            df_final: DataFrame com dados processados
            
        Returns:
            pd.DataFrame: Resumo por sindicato
        """
        summary = df_final.groupby('sindicato').agg({
            'matricula': 'count',
            'dias_vr': 'sum',
            'vr_total': 'sum',
            '%_empresa': 'sum',
            '%_colaborador': 'sum'
        }).round(2)
        
        summary.columns = ['Funcionários', 'Total Dias', 'Total VR', 'Custo Empresa', 'Desconto Colaborador']
        summary = summary.reset_index()
        
        return summary
    
    def save_vr_final_report(self, 
                           df_vr_final: pd.DataFrame, 
                           df_validations: pd.DataFrame,
                           df_summary: pd.DataFrame,
                           ano: int, 
                           mes: int) -> str:
        """
        Salva relatório final de VR conforme modelo
        
        Args:
            df_vr_final: Planilha final de VR
            df_validations: Validações
            df_summary: Resumo por sindicato
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            str: Caminho do arquivo salvo
        """
        filename = f"VR_MENSAL_{mes:02d}.{ano}.xlsx"
        output_path = self.output_folder / filename
        
        logger.info(f"Salvando relatório final: {output_path}")
        
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Aba principal conforme modelo
            df_vr_final.to_excel(writer, sheet_name=f"VR MENSAL {mes:02d}.{ano}", index=False)
            
            # Aba de validações
            df_validations.to_excel(writer, sheet_name="Validações", index=False)
            
            # Aba de resumo por sindicato
            df_summary.to_excel(writer, sheet_name="Resumo_Sindicato", index=False)
        
        logger.info(f"✅ Relatório final salvo: {output_path}")
        return str(output_path)
    
    def generate_complete_vr_report(self, df_final: pd.DataFrame, ano: int, mes: int) -> str:
        """
        Gera relatório completo de VR
        
        Args:
            df_final: DataFrame com dados processados
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            str: Caminho do arquivo salvo
        """
        logger.info("Gerando relatório completo de VR...")
        
        # Gerar planilha final
        df_vr_final = self.generate_vr_final_sheet(df_final, ano, mes)
        
        # Gerar validações
        df_validations = self.generate_validation_sheet(df_final)
        
        # Gerar resumo por sindicato
        df_summary = self.generate_summary_by_sindicato(df_final)
        
        # Salvar relatório
        output_path = self.save_vr_final_report(df_vr_final, df_validations, df_summary, ano, mes)
        
        # Log de estatísticas
        total_funcionarios = len(df_final)
        total_vr = df_final['vr_total'].sum()
        total_empresa = df_final['%_empresa'].sum()
        total_colaborador = df_final['%_colaborador'].sum()
        
        logger.info(f"📊 Estatísticas do relatório:")
        logger.info(f"   - Funcionários: {total_funcionarios}")
        logger.info(f"   - Total VR: R$ {total_vr:,.2f}")
        logger.info(f"   - Custo empresa: R$ {total_empresa:,.2f}")
        logger.info(f"   - Desconto colaborador: R$ {total_colaborador:,.2f}")
        
        return output_path
