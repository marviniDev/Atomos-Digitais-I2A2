"""
Módulo para carregamento de planilhas Excel com integração ao banco de dados - CORRIGIDO
"""
import pandas as pd
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import config
from database import VRDatabaseManager

logger = logging.getLogger(__name__)

class ExcelLoader:
    """Classe responsável por carregar planilhas Excel e integrar com banco de dados"""
    
    def __init__(self, db_manager: Optional[VRDatabaseManager] = None):
        self.data_folder = config.get_data_path()
        self.db_manager = db_manager
        
        # Mapeamento corrigido baseado nos arquivos reais encontrados
        self.file_mapping = {
            "ativos": ["ATIVOS"],
            "afastados": ["AFASTAMENTOS"],
            "aprendiz": ["APRENDIZ"],
            "desligados": ["DESLIGADOS"],
            "estagio": ["ESTÁGIO", "ESTAGIO"],
            "exterior": ["EXTERIOR"],
            "ferias": ["FÉRIAS", "FERIAS"],
            "admissoes": ["ADMISSÃO", "ADMISSAO"],
            "sindicatos": ["Base sindicato", "sindicato"],
            "dias_uteis": ["Base dias", "dias uteis", "dias_uteis"]
        }
    
    def load_all_spreadsheets(self, load_to_db: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Carrega todas as planilhas da pasta de dados e opcionalmente salva no banco
        
        Args:
            load_to_db: Se True, carrega os dados para o banco de dados
            
        Returns:
            Dict[str, pd.DataFrame]: Dicionário com nome da planilha e DataFrame
        """
        logger.info("Carregando planilhas...")
        
        if not self.data_folder.exists():
            raise FileNotFoundError(f"Pasta de dados não encontrada: {self.data_folder}")
        
        # Buscar arquivos Excel
        excel_files = list(self.data_folder.glob("*.xlsx"))
        logger.info(f"Encontrados {len(excel_files)} arquivos XLSX")
        
        spreadsheets = {}
        
        for file_path in excel_files:
            try:
                # Identificar tipo de planilha
                planilha_type = self._identify_spreadsheet_type(file_path.name)
                
                if planilha_type:
                    # Carregar planilha com tratamento específico
                    df = self._load_and_clean_spreadsheet(file_path, planilha_type)
                    
                    if df is not None and not df.empty:
                        spreadsheets[planilha_type] = df
                        logger.info(f"✅ Planilha carregada: {file_path.name} -> {planilha_type} ({len(df)} linhas)")
                    else:
                        logger.warning(f"⚠️ Planilha vazia ou com problemas: {file_path.name}")
                else:
                    logger.warning(f"⚠️ Arquivo não reconhecido: {file_path.name}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao carregar {file_path.name}: {e}")
        
        # Carregar dados para o banco se solicitado e disponível
        if load_to_db and self.db_manager and spreadsheets:
            try:
                logger.info("Carregando dados para o banco de dados...")
                self.db_manager.load_spreadsheet_data(spreadsheets)
                logger.info("✅ Dados carregados no banco de dados com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar dados no banco: {e}")
                raise
        
        return spreadsheets
    
    def _identify_spreadsheet_type(self, filename: str) -> Optional[str]:
        """
        Identifica o tipo de planilha baseado no nome do arquivo
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            str: Tipo da planilha ou None se não reconhecida
        """
        filename_clean = filename.replace(".xlsx", "").upper()
        
        # Mapear nome do arquivo para tipo
        for planilha_type, possible_names in self.file_mapping.items():
            for possible_name in possible_names:
                if possible_name.upper() in filename_clean:
                    return planilha_type
        
        return None
    
    def _load_and_clean_spreadsheet(self, file_path: Path, planilha_type: str) -> Optional[pd.DataFrame]:
        """
        Carrega e limpa uma planilha específica
        
        Args:
            file_path: Caminho do arquivo
            planilha_type: Tipo da planilha
            
        Returns:
            pd.DataFrame: DataFrame limpo ou None se houver erro
        """
        try:
            # Ler todas as abas primeiro para identificar a principal
            xl_file = pd.ExcelFile(file_path)
            
            # Escolher a aba principal
            main_sheet = self._get_main_sheet(xl_file, planilha_type)
            
            # Carregar dados
            df = pd.read_excel(file_path, sheet_name=main_sheet)
            
            # Limpar e tratar dados
            df_clean = self._clean_dataframe(df, planilha_type)
            
            return df_clean
            
        except Exception as e:
            logger.error(f"Erro ao processar {file_path.name}: {e}")
            return None
    
    def _get_main_sheet(self, xl_file, planilha_type: str) -> str:
        """
        Identifica a aba principal da planilha
        
        Args:
            xl_file: Arquivo Excel
            planilha_type: Tipo da planilha
            
        Returns:
            str: Nome da aba principal
        """
        sheets = xl_file.sheet_names
        
        # Se só há uma aba, usar ela
        if len(sheets) == 1:
            return sheets[0]
        
        # Procurar por abas com nomes relevantes
        for sheet in sheets:
            sheet_upper = sheet.upper()
            if planilha_type.upper() in sheet_upper or any(keyword in sheet_upper for keyword in ['DADOS', 'PLANILHA1', 'SHEET1']):
                return sheet
        
        # Se não encontrar, usar a primeira
        return sheets[0]
    
    def _clean_dataframe(self, df: pd.DataFrame, planilha_type: str) -> pd.DataFrame:
        """
        Limpa e padroniza um DataFrame
        
        Args:
            df: DataFrame original
            planilha_type: Tipo da planilha
            
        Returns:
            pd.DataFrame: DataFrame limpo
        """
        if df.empty:
            return df
        
        # Remover linhas completamente vazias
        df = df.dropna(how='all')
        
        # Limpar nomes das colunas
        df.columns = [self._clean_column_name(str(col)) for col in df.columns]
        
        # Tratamentos específicos por tipo de planilha
        if planilha_type == "ativos":
            df = self._clean_ativos(df)
        elif planilha_type == "sindicatos":
            df = self._clean_sindicatos(df)
        elif planilha_type == "dias_uteis":
            df = self._clean_dias_uteis(df)
        elif planilha_type == "desligados":
            df = self._clean_desligados(df)
        elif planilha_type == "ferias":
            df = self._clean_ferias(df)
        elif planilha_type == "admissoes":
            df = self._clean_admissoes(df)
        elif planilha_type == "afastados":
            df = self._clean_afastados(df)
        elif planilha_type == "estagio":
            df = self._clean_estagio(df)
        elif planilha_type == "aprendiz":
            df = self._clean_aprendiz(df)
        elif planilha_type == "exterior":
            df = self._clean_exterior(df)
        
        # Remover linhas vazias novamente após limpeza
        df = df.dropna(how='all')
        
        # Aplicar mapeamento de sindicatos se for planilha de ativos
        if planilha_type == 'ativos':
            df = self._apply_sindicato_mapping(df)
        
        return df
    
    def _clean_column_name(self, col_name: str) -> str:
        """
        Limpa nome de coluna removendo caracteres especiais e padronizando
        
        Args:
            col_name: Nome original da coluna
            
        Returns:
            str: Nome limpo da coluna
        """
        # Remover caracteres especiais (incluindo \xa0)
        clean_name = re.sub(r'[^\w\s]', ' ', str(col_name))
        # Remover espaços extras e converter para minúsculas
        clean_name = re.sub(r'\s+', ' ', clean_name).strip().lower()
        # Substituir espaços por underscores
        clean_name = clean_name.replace(' ', '_')
        # Remover underscores múltiplos
        clean_name = re.sub(r'_+', '_', clean_name)
        # Remover underscores no início e fim
        clean_name = clean_name.strip('_')
        
        return clean_name
    
    def _clean_ativos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados da planilha de funcionários ativos"""
        # Renomear colunas para padrão esperado
        column_mapping = {
            'matricula': 'matricula',
            'empresa': 'empresa', 
            'titulo_do_cargo': 'cargo',
            'desc_situacao': 'situacao',
            'sindicato': 'sindicato'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Filtrar apenas linhas com matrícula válida
        if 'matricula' in df.columns:
            df = df[df['matricula'].notna()]
            df = df[df['matricula'] != '']
        
        return df
    
    def _clean_sindicatos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados da planilha de sindicatos"""
        # Identificar colunas relevantes
        cols = df.columns.tolist()
        
        # Primeira coluna geralmente é o sindicato, segunda o valor
        if len(cols) >= 2:
            df = df.rename(columns={
                cols[0]: 'sindicato',
                cols[1]: 'valor_dia_sindicato'
            })
        
        # Filtrar apenas linhas com dados válidos
        df = df[df['sindicato'].notna()]
        df = df[df['sindicato'] != '']
        df = df[~df['sindicato'].str.upper().str.contains('ESTADO|SINDICADO', na=False)]
        
        return df
    
    def _clean_dias_uteis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados da planilha de dias úteis"""
        cols = df.columns.tolist()
        
        # Primeira coluna é sindicato, segunda é dias úteis
        if len(cols) >= 2:
            df = df.rename(columns={
                cols[0]: 'sindicato',
                cols[1]: 'dias_uteis_sindicato'
            })
        
        # Filtrar apenas linhas com dados válidos
        df = df[df['sindicato'].notna()]
        df = df[df['sindicato'] != '']
        df = df[~df['sindicato'].str.upper().str.contains('SINDICADO|DIAS', na=False)]
        
        return df
    
    def _clean_desligados(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados da planilha de desligados"""
        # Mapear colunas baseado no conteúdo real
        column_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'matricula' in col_lower:
                column_mapping[col] = 'matricula'
            elif 'demiss' in col_lower or 'desligamento' in col_lower:
                column_mapping[col] = 'data_desligamento'
            elif 'comunicado' in col_lower:
                column_mapping[col] = 'data_comunicado_desligamento'
        
        df = df.rename(columns=column_mapping)
        
        if 'matricula' in df.columns:
            df = df[df['matricula'].notna()]
        
        return df

    

    def _clean_ferias(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados da planilha de férias"""
        column_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'matricula' in col_lower:
                column_mapping[col] = 'matricula'
            elif 'situacao' in col_lower or 'situação' in col_lower:
                column_mapping[col] = 'situacao'
            elif 'ferias' in col_lower or 'férias' in col_lower:
                column_mapping[col] = 'dias_ferias'
        
        df = df.rename(columns=column_mapping)
        
        if 'matricula' in df.columns:
            df = df[df['matricula'].notna()]
        
        return df

    

    def _clean_admissoes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados da planilha de admissões"""
        column_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'matricula' in col_lower:
                column_mapping[col] = 'matricula'
            elif 'admiss' in col_lower:
                column_mapping[col] = 'data_admissao'
            elif 'cargo' in col_lower:
                column_mapping[col] = 'cargo'
        
        df = df.rename(columns=column_mapping)
        
        if 'matricula' in df.columns:
            df = df[df['matricula'].notna()]
        
        # Remover colunas extras, manter apenas as esperadas
        expected_cols = ['matricula', 'data_admissao', 'cargo']
        df = df[[col for col in expected_cols if col in df.columns]]
        
        return df

    def _clean_afastados(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados da planilha de afastados"""
        column_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'matricula' in col_lower:
                column_mapping[col] = 'matricula'
            elif 'situacao' in col_lower or 'situação' in col_lower:
                column_mapping[col] = 'afastamento_tipo'
        
        df = df.rename(columns=column_mapping)
        
        if 'matricula' in df.columns:
            df = df[df['matricula'].notna()]
        
        # Remover colunas extras
        expected_cols = ['matricula', 'afastamento_tipo']
        df = df[[col for col in expected_cols if col in df.columns]]
        
        return df

    

    def _clean_estagio(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados da planilha de estágio"""
        column_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'matricula' in col_lower:
                column_mapping[col] = 'matricula'
            elif 'cargo' in col_lower or 'titulo' in col_lower:
                column_mapping[col] = 'titulo_do_cargo'
        
        df = df.rename(columns=column_mapping)
        
        if 'matricula' in df.columns:
            df = df[df['matricula'].notna()]
        
        # Remover colunas extras
        expected_cols = ['matricula', 'titulo_do_cargo']
        df = df[[col for col in expected_cols if col in df.columns]]
        
        return df

    

    def _clean_aprendiz(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados da planilha de aprendiz"""
        column_mapping = {
            'matricula': 'matricula',
            'titulo_do_cargo': 'titulo_do_cargo'
        }
        
        df = df.rename(columns=column_mapping)
        
        if 'matricula' in df.columns:
            df = df[df['matricula'].notna()]
        
        return df
    
    def _clean_exterior(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados da planilha de exterior"""
        cols = df.columns.tolist()
        
        # Mapear colunas baseado na posição
        if len(cols) >= 2:
            new_mapping = {
                cols[0]: 'matricula',
                cols[1]: 'valor'
            }
            if len(cols) >= 3:
                new_mapping[cols[2]] = 'observacao'
            
            df = df.rename(columns=new_mapping)
        
        if 'matricula' in df.columns:
            df = df[df['matricula'].notna()]
        
        return df
    
    def validate_required_files(self, spreadsheets: Dict[str, pd.DataFrame]) -> List[str]:
        """
        Valida se todas as planilhas obrigatórias estão presentes
        
        Args:
            spreadsheets: Dicionário com planilhas carregadas
            
        Returns:
            List[str]: Lista de arquivos obrigatórios ausentes
        """
        required_files = ["ativos", "sindicatos", "dias_uteis"]
        missing_files = []
        
        for required_file in required_files:
            if required_file not in spreadsheets:
                missing_files.append(required_file)
        
        if missing_files:
            logger.error(f"❌ Planilhas obrigatórias ausentes: {missing_files}")
        else:
            logger.info("✅ Todas as planilhas obrigatórias estão presentes")
        
        return missing_files
    
    def get_spreadsheet_info(self, df: pd.DataFrame, name: str) -> Dict:
        """
        Obtém informações básicas sobre uma planilha
        
        Args:
            df: DataFrame da planilha
            name: Nome da planilha
            
        Returns:
            Dict: Informações da planilha
        """
        return {
            "name": name,
            "rows": len(df),
            "columns": list(df.columns),
            "has_data": len(df) > 0,
            "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
        }
    
    def get_database_info(self) -> Optional[Dict]:
        """
        Obtém informações do banco de dados se disponível
        
        Returns:
            Dict: Informações do banco de dados ou None se não disponível
        """
        if not self.db_manager:
            return None
        
        try:
            schema_info = self.db_manager.get_schema_info()
            return {
                "tables": list(schema_info.keys()),
                "schema": schema_info,
                "total_tables": len(schema_info)
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações do banco: {e}")
            return None

    def _apply_sindicato_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica mapeamento de sindicatos para padronizar nomes
        
        Args:
            df: DataFrame com dados de funcionários
            
        Returns:
            pd.DataFrame: DataFrame com sindicatos mapeados
        """
        if 'sindicato' not in df.columns:
            return df
        
        # Mapeamento de sindicatos (nomes completos -> nomes simplificados)
        mapeamento_sindicatos = {
            'SINDPD RJ - SINDICATO PROFISSIONAIS DE PROC DADOS DO RIO DE JANEIRO': 'Rio de Janeiro',
            'SINDPD SP - SIND.TRAB.EM PROC DADOS E EMPR.EMPRESAS PROC DADOS ESTADO DE SP.': 'São Paulo',
            'SINDPPD RS - SINDICATO DOS TRAB. EM PROC. DE DADOS RIO GRANDE DO SUL': 'Rio Grande do Sul',
            'SITEPD PR - SIND DOS TRAB EM EMPR PRIVADAS DE PROC DE DADOS DE CURITIBA E REGIAO METROPOLITANA': 'Paraná'
        }
        
        # Aplicar mapeamento
        df['sindicato'] = df['sindicato'].map(mapeamento_sindicatos).fillna(df['sindicato'])
        
        return df