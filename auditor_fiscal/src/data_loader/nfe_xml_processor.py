"""
Processador de arquivos XML de NFe para o sistema de auditoria fiscal
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
from datetime import datetime

from data_loader.nfe_xml_parser import NFeXMLParser
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class NFeXMLProcessor:
    """Processador de arquivos XML de NFe"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa o processador
        
        Args:
            db_manager: Instância do gerenciador de banco de dados
        """
        self.db_manager = db_manager
        self.parser = NFeXMLParser()
        
    def process_xml_file(self, xml_content: str, filename: str) -> Dict[str, Any]:
        """
        Processa um arquivo XML de NFe
        
        Args:
            xml_content: Conteúdo do arquivo XML
            filename: Nome do arquivo
            
        Returns:
            Dicionário com resultado do processamento
        """
        try:
            logger.info(f"Processando arquivo XML: {filename}")
            
            # Validar estrutura do XML
            is_valid, errors = self.parser.validate_xml_structure(xml_content)
            if not is_valid:
                return {
                    "status": "error",
                    "message": "XML inválido",
                    "errors": errors,
                    "filename": filename
                }
            
            # Fazer parse do XML
            parsed_data = self.parser.parse_xml_file(xml_content)
            
            # Processar dados e inserir no banco
            result = self._insert_nfe_data(parsed_data, filename)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar XML {filename}: {str(e)}")
            return {
                "status": "error",
                "message": f"Erro ao processar arquivo: {str(e)}",
                "filename": filename
            }
    
    def _insert_nfe_data(self, parsed_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """
        Insere dados da NFe no banco de dados
        
        Args:
            parsed_data: Dados parseados do XML
            filename: Nome do arquivo
            
        Returns:
            Resultado da inserção
        """
        try:
            notas_inseridas = 0
            itens_inseridos = 0
            notas_ids_inseridos = []
            
            # Processar cada nota
            for nota in parsed_data.get("notas", []):
                # Inserir dados da nota (retorna tupla: (nota_id, is_new))
                nota_result = self._insert_nota_fiscal(nota, filename)
                if nota_result:
                    nota_id, is_new = nota_result if isinstance(nota_result, tuple) else (nota_result, True)
                    
                    if is_new:
                        notas_inseridas += 1
                        
                    notas_ids_inseridos.append(nota_id)
                    
                    # Inserir itens apenas se a nota foi recém-criada OU se a nota não tem itens
                    if is_new or not self._nota_has_itens(nota_id):
                        itens_count = self._insert_itens_nota(nota.get("itens", []), nota_id)
                        itens_inseridos += itens_count
                    else:
                        logger.info(f"Nota ID {nota_id} já possui itens. Pulando inserção de itens duplicados.")
            
            # Validar dados inseridos logo após o cadastro
            if notas_inseridas > 0:
                validation_result = self._validate_inserted_data(notas_ids_inseridos, filename)
                if not validation_result["is_valid"]:
                    logger.warning(f"Validação pós-cadastro encontrou inconsistências: {validation_result['errors']}")
                    # Ainda retorna sucesso, mas inclui avisos de validação
                    return {
                        "status": "success",
                        "message": f"Arquivo processado com sucesso",
                        "filename": filename,
                        "notas_inseridas": notas_inseridas,
                        "itens_inseridos": itens_inseridos,
                        "tipo": parsed_data.get("tipo", "individual"),
                        "validation_warnings": validation_result.get("errors", [])
                    }
            
            return {
                "status": "success",
                "message": f"Arquivo processado com sucesso",
                "filename": filename,
                "notas_inseridas": notas_inseridas,
                "itens_inseridos": itens_inseridos,
                "tipo": parsed_data.get("tipo", "individual")
            }
            
        except Exception as e:
            logger.error(f"Erro ao inserir dados no banco: {str(e)}")
            return {
                "status": "error",
                "message": f"Erro ao inserir dados: {str(e)}",
                "filename": filename
            }
    
    def _validate_inserted_data(self, notas_ids: List[int], filename: str) -> Dict[str, Any]:
        """
        Valida os dados inseridos no banco de dados após o cadastro
        
        Args:
            notas_ids: Lista de IDs das notas inseridas
            filename: Nome do arquivo
            
        Returns:
            Resultado da validação
        """
        errors = []
        
        try:
            conn, cursor = self.db_manager._get_connection()
            
            # Validar que todas as notas foram inseridas corretamente
            for nota_id in notas_ids:
                nota_query = "SELECT * FROM nfe_notas_fiscais WHERE id = ?"
                cursor.execute(nota_query, (nota_id,))
                nota_row = cursor.fetchone()
                
                if not nota_row:
                    errors.append(f"Nota com ID {nota_id} não encontrada após inserção")
                else:
                    # Validar que a nota tem chave de acesso
                    columns = [col[0] for col in cursor.description]
                    nota_dict = dict(zip(columns, nota_row))
                    
                    chave_key = None
                    for key in ['chave_acesso', 'chave_de_acesso', 'chaveacesso']:
                        if key in nota_dict:
                            chave_key = key
                            break
                    
                    if not chave_key or not nota_dict.get(chave_key):
                        errors.append(f"Nota ID {nota_id} não possui chave de acesso válida")
                    
                    # Validar que os itens foram inseridos corretamente
                    items_query = "SELECT COUNT(*) as total FROM nfe_itens_nota WHERE nota_id = ?"
                    cursor.execute(items_query, (nota_id,))
                    items_result = cursor.fetchone()
                    items_count = items_result[0] if items_result else 0
                    
                    if items_count == 0:
                        # Aviso apenas, não é erro crítico
                        logger.info(f"Nota ID {nota_id} não possui itens associados")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Erro ao validar dados inseridos: {str(e)}")
            return {
                "is_valid": False,
                "errors": [f"Erro na validação: {str(e)}"]
            }
    
    def _nota_has_itens(self, nota_id: int) -> bool:
        """
        Verifica se a nota já possui itens cadastrados
        
        Args:
            nota_id: ID da nota fiscal
            
        Returns:
            True se a nota tem itens, False caso contrário
        """
        try:
            conn, cursor = self.db_manager._get_connection()
            check_sql = "SELECT COUNT(*) as total FROM nfe_itens_nota WHERE nota_id = ?"
            cursor.execute(check_sql, (nota_id,))
            result = cursor.fetchone()
            count = result[0] if result else 0
            return count > 0
        except Exception as e:
            logger.error(f"Erro ao verificar itens da nota {nota_id}: {str(e)}")
            return False
    
    def _insert_nota_fiscal(self, nota: Dict[str, Any], filename: str) -> Optional[tuple]:
        """
        Insere dados da nota fiscal na tabela existente
        
        Args:
            nota: Dados da nota fiscal
            filename: Nome do arquivo
            
        Returns:
            Tupla (nota_id, is_new) onde:
            - nota_id: ID da nota (existente ou recém-inserida)
            - is_new: True se a nota foi criada agora, False se já existia
            Retorna None em caso de erro
        """
        try:
            conn, cursor = self.db_manager._get_connection()
            
            # Preparar dados da nota
            ide = nota.get("ide", {})
            emit = nota.get("emit", {})
            dest = nota.get("dest", {})
            total = nota.get("total", {})
            icms_tot = total.get("ICMSTot", {})
            
            # Criar chave de acesso da NFe
            chave_acesso = self._generate_chave_acesso(ide)
            
            # Mapear dados para estrutura da tabela existente
            nota_data = {
                # Campos originais da tabela existente
                "chave_de_acesso": chave_acesso,
                "modelo": ide.get("mod", ""),
                "série": ide.get("serie", ""),
                "número": ide.get("nNF", ""),
                "natureza_da_operação": ide.get("natOp", ""),
                "data_emissão": self._parse_date(ide.get("dhEmi") or ide.get("dEmi", "")),
                "evento_mais_recente": "",
                "data_hora_evento_mais_recente": "",
                "cpf_cnpj_emitente": emit.get("CNPJ", "") or emit.get("CPF", ""),
                "razão_social_emitente": emit.get("xNome", ""),
                "inscrição_estadual_emitente": emit.get("IE", ""),
                "uf_emitente": emit.get("enderEmit", {}).get("UF", ""),
                "município_emitente": emit.get("enderEmit", {}).get("xMun", ""),
                "cnpj_destinatário": dest.get("CNPJ", ""),
                "nome_destinatário": dest.get("xNome", ""),
                "uf_destinatário": dest.get("enderDest", {}).get("UF", ""),
                "indicador_ie_destinatário": dest.get("indIEDest", ""),
                "destino_da_operação": ide.get("idDest", ""),
                "consumidor_final": ide.get("indFinal", ""),
                "presença_do_comprador": ide.get("indPres", ""),
                "valor_nota_fiscal": str(self._parse_float(icms_tot.get("vNF", "0"))),
                
                # Campos adicionais expandidos
                "data_saida": self._parse_date(ide.get("dhSaiEnt") or ide.get("dSaiEnt", "")),
                "tipo_nf": ide.get("tpNF", ""),
                "ambiente": ide.get("tpAmb", ""),
                "finalidade": ide.get("finNFe", ""),
                "processo_emissao": ide.get("procEmi", ""),
                "versao_processo": ide.get("verProc", ""),
                "emit_fantasia": emit.get("xFant", ""),
                "emit_crt": emit.get("CRT", ""),
                "dest_cpf": dest.get("CPF", ""),
                "dest_ie": dest.get("IE", ""),
                "valor_produtos": self._parse_float(icms_tot.get("vProd", "0")),
                "valor_frete": self._parse_float(icms_tot.get("vFrete", "0")),
                "valor_seguro": self._parse_float(icms_tot.get("vSeg", "0")),
                "valor_desconto": self._parse_float(icms_tot.get("vDesc", "0")),
                "valor_outros": self._parse_float(icms_tot.get("vOutro", "0")),
                "valor_icms": self._parse_float(icms_tot.get("vICMS", "0")),
                "valor_ipi": self._parse_float(icms_tot.get("vIPI", "0")),
                "valor_pis": self._parse_float(icms_tot.get("vPIS", "0")),
                "valor_cofins": self._parse_float(icms_tot.get("vCOFINS", "0")),
                "arquivo_origem": filename,
                "data_processamento": datetime.now().isoformat(),
                "versao_xml": nota.get("versao", "")
            }
            
            # Verificar se já existe nota com a mesma chave de acesso
            # Tentar diferentes nomes de coluna possíveis
            chave_cols = ['chave_de_acesso', 'chave_acesso', 'chaveacesso']
            existing_nota_id = None
            
            for chave_col in chave_cols:
                try:
                    check_sql = f'SELECT id FROM nfe_notas_fiscais WHERE "{chave_col}" = ?'
                    cursor.execute(check_sql, (chave_acesso,))
                    existing = cursor.fetchone()
                    if existing:
                        existing_nota_id = existing[0]
                        logger.info(f"Nota fiscal com chave de acesso {chave_acesso[:20]}... já existe (ID: {existing_nota_id}). Pulando inserção.")
                        break
                except Exception as check_error:
                    # Coluna pode não existir, tentar próxima
                    continue
            
            if existing_nota_id:
                # Nota já existe, retornar ID existente e flag indicando que não é nova
                return (existing_nota_id, False)
            
            # Inserir na tabela apenas se não existir
            columns = list(nota_data.keys())
            placeholders = ", ".join(["?" for _ in columns])
            values = list(nota_data.values())
            
            sql = f"""
            INSERT INTO nfe_notas_fiscais ({", ".join(columns)})
            VALUES ({placeholders})
            """
            
            cursor.execute(sql, values)
            conn.commit()
            
            nota_id = cursor.lastrowid
            logger.info(f"Nota fiscal inserida com ID: {nota_id}")
            
            # Retornar tupla (nota_id, True) indicando que é uma nota nova
            return (nota_id, True)
            
        except Exception as e:
            logger.error(f"Erro ao inserir nota fiscal: {str(e)}")
            return None
    
    def _insert_itens_nota(self, itens: List[Dict[str, Any]], nota_id: int) -> int:
        """
        Insere itens da nota fiscal na tabela existente
        
        Args:
            itens: Lista de itens da nota
            nota_id: ID da nota fiscal
            
        Returns:
            Número de itens inseridos
        """
        try:
            conn, cursor = self.db_manager._get_connection()
            itens_inseridos = 0
            
            # Obter dados da nota para campos duplicados
            nota_query = "SELECT * FROM nfe_notas_fiscais WHERE id = ?"
            cursor.execute(nota_query, (nota_id,))
            nota_row = cursor.fetchone()
            
            if not nota_row:
                logger.error(f"Nota com ID {nota_id} não encontrada")
                return 0
            
            # Converter para dicionário usando nomes das colunas
            columns_info = cursor.description
            nota_data = dict(zip([col[0] for col in columns_info], nota_row))
            
            for item in itens:
                prod = item.get("prod", {})
                imposto = item.get("imposto", {})
                icms = imposto.get("ICMS", {})
                ipi = imposto.get("IPI", {})
                pis = imposto.get("PIS", {})
                cofins = imposto.get("COFINS", {})
                
                # Mapear dados para estrutura da tabela existente
                item_data = {
                    # Campos originais da tabela existente
                    "chave_de_acesso": nota_data.get("chave_de_acesso", ""),
                    "modelo": nota_data.get("modelo", ""),
                    "série": nota_data.get("série", ""),
                    "número": nota_data.get("número", ""),
                    "natureza_da_operação": nota_data.get("natureza_da_operação", ""),
                    "data_emissão": nota_data.get("data_emissão", ""),
                    "cpf_cnpj_emitente": nota_data.get("cpf_cnpj_emitente", ""),
                    "razão_social_emitente": nota_data.get("razão_social_emitente", ""),
                    "inscrição_estadual_emitente": nota_data.get("inscrição_estadual_emitente", ""),
                    "uf_emitente": nota_data.get("uf_emitente", ""),
                    "município_emitente": nota_data.get("município_emitente", ""),
                    "cnpj_destinatário": nota_data.get("cnpj_destinatário", ""),
                    "nome_destinatário": nota_data.get("nome_destinatário", ""),
                    "uf_destinatário": nota_data.get("uf_destinatário", ""),
                    "indicador_ie_destinatário": nota_data.get("indicador_ie_destinatário", ""),
                    "destino_da_operação": nota_data.get("destino_da_operação", ""),
                    "consumidor_final": nota_data.get("consumidor_final", ""),
                    "presença_do_comprador": nota_data.get("presença_do_comprador", ""),
                    "número_produto": item.get("nItem", ""),
                    "descrição_do_produto_serviço": prod.get("xProd", ""),
                    "código_ncm_sh": prod.get("NCM", ""),
                    "ncm_sh_tipo_de_produto": "",
                    "cfop": prod.get("CFOP", ""),
                    "quantidade": str(self._parse_float(prod.get("qCom", "0"))),
                    "unidade": prod.get("uCom", ""),
                    "valor_unitário": str(self._parse_float(prod.get("vUnCom", "0"))),
                    "valor_total": str(self._parse_float(prod.get("vProd", "0"))),
                    
                    # Campos adicionais expandidos
                    "nota_id": nota_id,
                    "codigo_produto": prod.get("cProd", ""),
                    "codigo_ean": prod.get("cEAN", ""),
                    "unidade_tributavel": prod.get("uTrib", ""),
                    "quantidade_tributavel": self._parse_float(prod.get("qTrib", "0")),
                    "valor_unitario_tributavel": self._parse_float(prod.get("vUnTrib", "0")),
                    "valor_frete": self._parse_float(prod.get("vFrete", "0")),
                    "valor_seguro": self._parse_float(prod.get("vSeg", "0")),
                    "valor_desconto": self._parse_float(prod.get("vDesc", "0")),
                    "valor_outros": self._parse_float(prod.get("vOutro", "0")),
                    "indicador_total": prod.get("indTot", ""),
                    
                    # ICMS
                    "icms_origem": icms.get("orig", ""),
                    "icms_cst": icms.get("CST", ""),
                    "icms_csosn": icms.get("CSOSN", ""),
                    "icms_modalidade_bc": icms.get("modBC", ""),
                    "icms_base_calculo": self._parse_float(icms.get("vBC", "0")),
                    "icms_aliquota": self._parse_float(icms.get("pICMS", "0")),
                    "icms_valor": self._parse_float(icms.get("vICMS", "0")),
                    "icms_modalidade_bc_st": icms.get("modBCST", ""),
                    "icms_base_calculo_st": self._parse_float(icms.get("vBCST", "0")),
                    "icms_aliquota_st": self._parse_float(icms.get("pICMSST", "0")),
                    "icms_valor_st": self._parse_float(icms.get("vICMSST", "0")),
                    "icms_percentual_reducao": self._parse_float(icms.get("pRedBC", "0")),
                    "icms_valor_desoneracao": self._parse_float(icms.get("vICMSDeson", "0")),
                    "icms_motivo_desoneracao": icms.get("motDesICMS", ""),
                    
                    # IPI
                    "ipi_codigo_enquadramento": ipi.get("cEnq", ""),
                    "ipi_cst": ipi.get("IPITrib", {}).get("CST", "") or ipi.get("IPINT", {}).get("CST", ""),
                    "ipi_base_calculo": self._parse_float(ipi.get("IPITrib", {}).get("vBC", "0")),
                    "ipi_aliquota": self._parse_float(ipi.get("IPITrib", {}).get("pIPI", "0")),
                    "ipi_quantidade": self._parse_float(ipi.get("IPITrib", {}).get("qUnid", "0")),
                    "ipi_valor_unitario": self._parse_float(ipi.get("IPITrib", {}).get("vUnid", "0")),
                    "ipi_valor": self._parse_float(ipi.get("IPITrib", {}).get("vIPI", "0")),
                    
                    # PIS
                    "pis_cst": pis.get("CST", ""),
                    "pis_base_calculo": self._parse_float(pis.get("vBC", "0")),
                    "pis_aliquota": self._parse_float(pis.get("pPIS", "0")),
                    "pis_quantidade": self._parse_float(pis.get("qBCProd", "0")),
                    "pis_valor_aliquota": self._parse_float(pis.get("vAliqProd", "0")),
                    "pis_valor": self._parse_float(pis.get("vPIS", "0")),
                    
                    # COFINS
                    "cofins_cst": cofins.get("CST", ""),
                    "cofins_base_calculo": self._parse_float(cofins.get("vBC", "0")),
                    "cofins_aliquota": self._parse_float(cofins.get("pCOFINS", "0")),
                    "cofins_quantidade": self._parse_float(cofins.get("qBCProd", "0")),
                    "cofins_valor_aliquota": self._parse_float(cofins.get("vAliqProd", "0")),
                    "cofins_valor": self._parse_float(cofins.get("vCOFINS", "0")),
                    
                    # Informações adicionais
                    "informacoes_adicionais": item.get("infAdProd", "")
                }
                
                # Inserir item
                columns = list(item_data.keys())
                placeholders = ", ".join(["?" for _ in columns])
                values = list(item_data.values())
                
                sql = f"""
                INSERT INTO nfe_itens_nota ({", ".join(columns)})
                VALUES ({placeholders})
                """
                
                cursor.execute(sql, values)
                itens_inseridos += 1
            
            conn.commit()
            logger.info(f"Inseridos {itens_inseridos} itens para nota ID {nota_id}")
            
            return itens_inseridos
            
        except Exception as e:
            logger.error(f"Erro ao inserir itens da nota: {str(e)}")
            return 0
    
    def _generate_chave_acesso(self, ide: Dict[str, Any]) -> str:
        """
        Gera chave de acesso da NFe
        
        Args:
            ide: Dados de identificação da NFe
            
        Returns:
            Chave de acesso gerada
        """
        try:
            # Extrair componentes da chave
            cuf = ide.get("cUF", "").zfill(2)
            aamm = ide.get("dhEmi", "")[:4] if ide.get("dhEmi") else ide.get("dEmi", "")[:4]
            cnpj = ide.get("emit", {}).get("CNPJ", "").replace(".", "").replace("/", "").replace("-", "")
            mod = ide.get("mod", "").zfill(2)
            serie = ide.get("serie", "").zfill(3)
            nf = ide.get("nNF", "").zfill(9)
            tp_emis = ide.get("tpEmis", "").zfill(1)
            cnf = ide.get("cNF", "").zfill(8)
            
            # Montar chave (sem dígito verificador)
            chave_sem_dv = f"{cuf}{aamm}{cnpj}{mod}{serie}{nf}{tp_emis}{cnf}"
            
            # Calcular dígito verificador (algoritmo módulo 11)
            dv = self._calculate_digit_verifier(chave_sem_dv)
            
            return f"{chave_sem_dv}{dv}"
            
        except Exception as e:
            logger.error(f"Erro ao gerar chave de acesso: {str(e)}")
            return ""
    
    def _calculate_digit_verifier(self, chave: str) -> str:
        """
        Calcula dígito verificador da chave de acesso
        
        Args:
            chave: Chave sem dígito verificador
            
        Returns:
            Dígito verificador
        """
        try:
            # Algoritmo módulo 11
            multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9]
            soma = 0
            
            for i, digito in enumerate(reversed(chave)):
                multiplicador = multiplicadores[i % len(multiplicadores)]
                soma += int(digito) * multiplicador
            
            resto = soma % 11
            dv = 11 - resto
            
            if dv >= 10:
                dv = 0
            
            return str(dv)
            
        except Exception as e:
            logger.error(f"Erro ao calcular dígito verificador: {str(e)}")
            return "0"
    
    def _parse_date(self, date_str: str) -> str:
        """
        Converte string de data para formato ISO
        
        Args:
            date_str: String de data
            
        Returns:
            Data em formato ISO ou string vazia
        """
        try:
            if not date_str:
                return ""
            
            # Tentar diferentes formatos
            formats = [
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
                "%d/%m/%Y"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            return date_str
            
        except Exception as e:
            logger.error(f"Erro ao converter data {date_str}: {str(e)}")
            return date_str
    
    def _parse_float(self, value_str: str) -> float:
        """
        Converte string para float
        
        Args:
            value_str: String com valor numérico
            
        Returns:
            Valor float ou 0.0
        """
        try:
            if not value_str:
                return 0.0
            
            # Remover caracteres não numéricos exceto ponto e vírgula
            cleaned = value_str.replace(",", ".")
            return float(cleaned)
            
        except (ValueError, TypeError):
            return 0.0
    
