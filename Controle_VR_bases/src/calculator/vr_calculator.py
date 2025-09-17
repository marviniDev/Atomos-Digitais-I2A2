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
    
    def apply_exclusions(self, df_ativos: pd.DataFrame, spreadsheets: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, List[str]]:
        """
        Aplica todas as regras de exclusão
        
        Args:
            df_ativos: DataFrame de funcionários ativos
            spreadsheets: Dicionário com todas as planilhas
            
        Returns:
            Tuple[pd.DataFrame, List[str]]: (funcionários_elegíveis, lista_de_exclusões)
        """
        logger.info("Aplicando regras de exclusão...")
        
        df_resultado = df_ativos.copy()
        exclusoes_aplicadas = []
        
        # 1. Excluir por cargo
        if 'Cargo' in df_resultado.columns:
            cargos_excluir = df_resultado['Cargo'].str.upper().str.contains('|'.join(self.excluded_positions), na=False)
            excluidos_cargo = df_resultado[cargos_excluir]
            df_resultado = df_resultado[~cargos_excluir]
            exclusoes_aplicadas.append(f"Excluídos por cargo: {len(excluidos_cargo)} funcionários")
        
        # 2. Excluir afastados
        if "afastados" in spreadsheets:
            afastados_matriculas = spreadsheets["afastados"]["Matricula"].astype(str).unique()
            excluidos_afastados = df_resultado[df_resultado["Matricula"].astype(str).isin(afastados_matriculas)]
            df_resultado = df_resultado[~df_resultado["Matricula"].astype(str).isin(afastados_matriculas)]
            exclusoes_aplicadas.append(f"Excluídos afastados: {len(excluidos_afastados)} funcionários")
        
        # 3. Excluir estagiários e aprendizes (por planilha)
        for chave in ["estagio", "aprendiz"]:
            if chave in spreadsheets:
                mats = spreadsheets[chave]["Matricula"].astype(str).unique()
                excluidos = df_resultado[df_resultado["Matricula"].astype(str).isin(mats)]
                df_resultado = df_resultado[~df_resultado["Matricula"].astype(str).isin(mats)]
                exclusoes_aplicadas.append(f"Excluídos {chave}: {len(excluidos)} funcionários")
        
        # 4. Excluir profissionais no exterior (lidar com diferentes casos de colunas)
        if "exterior" in spreadsheets:
            # Verificar se a coluna é 'Matricula' ou 'matricula'
            if 'Matricula' in spreadsheets["exterior"].columns:
                exterior_mats = spreadsheets["exterior"]["Matricula"].astype(str).unique()
            elif 'matricula' in spreadsheets["exterior"].columns:
                exterior_mats = spreadsheets["exterior"]["matricula"].astype(str).unique()
            else:
                exterior_mats = []
            
            if len(exterior_mats) > 0:
                excluidos_exterior = df_resultado[df_resultado["Matricula"].astype(str).isin(exterior_mats)]
                df_resultado = df_resultado[~df_resultado["Matricula"].astype(str).isin(exterior_mats)]
                exclusoes_aplicadas.append(f"Excluídos exterior: {len(excluidos_exterior)} funcionários")
        
        logger.info(f"Exclusões aplicadas: {exclusoes_aplicadas}")
        return df_resultado, exclusoes_aplicadas
    
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
            if afastados_result:
                afastados_matriculas = [str(row['matricula']) for row in afastados_result]
                excluidos_afastados = df_resultado[df_resultado["Matricula"].astype(str).isin(afastados_matriculas)]
                df_resultado = df_resultado[~df_resultado["Matricula"].astype(str).isin(afastados_matriculas)]
                exclusoes_aplicadas.append(f"Excluídos afastados: {len(excluidos_afastados)} funcionários")
            
            # 3. Excluir estagiários e aprendizes
            for tabela in ["estagio", "aprendiz"]:
                query = f"SELECT matricula FROM {tabela}"
                result = self.db_manager.execute_query(query)
                if result:
                    mats = [str(row['matricula']) for row in result]
                    excluidos = df_resultado[df_resultado["Matricula"].astype(str).isin(mats)]
                    df_resultado = df_resultado[~df_resultado["Matricula"].astype(str).isin(mats)]
                    exclusoes_aplicadas.append(f"Excluídos {tabela}: {len(excluidos)} funcionários")
            
            # 4. Excluir profissionais no exterior
            exterior_query = "SELECT matricula FROM exterior"
            exterior_result = self.db_manager.execute_query(exterior_query)
            if exterior_result:
                exterior_mats = [str(row['matricula']) for row in exterior_result]
                excluidos_exterior = df_resultado[df_resultado["Matricula"].astype(str).isin(exterior_mats)]
                df_resultado = df_resultado[~df_resultado["Matricula"].astype(str).isin(exterior_mats)]
                exclusoes_aplicadas.append(f"Excluídos exterior: {len(excluidos_exterior)} funcionários")
            
        except Exception as e:
            logger.error(f"Erro ao aplicar exclusões do banco: {e}")
            return df_ativos, []
        
        logger.info(f"Exclusões aplicadas via banco: {exclusoes_aplicadas}")
        return df_resultado, exclusoes_aplicadas
    
    def calculate_working_days(self, df_base: pd.DataFrame, spreadsheets: Dict[str, pd.DataFrame], ano: int, mes: int) -> pd.DataFrame:
        """
        Calcula os dias úteis por colaborador
        
        Args:
            df_base: DataFrame base de funcionários
            spreadsheets: Dicionário com planilhas
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            pd.DataFrame: DataFrame com dias calculados
        """
        logger.info("Calculando dias úteis por colaborador...")
        
        df_resultado = df_base.copy()
        
        # Mapear dias úteis por sindicato
        if "dias_uteis" in spreadsheets:
            dias_uteis_dict = dict(
                zip(
                    spreadsheets["dias_uteis"]["Sindicato"].astype(str).str.strip(),
                    spreadsheets["dias_uteis"]["Dias_Uteis_Sindicato"]
                )
            )
            
            # Aplicar dias úteis base por sindicato
            df_resultado["Sindicato"] = df_resultado["Sindicato"].astype(str).str.strip()
            df_resultado["Dias_VR"] = df_resultado["Sindicato"].map(dias_uteis_dict).fillna(0)
        else:
            df_resultado["Dias_VR"] = 0
        
        # Aplicar regras de férias
        df_resultado = self._apply_vacation_rules(df_resultado, spreadsheets)
        
        # Aplicar regras de desligamento
        df_resultado = self._apply_termination_rules(df_resultado, spreadsheets, ano, mes)
        
        # Aplicar regras de admissão
        df_resultado = self._apply_admission_rules(df_resultado, spreadsheets, ano, mes)
        
        return df_resultado
    
    def calculate_working_days_from_db(self, df_base: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
        """
        Calcula os dias úteis por colaborador usando dados do banco
        
        Args:
            df_base: DataFrame base de funcionários
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            pd.DataFrame: DataFrame com dias calculados
        """
        if not self.db_manager:
            logger.warning("Banco de dados não disponível, usando método tradicional")
            return df_base
        
        logger.info("Calculando dias úteis usando banco de dados...")
        
        df_resultado = df_base.copy()
        
        try:
            # Mapear dias úteis por sindicato do banco
            dias_uteis_query = "SELECT sindicato, dias_uteis_sindicato FROM dias_uteis"
            dias_uteis_result = self.db_manager.execute_query(dias_uteis_query)
            
            if dias_uteis_result:
                dias_uteis_dict = {str(row['sindicato']).strip(): row['dias_uteis_sindicato'] for row in dias_uteis_result}
                
                # Aplicar dias úteis base por sindicato (usar coluna original)
                df_resultado["Sindicato"] = df_resultado["Sindicato"].astype(str).str.strip()
                df_resultado["Dias_VR"] = df_resultado["Sindicato"].map(dias_uteis_dict).fillna(0)
            else:
                df_resultado["Dias_VR"] = 0
            
            # Aplicar regras de férias do banco
            df_resultado = self._apply_vacation_rules_from_db(df_resultado)
            
            # Aplicar regras de desligamento do banco
            df_resultado = self._apply_termination_rules_from_db(df_resultado, ano, mes)
            
            # Aplicar regras de admissão do banco
            df_resultado = self._apply_admission_rules_from_db(df_resultado, ano, mes)
            
        except Exception as e:
            logger.error(f"Erro ao calcular dias úteis do banco: {e}")
            return df_base
        
        return df_resultado
    
    def _apply_vacation_rules(self, df: pd.DataFrame, spreadsheets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Aplica regras de férias"""
        if "ferias" not in spreadsheets:
            return df
        
        df_ferias = spreadsheets["ferias"].copy()
        df_ferias["Matricula"] = df_ferias["Matricula"].astype(str)
        df_ferias["Dias_Comprados"] = df_ferias["Dias_Comprados"].fillna(0)
        df_ferias["Dias_Ferias"] = df_ferias["Dias_Ferias"].fillna(0)
        df_ferias["Dias_Descontar"] = df_ferias["Dias_Ferias"] - df_ferias["Dias_Comprados"]
        df_ferias["Dias_Descontar"] = df_ferias["Dias_Descontar"].clip(lower=0)
        
        ferias_dict = df_ferias.groupby("Matricula")["Dias_Descontar"].sum().to_dict()
        df["Matricula"] = df["Matricula"].astype(str)
        df["Dias_VR"] = df.apply(
            lambda row: max(row["Dias_VR"] - ferias_dict.get(row["Matricula"], 0), 0), axis=1
        )
        
        return df
    
    def _apply_vacation_rules_from_db(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica regras de férias usando dados do banco"""
        if not self.db_manager:
            return df
        
        try:
            ferias_query = """
            SELECT matricula, 
                   COALESCE(dias_ferias, 0) as dias_ferias,
                   COALESCE(dias_comprados, 0) as dias_comprados
            FROM ferias
            """
            ferias_result = self.db_manager.execute_query(ferias_query)
            
            if ferias_result:
                ferias_dict = {}
                for row in ferias_result:
                    matricula = row['matricula']
                    dias_ferias = row['dias_ferias'] or 0
                    dias_comprados = row['dias_comprados'] or 0
                    dias_descontar = max(dias_ferias - dias_comprados, 0)
                    ferias_dict[matricula] = ferias_dict.get(matricula, 0) + dias_descontar
                
                df["Matricula"] = df["Matricula"].astype(str)
                df["Dias_VR"] = df.apply(
                    lambda row: max(row["Dias_VR"] - ferias_dict.get(row["Matricula"], 0), 0), axis=1
                )
        except Exception as e:
            logger.error(f"Erro ao aplicar regras de férias do banco: {e}")
        
        return df
    
    def _apply_termination_rules(self, df: pd.DataFrame, spreadsheets: Dict[str, pd.DataFrame], ano: int, mes: int) -> pd.DataFrame:
        """Aplica regras de desligamento"""
        if "desligados" not in spreadsheets:
            return df
        
        df_desligados = spreadsheets["desligados"].copy()
        df_desligados["Matricula"] = df_desligados["Matricula"].astype(str)
        
        if 'Data_Comunicado_Desligamento' in df_desligados.columns:
            df_desligados['Data_Comunicado_Desligamento'] = pd.to_datetime(df_desligados['Data_Comunicado_Desligamento'], errors='coerce')
            
            # Aplicar regra do dia 15
            for _, row in df_desligados.iterrows():
                matricula = row["Matricula"]
                if pd.notna(row['Data_Comunicado_Desligamento']):
                    if row['Data_Comunicado_Desligamento'].day <= 15:
                        # Não considerar para pagamento
                        df.loc[df["Matricula"] == matricula, "Dias_VR"] = 0
        
        return df
    
    def _apply_termination_rules_from_db(self, df: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
        """Aplica regras de desligamento usando dados do banco"""
        if not self.db_manager:
            return df
        
        try:
            desligados_query = """
            SELECT matricula, data_comunicado_desligamento 
            FROM desligados 
            WHERE data_comunicado_desligamento IS NOT NULL
            """
            desligados_result = self.db_manager.execute_query(desligados_query)
            
            if desligados_result:
                for row in desligados_result:
                    matricula = row['matricula']
                    data_comunicado = row['data_comunicado_desligamento']
                    
                    if data_comunicado and data_comunicado != 'OK':
                        try:
                            data_dt = pd.to_datetime(data_comunicado)
                            if data_dt.day <= 15:
                                df.loc[df["matricula"] == matricula, "Dias_VR"] = 0
                        except:
                            pass
        except Exception as e:
            logger.error(f"Erro ao aplicar regras de desligamento do banco: {e}")
        
        return df
    
    def _apply_admission_rules(self, df: pd.DataFrame, spreadsheets: Dict[str, pd.DataFrame], ano: int, mes: int) -> pd.DataFrame:
        """Aplica regras de admissão"""
        if "admissoes" not in spreadsheets:
            return df
        
        df_admissoes = spreadsheets["admissoes"].copy()
        df_admissoes["Matricula"] = df_admissoes["Matricula"].astype(str)
        df_admissoes['Data_Admissao'] = pd.to_datetime(df_admissoes['Data_Admissao'], errors='coerce')
        
        for _, row in df_admissoes.iterrows():
            matricula = row["Matricula"]
            if pd.notna(row['Data_Admissao']):
                # Se admitido no meio do mês, calcular proporcional
                dias_restantes = (pd.Timestamp(f"{ano}-{mes:02d}-01") + pd.offsets.MonthEnd(0) - row['Data_Admissao']).days + 1
                if dias_restantes < 30:  # Se não é do início do mês
                    # Aplicar proporção
                    df.loc[df["Matricula"] == matricula, "Dias_VR"] = \
                        df.loc[df["Matricula"] == matricula, "Dias_VR"] * (dias_restantes / 30)
        
        return df
    
    def _apply_admission_rules_from_db(self, df: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
        """Aplica regras de admissão usando dados do banco"""
        if not self.db_manager:
            return df
        
        try:
            admissoes_query = """
            SELECT matricula, data_admissao 
            FROM admissoes 
            WHERE data_admissao IS NOT NULL
            """
            admissoes_result = self.db_manager.execute_query(admissoes_query)
            
            if admissoes_result:
                for row in admissoes_result:
                    matricula = row['matricula']
                    data_admissao = row['data_admissao']
                    
                    if data_admissao:
                        try:
                            data_dt = pd.to_datetime(data_admissao)
                            dias_restantes = (pd.Timestamp(f"{ano}-{mes:02d}-01") + pd.offsets.MonthEnd(0) - data_dt).days + 1
                            if dias_restantes < 30:  # Se não é do início do mês
                                df.loc[df["matricula"] == matricula, "Dias_VR"] = \
                                    df.loc[df["matricula"] == matricula, "Dias_VR"] * (dias_restantes / 30)
                        except:
                            pass
        except Exception as e:
            logger.error(f"Erro ao aplicar regras de admissão do banco: {e}")
        
        return df
    
    def calculate_vr_values(self, df_base: pd.DataFrame, spreadsheets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calcula os valores de VR por colaborador
        
        Args:
            df_base: DataFrame base com dias calculados
            spreadsheets: Dicionário com planilhas
            
        Returns:
            pd.DataFrame: DataFrame com valores calculados
        """
        logger.info("Calculando valores de VR...")
        
        df_resultado = df_base.copy()
        
        # Mapear valor por sindicato
        if "sindicatos" in spreadsheets:
            valor_sindicato_dict = dict(
                zip(
                    spreadsheets["sindicatos"]["Sindicato"].astype(str).str.strip(),
                    spreadsheets["sindicatos"]["Valor_Dia_Sindicato"]
                )
            )
            
            # Aplicar valor por sindicato
            df_resultado["Valor_Dia"] = df_resultado["Sindicato"].map(valor_sindicato_dict).fillna(0)
        else:
            df_resultado["Valor_Dia"] = 0
        
        # Calcular valores totais
        df_resultado["VR_Total"] = df_resultado["Dias_VR"] * df_resultado["Valor_Dia"]
        df_resultado["%_Empresa"] = df_resultado["VR_Total"] * self.company_percentage
        df_resultado["%_Colaborador"] = df_resultado["VR_Total"] * self.employee_percentage
        
        return df_resultado
    
    def calculate_vr_values_from_db(self, df_base: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula os valores de VR por colaborador usando dados do banco
        
        Args:
            df_base: DataFrame base com dias calculados
            
        Returns:
            pd.DataFrame: DataFrame com valores calculados
        """
        if not self.db_manager:
            logger.warning("Banco de dados não disponível, usando método tradicional")
            return df_base
        
        logger.info("Calculando valores de VR usando banco de dados...")
        
        df_resultado = df_base.copy()
        
        try:
            # Mapear valor por sindicato do banco
            sindicatos_query = "SELECT sindicato, valor_dia_sindicato FROM sindicatos"
            sindicatos_result = self.db_manager.execute_query(sindicatos_query)
            
            if sindicatos_result:
                valor_sindicato_dict = {str(row['sindicato']).strip(): row['valor_dia_sindicato'] for row in sindicatos_result}
                
                # Aplicar valor por sindicato (usar coluna original)
                df_resultado["Valor_Dia"] = df_resultado["Sindicato"].map(valor_sindicato_dict).fillna(0)
            else:
                df_resultado["Valor_Dia"] = 0
            
            # Calcular valores totais
            df_resultado["VR_Total"] = df_resultado["Dias_VR"] * df_resultado["Valor_Dia"]
            df_resultado["%_Empresa"] = df_resultado["VR_Total"] * self.company_percentage
            df_resultado["%_Colaborador"] = df_resultado["VR_Total"] * self.employee_percentage
            
        except Exception as e:
            logger.error(f"Erro ao calcular valores de VR do banco: {e}")
            return df_base
        
        return df_resultado
    
    def generate_summary_by_sindicato(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """
        Gera resumo por sindicato
        
        Args:
            df_final: DataFrame final com valores calculados
            
        Returns:
            pd.DataFrame: Resumo por sindicato
        """
        if "Sindicato" not in df_final.columns and "sindicato" not in df_final.columns:
            return pd.DataFrame()
        
        # Usar coluna sindicato (minúscula) se disponível, senão Sindicato
        sindicato_col = "sindicato" if "sindicato" in df_final.columns else "Sindicato"
        
        resumo = df_final.groupby(sindicato_col)[
            ["Dias_VR", "VR_Total", "%_Empresa", "%_Colaborador"]
        ].sum().reset_index()
        
        return resumo
