"""
Parser XML para Notas Fiscais Eletrônicas (NFe)
"""
import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class NFeXMLParser:
    """Parser para arquivos XML de NFe"""
    
    def __init__(self):
        self.namespace = "http://www.portalfiscal.inf.br/nfe"
        self.namespaces = {'nfe': self.namespace}
    
    def parse_xml_file(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse um arquivo XML de NFe
        
        Args:
            xml_content: Conteúdo do arquivo XML
            
        Returns:
            Dicionário com dados da NFe processados
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Verificar se é um lote de NFe ou NFe individual
            if root.tag.endswith('enviNFe'):
                return self._parse_lote_nfe(root)
            elif root.tag.endswith('NFe'):
                return self._parse_single_nfe(root)
            else:
                raise ValueError("Formato XML não reconhecido")
                
        except ET.ParseError as e:
            logger.error(f"Erro ao fazer parse do XML: {str(e)}")
            raise ValueError(f"XML inválido: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado ao processar XML: {str(e)}")
            raise
    
    def _parse_lote_nfe(self, root: ET.Element) -> Dict[str, Any]:
        """Parse um lote de NFe"""
        lote_data = {
            "tipo": "lote",
            "id_lote": self._get_text(root, "idLote"),
            "versao": root.get("versao"),
            "notas": []
        }
        
        # Processar cada NFe no lote
        for nfe_element in root.findall(".//nfe:NFe", self.namespaces):
            nota_data = self._parse_nfe_element(nfe_element)
            if nota_data:
                lote_data["notas"].append(nota_data)
        
        return lote_data
    
    def _parse_single_nfe(self, root: ET.Element) -> Dict[str, Any]:
        """Parse uma NFe individual"""
        nfe_element = root.find(".//nfe:infNFe", self.namespaces)
        if nfe_element is None:
            raise ValueError("Elemento infNFe não encontrado")
        
        nota_data = self._parse_nfe_element(nfe_element)
        return {
            "tipo": "individual",
            "notas": [nota_data] if nota_data else []
        }
    
    def _parse_nfe_element(self, inf_nfe: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse elemento infNFe"""
        try:
            # Dados básicos da NFe
            nfe_data = {
                "id": inf_nfe.get("Id"),
                "versao": inf_nfe.get("versao"),
                "ide": self._parse_ide(inf_nfe),
                "emit": self._parse_emit(inf_nfe),
                "dest": self._parse_dest(inf_nfe),
                "itens": self._parse_itens(inf_nfe),
                "total": self._parse_total(inf_nfe),
                "transp": self._parse_transp(inf_nfe),
                "pag": self._parse_pag(inf_nfe),
                "infAdic": self._parse_inf_adic(inf_nfe)
            }
            
            return nfe_data
            
        except Exception as e:
            logger.error(f"Erro ao processar elemento NFe: {str(e)}")
            return None
    
    def _parse_ide(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Parse dados de identificação"""
        ide = inf_nfe.find("nfe:ide", self.namespaces)
        if ide is None:
            return {}
        
        return {
            "cUF": self._get_text(ide, "cUF"),
            "cNF": self._get_text(ide, "cNF"),
            "natOp": self._get_text(ide, "natOp"),
            "mod": self._get_text(ide, "mod"),
            "serie": self._get_text(ide, "serie"),
            "nNF": self._get_text(ide, "nNF"),
            "dhEmi": self._get_text(ide, "dhEmi"),
            "dEmi": self._get_text(ide, "dEmi"),
            "hEmi": self._get_text(ide, "hEmi"),
            "dhSaiEnt": self._get_text(ide, "dhSaiEnt"),
            "dSaiEnt": self._get_text(ide, "dSaiEnt"),
            "hSaiEnt": self._get_text(ide, "hSaiEnt"),
            "tpNF": self._get_text(ide, "tpNF"),
            "idDest": self._get_text(ide, "idDest"),
            "cMunFG": self._get_text(ide, "cMunFG"),
            "tpImp": self._get_text(ide, "tpImp"),
            "tpEmis": self._get_text(ide, "tpEmis"),
            "cDV": self._get_text(ide, "cDV"),
            "tpAmb": self._get_text(ide, "tpAmb"),
            "finNFe": self._get_text(ide, "finNFe"),
            "indFinal": self._get_text(ide, "indFinal"),
            "indPres": self._get_text(ide, "indPres"),
            "procEmi": self._get_text(ide, "procEmi"),
            "verProc": self._get_text(ide, "verProc")
        }
    
    def _parse_emit(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Parse dados do emitente"""
        emit = inf_nfe.find("nfe:emit", self.namespaces)
        if emit is None:
            return {}
        
        ender_emit = emit.find("nfe:enderEmit", self.namespaces)
        endereco = {}
        if ender_emit is not None:
            endereco = {
                "xLgr": self._get_text(ender_emit, "xLgr"),
                "nro": self._get_text(ender_emit, "nro"),
                "xCpl": self._get_text(ender_emit, "xCpl"),
                "xBairro": self._get_text(ender_emit, "xBairro"),
                "cMun": self._get_text(ender_emit, "cMun"),
                "xMun": self._get_text(ender_emit, "xMun"),
                "UF": self._get_text(ender_emit, "UF"),
                "CEP": self._get_text(ender_emit, "CEP"),
                "cPais": self._get_text(ender_emit, "cPais"),
                "xPais": self._get_text(ender_emit, "xPais"),
                "fone": self._get_text(ender_emit, "fone")
            }
        
        return {
            "CNPJ": self._get_text(emit, "CNPJ"),
            "CPF": self._get_text(emit, "CPF"),
            "xNome": self._get_text(emit, "xNome"),
            "xFant": self._get_text(emit, "xFant"),
            "enderEmit": endereco,
            "IE": self._get_text(emit, "IE"),
            "IEST": self._get_text(emit, "IEST"),
            "IM": self._get_text(emit, "IM"),
            "CNAE": self._get_text(emit, "CNAE"),
            "CRT": self._get_text(emit, "CRT")
        }
    
    def _parse_dest(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Parse dados do destinatário"""
        dest = inf_nfe.find("nfe:dest", self.namespaces)
        if dest is None:
            return {}
        
        ender_dest = dest.find("nfe:enderDest", self.namespaces)
        endereco = {}
        if ender_dest is not None:
            endereco = {
                "xLgr": self._get_text(ender_dest, "xLgr"),
                "nro": self._get_text(ender_dest, "nro"),
                "xCpl": self._get_text(ender_dest, "xCpl"),
                "xBairro": self._get_text(ender_dest, "xBairro"),
                "cMun": self._get_text(ender_dest, "cMun"),
                "xMun": self._get_text(ender_dest, "xMun"),
                "UF": self._get_text(ender_dest, "UF"),
                "CEP": self._get_text(ender_dest, "CEP"),
                "cPais": self._get_text(ender_dest, "cPais"),
                "xPais": self._get_text(ender_dest, "xPais"),
                "fone": self._get_text(ender_dest, "fone")
            }
        
        return {
            "CNPJ": self._get_text(dest, "CNPJ"),
            "CPF": self._get_text(dest, "CPF"),
            "idEstrangeiro": self._get_text(dest, "idEstrangeiro"),
            "xNome": self._get_text(dest, "xNome"),
            "enderDest": endereco,
            "indIEDest": self._get_text(dest, "indIEDest"),
            "IE": self._get_text(dest, "IE"),
            "ISUF": self._get_text(dest, "ISUF"),
            "IM": self._get_text(dest, "IM"),
            "email": self._get_text(dest, "email")
        }
    
    def _parse_itens(self, inf_nfe: ET.Element) -> List[Dict[str, Any]]:
        """Parse itens da NFe"""
        itens = []
        det_elements = inf_nfe.findall(".//nfe:det", self.namespaces)
        
        for det in det_elements:
            item = {
                "nItem": det.get("nItem"),
                "prod": self._parse_prod(det),
                "imposto": self._parse_imposto(det),
                "infAdProd": self._get_text(det, "infAdProd")
            }
            itens.append(item)
        
        return itens
    
    def _parse_prod(self, det: ET.Element) -> Dict[str, Any]:
        """Parse dados do produto"""
        prod = det.find("nfe:prod", self.namespaces)
        if prod is None:
            return {}
        
        return {
            "cProd": self._get_text(prod, "cProd"),
            "cEAN": self._get_text(prod, "cEAN"),
            "cEANTrib": self._get_text(prod, "cEANTrib"),
            "xProd": self._get_text(prod, "xProd"),
            "NCM": self._get_text(prod, "NCM"),
            "CFOP": self._get_text(prod, "CFOP"),
            "uCom": self._get_text(prod, "uCom"),
            "qCom": self._get_text(prod, "qCom"),
            "vUnCom": self._get_text(prod, "vUnCom"),
            "vProd": self._get_text(prod, "vProd"),
            "cEANTrib": self._get_text(prod, "cEANTrib"),
            "uTrib": self._get_text(prod, "uTrib"),
            "qTrib": self._get_text(prod, "qTrib"),
            "vUnTrib": self._get_text(prod, "vUnTrib"),
            "vFrete": self._get_text(prod, "vFrete"),
            "vSeg": self._get_text(prod, "vSeg"),
            "vDesc": self._get_text(prod, "vDesc"),
            "vOutro": self._get_text(prod, "vOutro"),
            "indTot": self._get_text(prod, "indTot")
        }
    
    def _parse_imposto(self, det: ET.Element) -> Dict[str, Any]:
        """Parse dados dos impostos"""
        imposto = det.find("nfe:imposto", self.namespaces)
        if imposto is None:
            return {}
        
        return {
            "ICMS": self._parse_icms(imposto),
            "IPI": self._parse_ipi(imposto),
            "II": self._parse_ii(imposto),
            "PIS": self._parse_pis(imposto),
            "PISST": self._parse_pisst(imposto),
            "COFINS": self._parse_cofins(imposto),
            "COFINSST": self._parse_cofinsst(imposto),
            "ISSQN": self._parse_issqn(imposto)
        }
    
    def _parse_icms(self, imposto: ET.Element) -> Dict[str, Any]:
        """Parse dados do ICMS"""
        icms = imposto.find("nfe:ICMS", self.namespaces)
        if icms is None:
            return {}
        
        # Buscar por qualquer elemento ICMS (ICMS00, ICMS10, etc.)
        for icms_type in ["ICMS00", "ICMS10", "ICMS20", "ICMS30", "ICMS40", "ICMS51", "ICMS60", "ICMS70", "ICMS90"]:
            icms_element = icms.find(f"nfe:{icms_type}", self.namespaces)
            if icms_element is not None:
                return {
                    "tipo": icms_type,
                    "orig": self._get_text(icms_element, "orig"),
                    "CST": self._get_text(icms_element, "CST"),
                    "CSOSN": self._get_text(icms_element, "CSOSN"),
                    "modBC": self._get_text(icms_element, "modBC"),
                    "vBC": self._get_text(icms_element, "vBC"),
                    "pICMS": self._get_text(icms_element, "pICMS"),
                    "vICMS": self._get_text(icms_element, "vICMS"),
                    "modBCST": self._get_text(icms_element, "modBCST"),
                    "vBCST": self._get_text(icms_element, "vBCST"),
                    "pICMSST": self._get_text(icms_element, "pICMSST"),
                    "vICMSST": self._get_text(icms_element, "vICMSST"),
                    "pRedBC": self._get_text(icms_element, "pRedBC"),
                    "vICMSDeson": self._get_text(icms_element, "vICMSDeson"),
                    "motDesICMS": self._get_text(icms_element, "motDesICMS")
                }
        
        return {}
    
    def _parse_ipi(self, imposto: ET.Element) -> Dict[str, Any]:
        """Parse dados do IPI"""
        ipi = imposto.find("nfe:IPI", self.namespaces)
        if ipi is None:
            return {}
        
        return {
            "cEnq": self._get_text(ipi, "cEnq"),
            "IPITrib": self._parse_ipi_trib(ipi),
            "IPINT": self._parse_ipi_nt(ipi)
        }
    
    def _parse_ipi_trib(self, ipi: ET.Element) -> Dict[str, Any]:
        """Parse dados do IPI Tributado"""
        ipi_trib = ipi.find("nfe:IPITrib", self.namespaces)
        if ipi_trib is None:
            return {}
        
        return {
            "CST": self._get_text(ipi_trib, "CST"),
            "vBC": self._get_text(ipi_trib, "vBC"),
            "pIPI": self._get_text(ipi_trib, "pIPI"),
            "qUnid": self._get_text(ipi_trib, "qUnid"),
            "vUnid": self._get_text(ipi_trib, "vUnid"),
            "vIPI": self._get_text(ipi_trib, "vIPI")
        }
    
    def _parse_ipi_nt(self, ipi: ET.Element) -> Dict[str, Any]:
        """Parse dados do IPI Não Tributado"""
        ipi_nt = ipi.find("nfe:IPINT", self.namespaces)
        if ipi_nt is None:
            return {}
        
        return {
            "CST": self._get_text(ipi_nt, "CST")
        }
    
    def _parse_ii(self, imposto: ET.Element) -> Dict[str, Any]:
        """Parse dados do II"""
        ii = imposto.find("nfe:II", self.namespaces)
        if ii is None:
            return {}
        
        return {
            "vBC": self._get_text(ii, "vBC"),
            "vDespAdu": self._get_text(ii, "vDespAdu"),
            "vII": self._get_text(ii, "vII"),
            "vIOF": self._get_text(ii, "vIOF")
        }
    
    def _parse_pis(self, imposto: ET.Element) -> Dict[str, Any]:
        """Parse dados do PIS"""
        pis = imposto.find("nfe:PIS", self.namespaces)
        if pis is None:
            return {}
        
        # Buscar por qualquer elemento PIS
        for pis_type in ["PISAliq", "PISQtde", "PISNT", "PISOutr"]:
            pis_element = pis.find(f"nfe:{pis_type}", self.namespaces)
            if pis_element is not None:
                return {
                    "tipo": pis_type,
                    "CST": self._get_text(pis_element, "CST"),
                    "vBC": self._get_text(pis_element, "vBC"),
                    "pPIS": self._get_text(pis_element, "pPIS"),
                    "qBCProd": self._get_text(pis_element, "qBCProd"),
                    "vAliqProd": self._get_text(pis_element, "vAliqProd"),
                    "vPIS": self._get_text(pis_element, "vPIS")
                }
        
        return {}
    
    def _parse_pisst(self, imposto: ET.Element) -> Dict[str, Any]:
        """Parse dados do PIS ST"""
        pisst = imposto.find("nfe:PISST", self.namespaces)
        if pisst is None:
            return {}
        
        return {
            "vBC": self._get_text(pisst, "vBC"),
            "pPIS": self._get_text(pisst, "pPIS"),
            "qBCProd": self._get_text(pisst, "qBCProd"),
            "vAliqProd": self._get_text(pisst, "vAliqProd"),
            "vPIS": self._get_text(pisst, "vPIS")
        }
    
    def _parse_cofins(self, imposto: ET.Element) -> Dict[str, Any]:
        """Parse dados do COFINS"""
        cofins = imposto.find("nfe:COFINS", self.namespaces)
        if cofins is None:
            return {}
        
        # Buscar por qualquer elemento COFINS
        for cofins_type in ["COFINSAliq", "COFINSQtde", "COFINSNT", "COFINSOutr"]:
            cofins_element = cofins.find(f"nfe:{cofins_type}", self.namespaces)
            if cofins_element is not None:
                return {
                    "tipo": cofins_type,
                    "CST": self._get_text(cofins_element, "CST"),
                    "vBC": self._get_text(cofins_element, "vBC"),
                    "pCOFINS": self._get_text(cofins_element, "pCOFINS"),
                    "qBCProd": self._get_text(cofins_element, "qBCProd"),
                    "vAliqProd": self._get_text(cofins_element, "vAliqProd"),
                    "vCOFINS": self._get_text(cofins_element, "vCOFINS")
                }
        
        return {}
    
    def _parse_cofinsst(self, imposto: ET.Element) -> Dict[str, Any]:
        """Parse dados do COFINS ST"""
        cofinsst = imposto.find("nfe:COFINSST", self.namespaces)
        if cofinsst is None:
            return {}
        
        return {
            "vBC": self._get_text(cofinsst, "vBC"),
            "pCOFINS": self._get_text(cofinsst, "pCOFINS"),
            "qBCProd": self._get_text(cofinsst, "qBCProd"),
            "vAliqProd": self._get_text(cofinsst, "vAliqProd"),
            "vCOFINS": self._get_text(cofinsst, "vCOFINS")
        }
    
    def _parse_issqn(self, imposto: ET.Element) -> Dict[str, Any]:
        """Parse dados do ISSQN"""
        issqn = imposto.find("nfe:ISSQN", self.namespaces)
        if issqn is None:
            return {}
        
        return {
            "vBC": self._get_text(issqn, "vBC"),
            "vAliq": self._get_text(issqn, "vAliq"),
            "vISSQN": self._get_text(issqn, "vISSQN"),
            "cMunFG": self._get_text(issqn, "cMunFG"),
            "cListServ": self._get_text(issqn, "cListServ"),
            "cSitTrib": self._get_text(issqn, "cSitTrib")
        }
    
    def _parse_total(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Parse dados totais da NFe"""
        total = inf_nfe.find("nfe:total", self.namespaces)
        if total is None:
            return {}
        
        icms_tot = total.find("nfe:ICMSTot", self.namespaces)
        icms_data = {}
        if icms_tot is not None:
            icms_data = {
                "vBC": self._get_text(icms_tot, "vBC"),
                "vICMS": self._get_text(icms_tot, "vICMS"),
                "vICMSDeson": self._get_text(icms_tot, "vICMSDeson"),
                "vFCP": self._get_text(icms_tot, "vFCP"),
                "vBCST": self._get_text(icms_tot, "vBCST"),
                "vST": self._get_text(icms_tot, "vST"),
                "vFCPST": self._get_text(icms_tot, "vFCPST"),
                "vFCPSTRet": self._get_text(icms_tot, "vFCPSTRet"),
                "vProd": self._get_text(icms_tot, "vProd"),
                "vFrete": self._get_text(icms_tot, "vFrete"),
                "vSeg": self._get_text(icms_tot, "vSeg"),
                "vDesc": self._get_text(icms_tot, "vDesc"),
                "vII": self._get_text(icms_tot, "vII"),
                "vIPI": self._get_text(icms_tot, "vIPI"),
                "vIPIDevol": self._get_text(icms_tot, "vIPIDevol"),
                "vPIS": self._get_text(icms_tot, "vPIS"),
                "vCOFINS": self._get_text(icms_tot, "vCOFINS"),
                "vOutro": self._get_text(icms_tot, "vOutro"),
                "vNF": self._get_text(icms_tot, "vNF"),
                "vTotTrib": self._get_text(icms_tot, "vTotTrib")
            }
        
        return {
            "ICMSTot": icms_data
        }
    
    def _parse_transp(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Parse dados do transporte"""
        transp = inf_nfe.find("nfe:transp", self.namespaces)
        if transp is None:
            return {}
        
        return {
            "modFrete": self._get_text(transp, "modFrete"),
            "transporta": self._parse_transporta(transp),
            "veicTransp": self._parse_veic_transp(transp),
            "reboque": self._parse_reboque(transp),
            "vagao": self._get_text(transp, "vagao"),
            "balsa": self._get_text(transp, "balsa"),
            "vol": self._parse_vol(transp)
        }
    
    def _parse_transporta(self, transp: ET.Element) -> Dict[str, Any]:
        """Parse dados do transportador"""
        transporta = transp.find("nfe:transporta", self.namespaces)
        if transporta is None:
            return {}
        
        return {
            "CNPJ": self._get_text(transporta, "CNPJ"),
            "CPF": self._get_text(transporta, "CPF"),
            "xNome": self._get_text(transporta, "xNome"),
            "IE": self._get_text(transporta, "IE"),
            "xEnder": self._get_text(transporta, "xEnder"),
            "xMun": self._get_text(transporta, "xMun"),
            "UF": self._get_text(transporta, "UF")
        }
    
    def _parse_veic_transp(self, transp: ET.Element) -> Dict[str, Any]:
        """Parse dados do veículo de transporte"""
        veic_transp = transp.find("nfe:veicTransp", self.namespaces)
        if veic_transp is None:
            return {}
        
        return {
            "placa": self._get_text(veic_transp, "placa"),
            "UF": self._get_text(veic_transp, "UF"),
            "RNTC": self._get_text(veic_transp, "RNTC")
        }
    
    def _parse_reboque(self, transp: ET.Element) -> List[Dict[str, Any]]:
        """Parse dados dos reboques"""
        reboques = []
        reboque_elements = transp.findall("nfe:reboque", self.namespaces)
        
        for reboque in reboque_elements:
            reboque_data = {
                "placa": self._get_text(reboque, "placa"),
                "UF": self._get_text(reboque, "UF"),
                "RNTC": self._get_text(reboque, "RNTC")
            }
            reboques.append(reboque_data)
        
        return reboques
    
    def _parse_vol(self, transp: ET.Element) -> List[Dict[str, Any]]:
        """Parse dados dos volumes"""
        volumes = []
        vol_elements = transp.findall("nfe:vol", self.namespaces)
        
        for vol in vol_elements:
            vol_data = {
                "qVol": self._get_text(vol, "qVol"),
                "esp": self._get_text(vol, "esp"),
                "marca": self._get_text(vol, "marca"),
                "nVol": self._get_text(vol, "nVol"),
                "pesoL": self._get_text(vol, "pesoL"),
                "pesoB": self._get_text(vol, "pesoB"),
                "lacres": self._parse_lacres(vol)
            }
            volumes.append(vol_data)
        
        return volumes
    
    def _parse_lacres(self, vol: ET.Element) -> List[Dict[str, Any]]:
        """Parse dados dos lacres"""
        lacres = []
        lacre_elements = vol.findall("nfe:lacres", self.namespaces)
        
        for lacre in lacre_elements:
            lacre_data = {
                "nLacre": self._get_text(lacre, "nLacre")
            }
            lacres.append(lacre_data)
        
        return lacres
    
    def _parse_pag(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Parse dados do pagamento"""
        pag = inf_nfe.find("nfe:pag", self.namespaces)
        if pag is None:
            return {}
        
        return {
            "detPag": self._parse_det_pag(pag)
        }
    
    def _parse_det_pag(self, pag: ET.Element) -> List[Dict[str, Any]]:
        """Parse dados dos detalhes de pagamento"""
        detalhes = []
        det_pag_elements = pag.findall("nfe:detPag", self.namespaces)
        
        for det_pag in det_pag_elements:
            det_data = {
                "indPag": self._get_text(det_pag, "indPag"),
                "tPag": self._get_text(det_pag, "tPag"),
                "vPag": self._get_text(det_pag, "vPag"),
                "card": self._parse_card(det_pag)
            }
            detalhes.append(det_data)
        
        return detalhes
    
    def _parse_card(self, det_pag: ET.Element) -> Dict[str, Any]:
        """Parse dados do cartão"""
        card = det_pag.find("nfe:card", self.namespaces)
        if card is None:
            return {}
        
        return {
            "tpIntegra": self._get_text(card, "tpIntegra"),
            "CNPJ": self._get_text(card, "CNPJ"),
            "tBand": self._get_text(card, "tBand"),
            "cAut": self._get_text(card, "cAut")
        }
    
    def _parse_inf_adic(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Parse informações adicionais"""
        inf_adic = inf_nfe.find("nfe:infAdic", self.namespaces)
        if inf_adic is None:
            return {}
        
        return {
            "infAdFisco": self._get_text(inf_adic, "infAdFisco"),
            "infCpl": self._get_text(inf_adic, "infCpl"),
            "obsCont": self._parse_obs_cont(inf_adic),
            "obsFisco": self._parse_obs_fisco(inf_adic),
            "procRef": self._parse_proc_ref(inf_adic)
        }
    
    def _parse_obs_cont(self, inf_adic: ET.Element) -> List[Dict[str, Any]]:
        """Parse observações do contribuinte"""
        obs_cont = []
        obs_cont_elements = inf_adic.findall("nfe:obsCont", self.namespaces)
        
        for obs in obs_cont_elements:
            obs_data = {
                "xCampo": obs.get("xCampo"),
                "xTexto": self._get_text(obs, "xTexto")
            }
            obs_cont.append(obs_data)
        
        return obs_cont
    
    def _parse_obs_fisco(self, inf_adic: ET.Element) -> List[Dict[str, Any]]:
        """Parse observações do fisco"""
        obs_fisco = []
        obs_fisco_elements = inf_adic.findall("nfe:obsFisco", self.namespaces)
        
        for obs in obs_fisco_elements:
            obs_data = {
                "xCampo": obs.get("xCampo"),
                "xTexto": self._get_text(obs, "xTexto")
            }
            obs_fisco.append(obs_data)
        
        return obs_fisco
    
    def _parse_proc_ref(self, inf_adic: ET.Element) -> List[Dict[str, Any]]:
        """Parse processos de referência"""
        proc_ref = []
        proc_ref_elements = inf_adic.findall("nfe:procRef", self.namespaces)
        
        for proc in proc_ref_elements:
            proc_data = {
                "nProc": self._get_text(proc, "nProc"),
                "indProc": self._get_text(proc, "indProc")
            }
            proc_ref.append(proc_data)
        
        return proc_ref
    
    def _get_text(self, element: ET.Element, tag: str) -> str:
        """Obtém texto de um elemento XML"""
        if element is None:
            return ""
        
        child = element.find(f"nfe:{tag}", self.namespaces)
        if child is not None:
            return child.text or ""
        
        return ""
    
    def validate_xml_structure(self, xml_content: str) -> Tuple[bool, List[str]]:
        """
        Valida a estrutura básica do XML de NFe
        
        Args:
            xml_content: Conteúdo do arquivo XML
            
        Returns:
            Tupla (é_válido, lista_de_erros)
        """
        errors = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Verificar namespace
            if not root.tag.endswith(('NFe', 'enviNFe')):
                errors.append("Elemento raiz deve ser 'NFe' ou 'enviNFe'")
            
            # Verificar se tem namespace correto
            if 'http://www.portalfiscal.inf.br/nfe' not in root.tag:
                errors.append("Namespace incorreto - deve ser 'http://www.portalfiscal.inf.br/nfe'")
            
            # Verificar elementos obrigatórios
            if root.tag.endswith('enviNFe'):
                if root.find(".//nfe:infNFe", self.namespaces) is None:
                    errors.append("Lote deve conter pelo menos uma NFe")
            else:
                if root.find(".//nfe:infNFe", self.namespaces) is None:
                    errors.append("NFe deve conter elemento 'infNFe'")
            
            return len(errors) == 0, errors
            
        except ET.ParseError as e:
            errors.append(f"XML malformado: {str(e)}")
            return False, errors
        except Exception as e:
            errors.append(f"Erro de validação: {str(e)}")
            return False, errors
