"""
Módulo de cálculos de VR/VA com integração ao banco de dados
"""
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from config import config
from database import VRDatabaseManager
from .holiday_calendar import HolidayCalendar

logger = logging.getLogger(__name__)

class VRCalculator:
    """Classe responsável pelos cálculos de VR/VA com integração ao banco de dados"""
    
    def __init__(self, db_manager: Optional[VRDatabaseManager] = None):
        self.company_percentage = config.company_percentage
        self.employee_percentage = config.employee_percentage
        self.excluded_positions = config.excluded_positions
        self.db_manager = db_manager
        self.holiday_calendar = HolidayCalendar()
    
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
            afastados_matriculas = [row['matricula'] for row in afastados_result]
            
            # Converter matrículas do DataFrame para string para comparação
            df_resultado['matricula'] = df_resultado['matricula'].astype(str)
            
            if afastados_matriculas:
                afastados_mask = df_resultado['matricula'].isin(afastados_matriculas)
                excluidos_afastados = df_resultado[afastados_mask]
                df_resultado = df_resultado[~afastados_mask]
                exclusoes_aplicadas.append(f"Excluídos afastados: {len(excluidos_afastados)} funcionários")
            
            # 3. Excluir estagiários
            estagio_query = "SELECT matricula FROM estagio"
            result = self.db_manager.execute_query(estagio_query)
            estagio_matriculas = [int(row['matricula']) for row in result]
            
            if estagio_matriculas:
                estagio_mask = df_resultado['matricula'].isin(estagio_matriculas)
                excluidos_estagio = df_resultado[estagio_mask]
                df_resultado = df_resultado[~estagio_mask]
                exclusoes_aplicadas.append(f"Excluídos estagio: {len(excluidos_estagio)} funcionários")
            
            # 4. Excluir aprendizes
            aprendiz_query = "SELECT matricula FROM aprendiz"
            result = self.db_manager.execute_query(aprendiz_query)
            aprendiz_matriculas = [int(row['matricula']) for row in result]
            
            if aprendiz_matriculas:
                aprendiz_mask = df_resultado['matricula'].isin(aprendiz_matriculas)
                excluidos_aprendiz = df_resultado[aprendiz_mask]
                df_resultado = df_resultado[~aprendiz_mask]
                exclusoes_aplicadas.append(f"Excluídos aprendiz: {len(excluidos_aprendiz)} funcionários")
            
            # 5. Excluir exterior
            exterior_query = "SELECT matricula FROM exterior"
            exterior_result = self.db_manager.execute_query(exterior_query)
            exterior_matriculas = [row['matricula'] for row in exterior_result]
            
            if exterior_matriculas:
                exterior_mask = df_resultado['matricula'].isin(exterior_matriculas)
                excluidos_exterior = df_resultado[exterior_mask]
                df_resultado = df_resultado[~exterior_mask]
                exclusoes_aplicadas.append(f"Excluídos exterior: {len(excluidos_exterior)} funcionários")
            
            # 6. Excluir desligados
            desligados_query = "SELECT matricula FROM desligados WHERE data_comunicado_desligamento IS NOT NULL"
            desligados_result = self.db_manager.execute_query(desligados_query)
            desligados_matriculas = [row['matricula'] for row in desligados_result]
            
            if desligados_matriculas:
                desligados_mask = df_resultado['matricula'].isin(desligados_matriculas)
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
            df_resultado['dias_vr'] = df_resultado['sindicato'].map(dias_uteis_dict).fillna(22)
            
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
        
        Regras por sindicato:
        - Férias parciais: reduzir dias de VR proporcionalmente
        - Férias integrais: zerar dias de VR
        - Dias comprados: adicionar aos dias de VR (máximo 22)
        
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
                   COALESCE(dias_comprados, 0) as dias_comprados,
                   situacao
            FROM ferias
            """
            ferias_result = self.db_manager.execute_query(ferias_query)
            
            if not ferias_result:
                logger.info("Nenhum funcionário em férias encontrado")
                return df
            
            # Criar dicionário de férias por matrícula
            ferias_dict = {row['matricula']: {
                'dias_ferias': row['dias_ferias'],
                'dias_comprados': row['dias_comprados'],
                'situacao': row['situacao']
            } for row in ferias_result}
            
            # Aplicar regras de férias
            funcionarios_em_ferias = 0
            funcionarios_ferias_parciais = 0
            funcionarios_dias_comprados = 0
            
            for idx, row in df.iterrows():
                matricula = row['matricula']
                if matricula in ferias_dict:
                    ferias_data = ferias_dict[matricula]
                    dias_ferias = ferias_data['dias_ferias']
                    dias_comprados = ferias_data['dias_comprados']
                    situacao = ferias_data['situacao']
                    
                    # Verificar se está em férias
                    if situacao and 'férias' in situacao.lower():
                        funcionarios_em_ferias += 1
                        
                        # Aplicar regra de férias
                        if dias_ferias > 0:
                            if dias_ferias >= 22:  # Férias integrais
                                df.at[idx, 'dias_vr'] = 0
                                df.at[idx, 'observacao'] = f'Férias integrais - {dias_ferias} dias'
                            else:  # Férias parciais
                                df.at[idx, 'dias_vr'] = max(0, df.at[idx, 'dias_vr'] - dias_ferias)
                                df.at[idx, 'observacao'] = f'Férias parciais - {dias_ferias} dias'
                                funcionarios_ferias_parciais += 1
                        else:
                            # Em férias mas sem dias específicos - zerar
                            df.at[idx, 'dias_vr'] = 0
                            df.at[idx, 'observacao'] = 'Férias - sem dias específicos'
                    
                    # Aplicar regra de dias comprados
                    if dias_comprados > 0:
                        df.at[idx, 'dias_vr'] = min(22, df.at[idx, 'dias_vr'] + dias_comprados)
                        df.at[idx, 'observacao'] = f'Dias comprados: +{dias_comprados} dias'
                        funcionarios_dias_comprados += 1
            
            logger.info(f"Regras de férias aplicadas:")
            logger.info(f"  - Funcionários em férias: {funcionarios_em_ferias}")
            logger.info(f"  - Férias parciais: {funcionarios_ferias_parciais}")
            logger.info(f"  - Dias comprados: {funcionarios_dias_comprados}")
            
        except Exception as e:
            logger.error(f"Erro ao aplicar regras de férias via banco: {e}")
        
        return df
    
    def _apply_termination_rules_from_db(self, df: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
        """
        Aplica regras de desligamento usando banco de dados
        
        Regras:
        - Se comunicado de desligamento até dia 15: não considerar para pagamento
        - Se comunicado depois do dia 15: compra proporcional
        
        Args:
            df: DataFrame com funcionários
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            pd.DataFrame: DataFrame com regras de desligamento aplicadas
        """
        try:
            from datetime import datetime, date
            
            # Obter dados de desligamento do banco
            desligados_query = """
            SELECT matricula, data_desligamento, data_comunicado_desligamento 
            FROM desligados 
            WHERE data_desligamento IS NOT NULL
            """
            desligados_result = self.db_manager.execute_query(desligados_query)
            
            if not desligados_result:
                logger.info("Nenhum funcionário desligado encontrado")
                return df
            
            # Data de corte: dia 15 do mês
            data_corte = date(ano, mes, 15)
            
            # Separar desligados por regra
            desligados_excluir = []  # Comunicado até dia 15
            desligados_proporcional = []  # Comunicado depois do dia 15
            
            for desligado in desligados_result:
                matricula = desligado['matricula']
                data_desligamento = desligado['data_desligamento']
                data_comunicado = desligado['data_comunicado_desligamento']
                
                # Converter data de desligamento se for string
                if isinstance(data_desligamento, str):
                    try:
                        data_desligamento = datetime.strptime(data_desligamento.split()[0], '%Y-%m-%d').date()
                    except:
                        continue
                
                # Verificar se o desligamento foi no mês de referência
                if data_desligamento.year == ano and data_desligamento.month == mes:
                    # Verificar data do comunicado
                    if data_comunicado and data_comunicado.upper() == 'OK':
                        # Se comunicado foi 'OK', considerar como comunicado no dia 15
                        if data_desligamento.day <= 15:
                            desligados_excluir.append(matricula)
                        else:
                            desligados_proporcional.append(matricula)
                    else:
                        # Se não há comunicado ou não é 'OK', excluir
                        desligados_excluir.append(matricula)
            
            # Aplicar exclusões
            if desligados_excluir:
                mask_excluir = df['matricula'].isin(desligados_excluir)
                df = df[~mask_excluir]
                logger.info(f"Funcionários desligados excluídos (comunicado até dia 15): {mask_excluir.sum()}")
            
            # Aplicar regras proporcionais
            if desligados_proporcional:
                mask_proporcional = df['matricula'].isin(desligados_proporcional)
                df_proporcional = df[mask_proporcional].copy()
                
                # Calcular dias proporcionais para desligados
                for idx in df_proporcional.index:
                    matricula = df_proporcional.loc[idx, 'matricula']
                    
                    # Encontrar data de desligamento
                    desligado_info = next((d for d in desligados_result if d['matricula'] == matricula), None)
                    if desligado_info:
                        data_desligamento = desligado_info['data_desligamento']
                        if isinstance(data_desligamento, str):
                            data_desligamento = datetime.strptime(data_desligamento.split()[0], '%Y-%m-%d').date()
                        
                        # Calcular dias proporcionais (do dia 1 até o dia do desligamento)
                        dias_proporcionais = data_desligamento.day
                        
                        # Aplicar proporção aos dias de VR
                        if 'dias_vr' in df_proporcional.columns:
                            df_proporcional.loc[idx, 'dias_vr'] = dias_proporcionais
                            df_proporcional.loc[idx, 'observacao'] = f'Desligamento proporcional - {dias_proporcionais} dias'
                
                # Atualizar DataFrame principal
                df.loc[mask_proporcional] = df_proporcional
                logger.info(f"Funcionários desligados com cálculo proporcional: {mask_proporcional.sum()}")
        
        except Exception as e:
            logger.error(f"Erro ao aplicar regras de desligamento via banco: {e}")
        
        return df
    
    def _apply_admission_rules_from_db(self, df: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
        """
        Aplica regras de admissão usando banco de dados
        
        Regras:
        - Funcionários admitidos no mês recebem VR proporcional aos dias trabalhados
        - Cálculo: do dia da admissão até o final do mês
        
        Args:
            df: DataFrame com funcionários
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            pd.DataFrame: DataFrame com regras de admissão aplicadas
        """
        try:
            from datetime import datetime, date
            import calendar
            
            # Obter dados de admissão do banco
            admissoes_query = """
            SELECT matricula, data_admissao 
            FROM admissoes 
            WHERE data_admissao IS NOT NULL
            """
            admissoes_result = self.db_manager.execute_query(admissoes_query)
            
            if not admissoes_result:
                logger.info("Nenhuma admissão encontrada")
                return df
            
            # Obter último dia do mês
            ultimo_dia_mes = calendar.monthrange(ano, mes)[1]
            
            # Aplicar regras de admissão
            for admissao in admissoes_result:
                matricula = admissao['matricula']
                data_admissao = admissao['data_admissao']
                
                # Converter data de admissão se for string
                if isinstance(data_admissao, str):
                    try:
                        data_admissao = datetime.strptime(data_admissao.split()[0], '%Y-%m-%d').date()
                    except:
                        continue
                
                # Verificar se a admissão foi no mês de referência
                if data_admissao.year == ano and data_admissao.month == mes:
                    # Verificar se funcionário está no DataFrame
                    mask = df['matricula'] == matricula
                    if mask.any():
                        # Calcular dias proporcionais (do dia da admissão até o final do mês)
                        dias_proporcionais = ultimo_dia_mes - data_admissao.day + 1
                        
                        # Aplicar proporção aos dias de VR
                        if 'dias_vr' in df.columns:
                            df.loc[mask, 'dias_vr'] = dias_proporcionais
                            df.loc[mask, 'observacao'] = f'Admissão proporcional - {dias_proporcionais} dias (admitido em {data_admissao.day}/{mes})'
                            
                            logger.info(f"Funcionário {matricula}: admissão em {data_admissao.day}/{mes}, {dias_proporcionais} dias de VR")
        
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
            df_resultado['valor_dia'] = df_resultado['sindicato'].map(valores_dict).fillna(0)
            df_resultado['vr_total'] = df_resultado['dias_vr'] * df_resultado['valor_dia']
            df_resultado['%_empresa'] = df_resultado['vr_total'] * self.company_percentage
            df_resultado['%_colaborador'] = df_resultado['vr_total'] * self.employee_percentage
            
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
            resumo = df_final.groupby('sindicato').agg({
                'matricula': 'count',
                'dias_vr': 'sum',
                'vr_total': 'sum',
                '%_empresa': 'sum',
                '%_colaborador': 'sum'
            }).round(2)
            
            resumo.columns = ['total_funcionarios', 'total_dias_uteis', 'total_vr', 'total_empresa', 'total_colaborador']
            resumo = resumo.reset_index()
            
            return resumo
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo por sindicato: {e}")
            return pd.DataFrame()
