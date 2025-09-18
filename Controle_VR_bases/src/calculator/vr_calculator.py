"""
Módulo de cálculos de VR/VA com integração ao banco de dados
"""
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from config import config
from database import VRDatabaseManager

logger = logging.getLogger(__name__)

class VRCalculator:
    """Classe responsável pelos cálculos de VR/VA com integração ao banco de dados"""
    
    def __init__(self, db_manager: Optional[VRDatabaseManager] = None):
        self.company_percentage = config.company_percentage
        self.employee_percentage = config.employee_percentage
        self.excluded_positions = config.excluded_positions
        self.db_manager = db_manager
    
    def apply_exclusions_from_db(self, df_ativos: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Aplica exclusões usando dados do banco de dados
        
        Args:
            df_ativos: DataFrame de funcionários ativos
            
        Returns:
            Tuple[pd.DataFrame, List[str]]: (funcionários_elegíveis, lista_de_exclusões)
        """
        if not self.db_manager:
            logger.warning("Banco de dados não disponível, usando método tradicional")
            return df_ativos, []
        
        logger.info("Aplicando exclusões usando banco de dados...")
        
        df_resultado = df_ativos.copy()
        exclusoes_aplicadas = []
        
        try:
            # 1. Excluir por cargo (usar coluna original)
            if 'Cargo' in df_resultado.columns:
                cargos_excluir = df_resultado['Cargo'].str.upper().str.contains('|'.join(self.excluded_positions), na=False)
                excluidos_cargo = df_resultado[cargos_excluir]
                df_resultado = df_resultado[~cargos_excluir]
                exclusoes_aplicadas.append(f"Excluídos por cargo: {len(excluidos_cargo)} funcionários")
            
            # 2. Excluir afastados
            afastados_query = "SELECT matricula FROM afastados"
            afastados_result = self.db_manager.execute_query(afastados_query)
            afastados_matriculas = [int(row['matricula']) for row in afastados_result]
            
            if afastados_matriculas:
                afastados_mask = df_resultado['Matricula'].isin(afastados_matriculas)
                excluidos_afastados = df_resultado[afastados_mask]
                df_resultado = df_resultado[~afastados_mask]
                exclusoes_aplicadas.append(f"Excluídos afastados: {len(excluidos_afastados)} funcionários")
            
            # 3. Excluir estagiários
            estagio_query = "SELECT matricula FROM estagio"
            result = self.db_manager.execute_query(estagio_query)
            estagio_matriculas = [int(row['matricula']) for row in result]
            
            if estagio_matriculas:
                estagio_mask = df_resultado['Matricula'].isin(estagio_matriculas)
                excluidos_estagio = df_resultado[estagio_mask]
                df_resultado = df_resultado[~estagio_mask]
                exclusoes_aplicadas.append(f"Excluídos estagio: {len(excluidos_estagio)} funcionários")
            
            # 4. Excluir aprendizes
            aprendiz_query = "SELECT matricula FROM aprendiz"
            result = self.db_manager.execute_query(aprendiz_query)
            aprendiz_matriculas = [int(row['matricula']) for row in result]
            
            if aprendiz_matriculas:
                aprendiz_mask = df_resultado['Matricula'].isin(aprendiz_matriculas)
                excluidos_aprendiz = df_resultado[aprendiz_mask]
                df_resultado = df_resultado[~aprendiz_mask]
                exclusoes_aplicadas.append(f"Excluídos aprendiz: {len(excluidos_aprendiz)} funcionários")
            
            # 5. Excluir exterior
            exterior_query = "SELECT matricula FROM exterior"
            exterior_result = self.db_manager.execute_query(exterior_query)
            exterior_matriculas = [int(row['matricula']) for row in exterior_result]
            
            if exterior_matriculas:
                exterior_mask = df_resultado['Matricula'].isin(exterior_matriculas)
                excluidos_exterior = df_resultado[exterior_mask]
                df_resultado = df_resultado[~exterior_mask]
                exclusoes_aplicadas.append(f"Excluídos exterior: {len(excluidos_exterior)} funcionários")
            
            # 6. Excluir desligados
            desligados_query = "SELECT matricula FROM desligados WHERE data_comunicado_desligamento IS NOT NULL"
            desligados_result = self.db_manager.execute_query(desligados_query)
            desligados_matriculas = [int(row['matricula']) for row in desligados_result]
            
            if desligados_matriculas:
                desligados_mask = df_resultado['Matricula'].isin(desligados_matriculas)
                excluidos_desligados = df_resultado[desligados_mask]
                df_resultado = df_resultado[~desligados_mask]
                exclusoes_aplicadas.append(f"Excluídos desligados: {len(excluidos_desligados)} funcionários")
            
            logger.info(f"Exclusões aplicadas via banco: {exclusoes_aplicadas}")
            
        except Exception as e:
            logger.error(f"Erro ao aplicar exclusões via banco: {e}")
            raise
        
        return df_resultado, exclusoes_aplicadas
    
    def calculate_working_days_from_db(self, df_base: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
        """
        Calcula dias úteis usando dados do banco de dados
        
        Args:
            df_base: DataFrame base com funcionários
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            pd.DataFrame: DataFrame com dias úteis calculados
        """
        if not self.db_manager:
            logger.warning("Banco de dados não disponível")
            return df_base
        
        logger.info("Calculando dias úteis usando banco de dados...")
        
        df_resultado = df_base.copy()
        
        try:
            # 1. Obter dias úteis por sindicato
            dias_uteis_query = "SELECT sindicato, dias_uteis_sindicato FROM dias_uteis"
            dias_uteis_result = self.db_manager.execute_query(dias_uteis_query)
            
            # Criar dicionário de dias úteis por sindicato
            dias_uteis_dict = {row['sindicato']: row['dias_uteis_sindicato'] for row in dias_uteis_result}
            
            # 2. Aplicar dias úteis baseado no sindicato
            df_resultado['Dias_VR'] = df_resultado['Sindicato'].map(dias_uteis_dict).fillna(22)
            
            # 3. Aplicar regras de férias
            df_resultado = self._apply_vacation_rules_from_db(df_resultado)
            
            # 4. Aplicar regras de desligamento (removido - agora é exclusão)
            
            # 5. Aplicar regras de admissão
            df_resultado = self._apply_admission_rules_from_db(df_resultado, ano, mes)
            
        except Exception as e:
            logger.error(f"Erro ao calcular dias úteis via banco: {e}")
            raise
        
        return df_resultado
    
    def _apply_vacation_rules_from_db(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica regras de férias usando banco de dados
        
        Args:
            df: DataFrame com funcionários
            
        Returns:
            pd.DataFrame: DataFrame com regras de férias aplicadas
        """
        try:
            # Obter dados de férias do banco
            ferias_query = """
            SELECT matricula, 
                   COALESCE(dias_ferias, 0) as dias_ferias,
                   COALESCE(dias_comprados, 0) as dias_comprados
            FROM ferias
            """
            ferias_result = self.db_manager.execute_query(ferias_query)
            
            # Criar dicionário de férias por matrícula
            ferias_dict = {row['matricula']: {
                'dias_ferias': row['dias_ferias'],
                'dias_comprados': row['dias_comprados']
            } for row in ferias_result}
            
            # Aplicar regras de férias
            for idx, row in df.iterrows():
                matricula = row['Matricula']
                if matricula in ferias_dict:
                    ferias_data = ferias_dict[matricula]
                    dias_ferias = ferias_data['dias_ferias']
                    dias_comprados = ferias_data['dias_comprados']
                    
                    # Aplicar regra de férias
                    if dias_ferias > 0:
                        df.at[idx, 'Dias_VR'] = max(0, df.at[idx, 'Dias_VR'] - dias_ferias)
                    
                    # Aplicar regra de dias comprados
                    if dias_comprados > 0:
                        df.at[idx, 'Dias_VR'] = min(22, df.at[idx, 'Dias_VR'] + dias_comprados)
            
        except Exception as e:
            logger.error(f"Erro ao aplicar regras de férias via banco: {e}")
        
        return df
    
    def _apply_termination_rules_from_db(self, df: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
        """
        Aplica regras de desligamento usando banco de dados
        
        Args:
            df: DataFrame com funcionários
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            pd.DataFrame: DataFrame com regras de desligamento aplicadas
        """
        try:
            # Obter dados de desligamento do banco
            desligados_query = """
            SELECT matricula, data_comunicado_desligamento 
            FROM desligados 
            WHERE data_comunicado_desligamento IS NOT NULL
            """
            desligados_result = self.db_manager.execute_query(desligados_query)
            
            # Obter matrículas de desligados
            desligados_matriculas = [int(row['matricula']) for row in desligados_result]
            
            # Excluir funcionários desligados completamente
            if desligados_matriculas:
                desligados_mask = df['Matricula'].isin(desligados_matriculas)
                df = df[~desligados_mask]
                logger.info(f"Funcionários desligados excluídos: {desligados_mask.sum()}")
        
        except Exception as e:
            logger.error(f"Erro ao aplicar regras de desligamento via banco: {e}")
        
        return df
    
    def _apply_admission_rules_from_db(self, df: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
        """
        Aplica regras de admissão usando banco de dados
        
        Args:
            df: DataFrame com funcionários
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            pd.DataFrame: DataFrame com regras de admissão aplicadas
        """
        try:
            # Obter dados de admissão do banco
            admissoes_query = """
            SELECT matricula, data_admissao 
            FROM admissoes 
            WHERE data_admissao IS NOT NULL
            """
            admissoes_result = self.db_manager.execute_query(admissoes_query)
            
            # Aplicar regras de admissão
            for row in admissoes_result:
                matricula = row['Matricula']
                data_admissao = row['data_admissao']
                
                # Verificar se funcionário está no DataFrame
                mask = df['Matricula'] == matricula
                if mask.any():
                    # Aplicar regra de admissão
                    df.loc[mask, 'Dias_VR'] = 0
        
        except Exception as e:
            logger.error(f"Erro ao aplicar regras de admissão via banco: {e}")
        
        return df
    
    def calculate_vr_values_from_db(self, df_base: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula valores de VR usando dados do banco de dados
        
        Args:
            df_base: DataFrame base com funcionários
            
        Returns:
            pd.DataFrame: DataFrame com valores de VR calculados
        """
        if not self.db_manager:
            logger.warning("Banco de dados não disponível")
            return df_base
        
        logger.info("Calculando valores de VR usando banco de dados...")
        
        df_resultado = df_base.copy()
        
        try:
            # 1. Obter valores por sindicato
            sindicatos_query = "SELECT sindicato, valor_dia_sindicato FROM sindicatos"
            sindicatos_result = self.db_manager.execute_query(sindicatos_query)
            
            # Criar dicionário de valores por sindicato
            valores_dict = {row['sindicato']: row['valor_dia_sindicato'] for row in sindicatos_result}
            
            # 2. Calcular valores de VR
            df_resultado['valor_dia'] = df_resultado['Sindicato'].map(valores_dict).fillna(0)
            df_resultado['VR_Total'] = df_resultado['Dias_VR'] * df_resultado['valor_dia']
            df_resultado['%_Empresa'] = df_resultado['VR_Total'] * self.company_percentage
            df_resultado['%_Colaborador'] = df_resultado['VR_Total'] * self.employee_percentage
            
        except Exception as e:
            logger.error(f"Erro ao calcular valores de VR via banco: {e}")
            raise
        
        return df_resultado
    
    def generate_summary_by_sindicato(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """
        Gera resumo por sindicato
        
        Args:
            df_final: DataFrame final com funcionários
            
        Returns:
            pd.DataFrame: Resumo por sindicato
        """
        try:
            resumo = df_final.groupby('Sindicato').agg({
                'Matricula': 'count',
                'Dias_VR': 'sum',
                'VR_Total': 'sum',
                '%_Empresa': 'sum',
                '%_Colaborador': 'sum'
            }).round(2)
            
            resumo.columns = ['Total_Funcionarios', 'Total_Dias_Uteis', 'Total_VR', 'Total_Empresa', 'Total_Colaborador']
            resumo = resumo.reset_index()
            
            return resumo
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo por sindicato: {e}")
            return pd.DataFrame()
