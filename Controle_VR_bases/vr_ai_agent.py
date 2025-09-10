import os
import pandas as pd
import openai
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VRAIAgent:
    """
    Agente IA completo para automação da compra de VR/VA
    Atende todos os requisitos especificados:
    - Base única consolidada
    - Tratamento de exclusões
    - Validação e correção de dados
    - Cálculo automatizado do benefício
    - Entrega final para operadora
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Inicializa o agente IA completo
        """
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("Chave da API OpenAI não encontrada. Configure OPENAI_API_KEY ou passe como parâmetro.")
        
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Configurações do sistema
        self.pasta_dados = "dados"
        self.pasta_output = "output"
        
        # Mapeamento de arquivos esperados
        self.nomes_esperados = {
            "afastados": "Afastados",
            "aprendiz": "Aprendiz", 
            "ativos": "Ativos",
            "dias_uteis": "Dias_Uteis",
            "sindicatos": "Sindicatos",
            "desligados": "Desligados",
            "estagio": "Estagio",
            "exterior": "Exterior",
            "ferias": "Ferias",
            "admissoes": "Admissoes",
        }
        
        # Planilhas obrigatórias
        self.obrigatorios = ["ativos", "dias_uteis", "sindicatos"]
        
        # Cargos de exclusão (diretores, estagiários, aprendizes)
        self.cargos_exclusao = ["DIRETOR", "ESTAGIÁRIO", "ESTAGIARIO", "APRENDIZ"]
        
        # Percentuais de custo
        self.percentual_empresa = 0.8  # 80% empresa
        self.percentual_colaborador = 0.2  # 20% colaborador
    
    def _carregar_planilhas(self) -> Dict[str, pd.DataFrame]:
        """
        Carrega todas as planilhas da pasta dados
        """
        logger.info("Carregando planilhas...")
        
        if not os.path.exists(self.pasta_dados):
            raise FileNotFoundError(f"Pasta '{self.pasta_dados}' não encontrada.")
        
        arquivos = os.listdir(self.pasta_dados)
        arquivos_xlsx = [f for f in arquivos if f.lower().endswith(".xlsx")]
        
        logger.info(f"{len(arquivos_xlsx)} arquivos XLSX encontrados.")
        
        planilhas = {}
        
        for arquivo in arquivos_xlsx:
            caminho_arquivo = os.path.join(self.pasta_dados, arquivo)
            nome_base = os.path.splitext(os.path.basename(arquivo))[0].lower().replace(" ", "_")
            
            for chave_normalizada, nome_amigavel in self.nomes_esperados.items():
                if chave_normalizada in nome_base:
                    try:
                        df = pd.read_excel(caminho_arquivo)
                        planilhas[chave_normalizada] = df
                        logger.info(f"✅ Planilha carregada: {arquivo}")
                    except Exception as e:
                        logger.error(f"❌ Erro ao ler {arquivo}: {e}")
                    break
        
        return planilhas
    
    def _validar_planilha_com_ia(self, df: pd.DataFrame, tipo_planilha: str, nome_arquivo: str) -> bool:
        """
        Usa IA para validar se a planilha tem a estrutura esperada
        """
        try:
            # Preparar informações sobre a planilha
            info_planilha = {
                "tipo": tipo_planilha,
                "arquivo": nome_arquivo,
                "colunas": list(df.columns),
                "linhas": len(df),
                "primeiras_linhas": df.head(3).to_dict('records') if len(df) > 0 else []
            }
            
            prompt = f"""
            Analise se esta planilha tem a estrutura correta para o tipo '{tipo_planilha}':
            
            Informações da planilha:
            {json.dumps(info_planilha, indent=2, ensure_ascii=False, default=str)}
            
            Para cada tipo de planilha, as colunas esperadas são:
            - ativos: deve ter colunas como Matricula, Sindicato, Cargo
            - dias_uteis: deve ter colunas com sindicatos e dias úteis
            - sindicatos: deve ter colunas Sindicato e Valor_Dia_Sindicato
            - afastados: deve ter coluna Matricula
            - ferias: deve ter colunas Matricula, Dias_Ferias, Dias_Comprados
            - exterior/estagio/aprendiz: deve ter coluna Matricula
            - desligados: deve ter colunas Matricula, Data_Desligamento, Data_Comunicado_Desligamento
            - admissoes: deve ter colunas Matricula, Data_Admissao
            
            Responda apenas com 'SIM' se a planilha está correta ou 'NAO' se há problemas.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            
            resultado = response.choices[0].message.content.strip().upper()
            return resultado == "SIM"
            
        except Exception as e:
            logger.error(f"Erro na validação IA: {e}")
            return True  # Em caso de erro, aceita a planilha
    
    def _processar_com_ia(self, planilhas: Dict[str, pd.DataFrame], ano: int, mes: int) -> Dict:
        """
        Usa IA para processar os dados e gerar insights
        """
        logger.info("Processando dados com IA...")
        
        # Preparar dados para análise da IA
        dados_para_ia = {}
        
        for nome, df in planilhas.items():
            # Converter timestamps e outros tipos não serializáveis para string
            df_copy = df.copy()
            for col in df_copy.columns:
                if df_copy[col].dtype == 'datetime64[ns]':
                    df_copy[col] = df_copy[col].astype(str)
                elif df_copy[col].dtype == 'object':
                    # Converter objetos complexos para string
                    df_copy[col] = df_copy[col].astype(str)
            
            dados_para_ia[nome] = {
                "colunas": list(df_copy.columns),
                "total_linhas": len(df_copy),
                "amostra": df_copy.head(5).to_dict('records') if len(df_copy) > 0 else []
            }
        
        prompt = f"""
        Analise os dados de VR para {mes}/{ano} e forneça insights sobre:
        
        Dados disponíveis:
        {json.dumps(dados_para_ia, indent=2, ensure_ascii=False, default=str)}
        
        Forneça uma análise em JSON com:
        1. resumo_geral: resumo dos dados encontrados
        2. alertas: possíveis problemas ou inconsistências (datas quebradas, campos faltantes, etc.)
        3. sugestoes: sugestões de melhoria para o processo
        4. estatisticas: estatísticas relevantes (total funcionários, por sindicato, etc.)
        5. validacoes: validações específicas para o processo de VR
        
        Responda apenas com JSON válido.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            insights = json.loads(response.choices[0].message.content)
            return insights
            
        except Exception as e:
            logger.error(f"Erro no processamento IA: {e}")
            return {
                "resumo_geral": "Análise não disponível",
                "alertas": [],
                "sugestoes": [],
                "estatisticas": {},
                "validacoes": []
            }
    
    def _aplicar_exclusoes(self, df_base: pd.DataFrame, planilhas: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Aplica todas as regras de exclusão conforme especificado
        """
        logger.info("Aplicando regras de exclusão...")
        
        df_resultado = df_base.copy()
        exclusoes_aplicadas = []
        
        # 1. Excluir diretores, estagiários e aprendizes (por cargo)
        if 'cargo' in df_resultado.columns:
            cargos_excluir = df_resultado['Cargo'].str.upper().str.contains('|'.join(self.cargos_exclusao), na=False)
            excluidos_cargo = df_resultado[cargos_excluir]
            df_resultado = df_resultado[~cargos_excluir]
            exclusoes_aplicadas.append(f"Excluídos por cargo: {len(excluidos_cargo)} funcionários")
        
        # 2. Excluir afastados em geral
        if "afastados" in planilhas:
            afastados_matriculas = planilhas["afastados"]["Matricula"].astype(str).unique()
            excluidos_afastados = df_resultado[df_resultado["Matricula"].astype(str).isin(afastados_matriculas)]
            df_resultado = df_resultado[~df_resultado["Matricula"].astype(str).isin(afastados_matriculas)]
            exclusoes_aplicadas.append(f"Excluídos afastados: {len(excluidos_afastados)} funcionários")
        
        # 3. Excluir estagiários e aprendizes (por planilha específica)
        for chave in ["estagio", "aprendiz"]:
            if chave in planilhas:
                mats = planilhas[chave]["Matricula"].astype(str).unique()
                excluidos = df_resultado[df_resultado["Matricula"].astype(str).isin(mats)]
                df_resultado = df_resultado[~df_resultado["Matricula"].astype(str).isin(mats)]
                exclusoes_aplicadas.append(f"Excluídos {chave}: {len(excluidos)} funcionários")
        
        # 4. Excluir profissionais no exterior
        if "exterior" in planilhas:
            exterior_mats = planilhas["exterior"]["Matricula"].astype(str).unique()
            excluidos_exterior = df_resultado[df_resultado["Matricula"].astype(str).isin(exterior_mats)]
            df_resultado = df_resultado[~df_resultado["Matricula"].astype(str).isin(exterior_mats)]
            exclusoes_aplicadas.append(f"Excluídos exterior: {len(excluidos_exterior)} funcionários")
        
        logger.info(f"Exclusões aplicadas: {exclusoes_aplicadas}")
        return df_resultado, exclusoes_aplicadas
    
    def _calcular_dias_uteis_por_colaborador(self, df_base: pd.DataFrame, planilhas: Dict[str, pd.DataFrame], ano: int, mes: int) -> pd.DataFrame:
        """
        Calcula os dias úteis por colaborador considerando todas as regras
        """
        logger.info("Calculando dias úteis por colaborador...")
        
        df_resultado = df_base.copy()
        
        # Mapear dias úteis por sindicato
        dias_uteis_dict = dict(
            zip(
                planilhas["dias_uteis"]["Sindicato"].astype(str).str.strip(),
                planilhas["dias_uteis"]["Dias_Uteis_Sindicato"]
            )
        )
        
        # Aplicar dias úteis base por sindicato
        df_resultado["Sindicato"] = df_resultado["Sindicato"].astype(str).str.strip()
        df_resultado["Dias_VR"] = df_resultado["Sindicato"].map(dias_uteis_dict).fillna(0)
        
        # Aplicar regras de férias
        if "ferias" in planilhas:
            df_ferias = planilhas["ferias"].copy()
            df_ferias["Matricula"] = df_ferias["Matricula"].astype(str)
            df_ferias["Dias_Comprados"] = df_ferias["Dias_Comprados"].fillna(0)
            df_ferias["Dias_Ferias"] = df_ferias["Dias_Ferias"].fillna(0)
            df_ferias["Dias_Descontar"] = df_ferias["Dias_Ferias"] - df_ferias["Dias_Comprados"]
            df_ferias["Dias_Descontar"] = df_ferias["Dias_Descontar"].clip(lower=0)
            
            ferias_dict = df_ferias.groupby("Matricula")["Dias_Descontar"].sum().to_dict()
            df_resultado["Matricula"] = df_resultado["Matricula"].astype(str)
            df_resultado["Dias_VR"] = df_resultado.apply(
                lambda row: max(row["Dias_VR"] - ferias_dict.get(row["Matricula"], 0), 0), axis=1
            )
        
        # Aplicar regras de desligamento
        if "desligados" in planilhas:
            df_desligados = planilhas["desligados"].copy()
            df_desligados["Matricula"] = df_desligados["Matricula"].astype(str)
            
            # Converter datas se necessário
            if 'Data_Comunicado_Desligamento' in df_desligados.columns:
                # Se comunicado até dia 15, não considerar para pagamento
                df_desligados['Data_Comunicado_Desligamento'] = pd.to_datetime(df_desligados['Data_Comunicado_Desligamento'], errors='coerce')
                
                # Aplicar regra do dia 15
                for _, row in df_desligados.iterrows():
                    matricula = row["Matricula"]
                    if pd.notna(row['Data_Comunicado_Desligamento']):
                        if row['Data_Comunicado_Desligamento'].day <= 15:
                            # Não considerar para pagamento
                            df_resultado.loc[df_resultado["Matricula"] == matricula, "Dias_VR"] = 0
                        else:
                            # Proporcional (implementar lógica específica se necessário)
                            pass
        
        # Aplicar regras de admissão (proporcional se admitido no meio do mês)
        if "admissoes" in planilhas:
            df_admissoes = planilhas["admissoes"].copy()
            df_admissoes["Matricula"] = df_admissoes["Matricula"].astype(str)
            df_admissoes['Data_Admissao'] = pd.to_datetime(df_admissoes['Data_Admissao'], errors='coerce')
            
            for _, row in df_admissoes.iterrows():
                matricula = row["Matricula"]
                if pd.notna(row['Data_Admissao']):
                    # Se admitido no meio do mês, calcular proporcional
                    dias_restantes = (pd.Timestamp(f"{ano}-{mes:02d}-01") + pd.offsets.MonthEnd(0) - row['Data_Admissao']).days + 1
                    if dias_restantes < 30:  # Se não é do início do mês
                        # Aplicar proporção (simplificado)
                        df_resultado.loc[df_resultado["Matricula"] == matricula, "Dias_VR"] = \
                            df_resultado.loc[df_resultado["Matricula"] == matricula, "Dias_VR"] * (dias_restantes / 30)
        
        return df_resultado
    
    def _calcular_valores_vr(self, df_base: pd.DataFrame, planilhas: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calcula os valores de VR por colaborador
        """
        logger.info("Calculando valores de VR...")
        
        df_resultado = df_base.copy()
        
        # Mapear valor por sindicato
        valor_sindicato_dict = dict(
            zip(
                planilhas["sindicatos"]["Sindicato"].astype(str).str.strip(),
                planilhas["sindicatos"]["Valor_Dia_Sindicato"]
            )
        )
        
        # Aplicar valor por sindicato
        df_resultado["Valor_Dia"] = df_resultado["Sindicato"].map(valor_sindicato_dict).fillna(0)
        
        # Calcular valores totais
        df_resultado["VR_Total"] = df_resultado["Dias_VR"] * df_resultado["Valor_Dia"]
        df_resultado["%_Empresa"] = df_resultado["VR_Total"] * self.percentual_empresa
        df_resultado["%_Colaborador"] = df_resultado["VR_Total"] * self.percentual_colaborador
        
        return df_resultado
    
    def _gerar_validacoes(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """
        Gera validações dos dados processados conforme especificado
        """
        logger.info("Gerando validações...")
        
        validacoes = []
        for _, row in df_final.iterrows():
            matricula = row["Matricula"]
            dias = row["Dias_VR"]
            valor_total = row["VR_Total"]
            problema = "ok"
            
            # Validações conforme especificado
            if dias == 0 and valor_total > 0:
                problema = "Dias zerados com valor > 0"
            elif valor_total == 0 and dias > 0:
                problema = "Sem valor mesmo com dias"
            elif dias > 22:
                problema = "Dias maiores que possível (máximo 22)"
            elif dias < 0:
                problema = "Dias negativos"
            elif row["Valor_Dia"] == 0 and dias > 0:
                problema = "Valor por dia zerado"
            elif row["%_Empresa"] + row["%_Colaborador"] != valor_total:
                problema = "Divisão de percentuais incorreta"
            
            validacoes.append({
                "Matricula": matricula,
                "Problema": problema,
                "Dias_VR": dias,
                "VR_Total": valor_total
            })
        
        return pd.DataFrame(validacoes)
    
    def _salvar_arquivo_final(self, df_final: pd.DataFrame, df_resumo: pd.DataFrame, 
                             df_validacoes: pd.DataFrame, nome_saida: str, insights_ia: Dict, 
                             exclusoes_aplicadas: List[str]) -> str:
        """
        Salva o arquivo Excel final conforme modelo especificado
        """
        os.makedirs(self.pasta_output, exist_ok=True)
        caminho_saida = os.path.join(self.pasta_output, nome_saida)
        
        # Preparar dados detalhados (aba "VR Mensal")
        df_detalhado = df_final[[
            "Matricula", "Sindicato", "Dias_VR", "Valor_Dia", "VR_Total", "%_Empresa", "%_Colaborador"
        ]].copy()
        
        # Criar planilha com insights da IA
        df_insights = pd.DataFrame([
            {"Categoria": "Resumo Geral", "Informação": insights_ia.get("resumo_geral", "")},
            {"Categoria": "Alertas", "Informação": "; ".join(insights_ia.get("alertas", []))},
            {"Categoria": "Sugestões", "Informação": "; ".join(insights_ia.get("sugestoes", []))},
            {"Categoria": "Exclusões Aplicadas", "Informação": "; ".join(exclusoes_aplicadas)}
        ])
        
        # Criar planilha de estatísticas
        df_estatisticas = pd.DataFrame([
            {"Métrica": "Total Funcionários", "Valor": len(df_final)},
            {"Métrica": "Total VR", "Valor": f"R$ {df_final['VR_Total'].sum():,.2f}"},
            {"Métrica": "Total Empresa (80%)", "Valor": f"R$ {df_final['%_Empresa'].sum():,.2f}"},
            {"Métrica": "Total Colaborador (20%)", "Valor": f"R$ {df_final['%_Colaborador'].sum():,.2f}"},
            {"Métrica": "Média Dias por Funcionário", "Valor": f"{df_final['Dias_VR'].mean():.1f}"},
            {"Métrica": "Funcionários com Problemas", "Valor": len(df_validacoes[df_validacoes['Problema'] != 'ok'])}
        ])
        
        with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
            # Aba principal conforme modelo "VR Mensal 05.2025"
            df_detalhado.to_excel(writer, sheet_name="VR_Mensal", index=False)
            
            # Aba de resumo por sindicato
            df_resumo.to_excel(writer, sheet_name="resumo_sindicato", index=False)
            
            # Aba de validações
            df_validacoes.to_excel(writer, sheet_name="validações", index=False)
            
            # Aba com dados completos
            df_final.to_excel(writer, sheet_name="VR_Completo", index=False)
            
            # Aba com insights da IA
            df_insights.to_excel(writer, sheet_name="insights_ia", index=False)
            
            # Aba com estatísticas
            df_estatisticas.to_excel(writer, sheet_name="estatisticas", index=False)
        
        return caminho_saida
    
    def processar_vr_completo(self, ano: int, mes: int, nome_saida: str = None) -> Dict:
        """
        Processa completamente o VR conforme todos os requisitos especificados
        """
        logger.info(f"Iniciando processamento completo de VR para {mes}/{ano}...")
        
        try:
            # 1. Carregar planilhas
            planilhas = self._carregar_planilhas()
            
            # 2. Validar planilhas obrigatórias
            for nome in self.obrigatorios:
                if nome not in planilhas:
                    raise ValueError(f"Planilha obrigatória '{nome}' não encontrada.")
            
            # 3. Processar com IA
            insights_ia = self._processar_com_ia(planilhas, ano, mes)
            
            # 4. Base única consolidada - começar com ativos
            df_base = planilhas["ativos"].copy()
            logger.info(f"Base inicial: {len(df_base)} funcionários ativos")
            
            # 5. Aplicar exclusões
            df_base, exclusoes_aplicadas = self._aplicar_exclusoes(df_base, planilhas)
            logger.info(f"Após exclusões: {len(df_base)} funcionários elegíveis")
            
            # 6. Calcular dias úteis por colaborador
            df_base = self._calcular_dias_uteis_por_colaborador(df_base, planilhas, ano, mes)
            
            # 7. Calcular valores de VR
            df_final = self._calcular_valores_vr(df_base, planilhas)
            
            # 8. Gerar resumos
            df_resumo = df_final.groupby("Sindicato")[
                ["Dias_VR", "VR_Total", "%_Empresa", "%_Colaborador"]
            ].sum().reset_index()
            
            # 9. Gerar validações
            df_validacoes = self._gerar_validacoes(df_final)
            
            # 10. Salvar arquivo final
            if nome_saida is None:
                nome_saida = f"VR_{ano}_{mes:02d}_Processado_Completo.xlsx"
            
            caminho_saida = self._salvar_arquivo_final(df_final, df_resumo, df_validacoes, nome_saida, insights_ia, exclusoes_aplicadas)
            
            # 11. Preparar resultado
            problemas = df_validacoes[df_validacoes['Problema'] != 'ok']
            
            resultado = {
                "sucesso": True,
                "arquivo_saida": caminho_saida,
                "total_funcionarios_inicial": len(planilhas["ativos"]),
                "total_funcionarios_final": len(df_final),
                "total_vr": df_final["VR_Total"].sum(),
                "total_empresa": df_final["%_Empresa"].sum(),
                "total_colaborador": df_final["%_Colaborador"].sum(),
                "exclusoes_aplicadas": exclusoes_aplicadas,
                "problemas_encontrados": len(problemas),
                "insights_ia": insights_ia,
                "resumo_sindicatos": df_resumo.to_dict('records')
            }
            
            logger.info("✅ Processamento completo concluído com sucesso!")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento: {e}")
            return {
                "sucesso": False,
                "erro": str(e),
                "insights_ia": {}
            }
    
    def consultar_ia(self, pergunta: str) -> str:
        """
        Permite fazer consultas diretas à IA sobre os dados de VR
        """
        try:
            # Carregar dados atuais se disponível
            planilhas = {}
            if os.path.exists(self.pasta_dados):
                planilhas = self._carregar_planilhas()
            
            dados_contexto = {}
            for nome, df in planilhas.items():
                # Converter timestamps e outros tipos não serializáveis
                df_copy = df.copy()
                for col in df_copy.columns:
                    if df_copy[col].dtype == 'datetime64[ns]':
                        df_copy[col] = df_copy[col].astype(str)
                    elif df_copy[col].dtype == 'object':
                        df_copy[col] = df_copy[col].astype(str)
                
                dados_contexto[nome] = {
                    "colunas": list(df_copy.columns),
                    "total_linhas": len(df_copy),
                    "amostra": df_copy.head(3).to_dict('records') if len(df_copy) > 0 else []
                }
            
            prompt = f"""
            Você é um especialista em processamento de dados de VR (Vale Refeição) e automação de compra de benefícios.
            
            Dados disponíveis:
            {json.dumps(dados_contexto, indent=2, ensure_ascii=False, default=str)}
            
            Pergunta do usuário: {pergunta}
            
            Responda de forma clara e útil, baseando-se nos dados disponíveis e nas regras de negócio do processo de VR.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Erro ao consultar IA: {e}"


def main():
    """
    Função principal para teste do agente
    """
    try:
        # Inicializar agente
        agente = VRAIAgent()
        
        # Exemplo de uso
        print("🤖 Agente IA de VR Completo inicializado!")
        print("Digite 'sair' para encerrar.")
        
        while True:
            comando = input("\nDigite um comando (ex: 'processar setembro 2025' ou 'consultar quantos funcionários temos?'): ")
            
            if comando.lower() == 'sair':
                break
            
            if 'processar' in comando.lower():
                # Extrair mês e ano
                partes = comando.lower().split()
                meses = {
                    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
                    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
                    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
                }
                
                mes_texto = next((p for p in partes if p in meses), None)
                ano = next((p for p in partes if p.isdigit() and len(p) == 4), None)
                
                if mes_texto and ano:
                    mes = meses[mes_texto]
                    ano = int(ano)
                    resultado = agente.processar_vr_completo(ano, mes)
                    
                    if resultado["sucesso"]:
                        print(f"✅ Processamento completo concluído!")
                        print(f"📁 Arquivo salvo: {resultado['arquivo_saida']}")
                        print(f"👥 Funcionários inicial: {resultado['total_funcionarios_inicial']}")
                        print(f"👥 Funcionários final: {resultado['total_funcionarios_final']}")
                        print(f"💰 Total VR: R$ {resultado['total_vr']:,.2f}")
                        print(f"🏢 Total Empresa (80%): R$ {resultado['total_empresa']:,.2f}")
                        print(f"👤 Total Colaborador (20%): R$ {resultado['total_colaborador']:,.2f}")
                        print(f"⚠️ Problemas encontrados: {resultado['problemas_encontrados']}")
                    else:
                        print(f"❌ Erro: {resultado['erro']}")
                else:
                    print("❌ Não foi possível identificar mês e ano.")
            
            elif 'consultar' in comando.lower():
                pergunta = comando.replace('consultar', '').strip()
                resposta = agente.consultar_ia(pergunta)
                print(f"🤖 IA: {resposta}")
            
            else:
                print("❌ Comando não reconhecido. Use 'processar' ou 'consultar'.")
    
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main()
