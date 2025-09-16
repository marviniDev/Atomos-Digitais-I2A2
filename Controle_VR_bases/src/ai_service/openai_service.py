"""
Serviço OpenAI Refatorado - Arquitetura Limpa
"""
import logging

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    logger.error("OpenAI não disponível. Instale com: pip install openai")
    OPENAI_AVAILABLE = False
    raise ImportError("OpenAI é obrigatório. Instale com: pip install openai")

class OpenAIService:
    """
    Serviço OpenAI refatorado com arquitetura limpa
    
    Responsabilidades:
    - Gerenciar conexão com OpenAI
    - Processar dados com IA
    - Consultas diretas à IA
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa o serviço OpenAI
        
        Args:
            api_key: Chave da API OpenAI (obrigatória)
        """
        if not api_key:
            raise ValueError("❌ API Key da OpenAI é obrigatória!")
        
        self.api_key = api_key
        
        # Inicializar cliente OpenAI
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("✅ Cliente OpenAI inicializado")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar cliente OpenAI: {e}")
            raise ValueError(f"Erro ao inicializar OpenAI: {e}")
    
    def process_data_with_ai(self, spreadsheets: dict, ano: int, mes: int) -> dict:
        """
        Processa dados com IA para gerar insights
        
        Args:
            spreadsheets: Dicionário com planilhas carregadas
            ano: Ano de referência
            mes: Mês de referência
            
        Returns:
            dict: Insights gerados pela IA
        """
        try:
            # Preparar dados para análise
            dados_resumo = {}
            for nome, df in spreadsheets.items():
                dados_resumo[nome] = {
                    "total_registros": len(df),
                    "colunas": list(df.columns),
                    "amostra": df.head(3).to_dict('records') if len(df) > 0 else []
                }
            
            # Prompt para análise
            prompt = f"""
            Analise os seguintes dados de VR/VA para {mes}/{ano}:
            
            {dados_resumo}
            
            Forneça:
            1. Resumo geral dos dados
            2. Alertas importantes
            3. Sugestões de melhoria
            
            Formato de resposta em JSON:
            {{
                "resumo_geral": "texto do resumo",
                "alertas": ["alerta1", "alerta2"],
                "sugestoes": ["sugestao1", "sugestao2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um especialista em análise de dados de VR/VA."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            
            # Processar resposta
            content = response.choices[0].message.content
            
            # Tentar extrair JSON da resposta
            import json
            try:
                # Procurar por JSON na resposta
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    return json.loads(json_str)
                else:
                    # Se não encontrar JSON, retornar resposta formatada
                    return {
                        "resumo_geral": content,
                        "alertas": [],
                        "sugestoes": []
                    }
            except json.JSONDecodeError:
                return {
                    "resumo_geral": content,
                    "alertas": [],
                    "sugestoes": []
                }
                
        except Exception as e:
            logger.error(f"Erro no processamento IA: {e}")
            return {
                "resumo_geral": f"Erro na análise de IA: {e}",
                "alertas": [],
                "sugestoes": []
            }
    
    def consult_ai(self, pergunta: str, context_data: dict = None) -> str:
        """
        Permite fazer consultas diretas à IA
        
        Args:
            pergunta: Pergunta do usuário
            context_data: Dados de contexto (opcional)
            
        Returns:
            str: Resposta da IA
        """
        try:
            # Preparar contexto se fornecido
            contexto = ""
            if context_data:
                contexto = f"\n\nDados disponíveis:\n{context_data}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um assistente de IA para análise de dados de VR/VA."},
                    {"role": "user", "content": f"{pergunta}{contexto}"}
                ],
                temperature=0.7,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro na consulta IA: {e}")
            return f"Erro ao consultar IA: {e}"
