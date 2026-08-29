from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
import xml.etree.ElementTree as ET


def _local(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _primeiro(parent, nome):
    if parent is None:
        return None
    for el in parent.iter():
        if _local(el.tag) == nome:
            return el
    return None


def _texto(parent, nome):
    el = _primeiro(parent, nome)
    return (el.text or "").strip() if el is not None and el.text else ""


def _digits(valor):
    return re.sub(r"\D", "", str(valor or ""))


def _data_iso(valor):
    texto = str(valor or "").strip()[:10]
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""


def _decimal(valor):
    texto = str(valor or "0").strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return f"{Decimal(texto).quantize(Decimal('0.01')):.2f}"
    except (InvalidOperation, ValueError, TypeError):
        return "0.00"


def eh_cte_xml(xml_bytes):
    if not xml_bytes:
        return False
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return False
    nomes = {_local(el.tag) for el in root.iter()}
    return "CTe" in nomes or "infCte" in nomes


def extrair_cte_xml(xml_bytes, normalizar_nome=None):
    if not xml_bytes:
        raise ValueError("Arquivo XML vazio.")
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"XML fiscal inválido: {exc}") from exc

    inf = _primeiro(root, "infCte")
    if inf is None:
        raise ValueError("Estrutura CT-e não localizada no XML.")

    ide = _primeiro(inf, "ide")
    emit = _primeiro(inf, "emit")
    dest = _primeiro(inf, "dest")
    rem = _primeiro(inf, "rem")
    vprest = _primeiro(inf, "vPrest")
    if ide is None or emit is None:
        raise ValueError("XML de CT-e sem identificação do emitente/documento.")

    numero = _texto(ide, "nCT")
    serie = _texto(ide, "serie")
    emissao = _data_iso(_texto(ide, "dhEmi") or _texto(ide, "dEmi"))
    chave = re.sub(r"^[A-Za-z]+", "", str(inf.attrib.get("Id") or ""))
    nome_original = _texto(emit, "xNome")
    nome_apresentacao = normalizar_nome(nome_original) if normalizar_nome else nome_original
    emitente = _digits(_texto(emit, "CNPJ") or _texto(emit, "CPF"))
    destinatario = _digits(_texto(dest, "CNPJ") or _texto(dest, "CPF")) if dest is not None else ""
    valor = _decimal(_texto(vprest, "vTPrest") or _texto(vprest, "vRec"))

    origem = " / ".join(item for item in (_texto(ide, "xMunIni"), _texto(ide, "UFIni")) if item)
    destino = " / ".join(item for item in (_texto(ide, "xMunFim"), _texto(ide, "UFFim")) if item)
    remetente = _texto(rem, "xNome") if rem is not None else ""
    descricao = f"CT-e {numero}"
    if origem or destino:
        descricao += f" - {origem or '?'} -> {destino or '?'}"
    if remetente:
        descricao += f" - Remetente: {remetente}"

    return {
        "tipo_documento": "CTE",
        "numero_documento": numero,
        "serie": serie,
        "chave_acesso": chave,
        "data_emissao": emissao,
        "data_competencia": emissao,
        "valor_total": valor,
        "nome_emitente_original": nome_original,
        "nome_emitente": nome_apresentacao,
        "cpf_cnpj_emitente": emitente,
        "cpf_cnpj_destinatario": destinatario,
        "descricao": descricao[:255],
        "modelo_detectado": "CT-e",
    }


def instalar_suporte_cte(importacao_module):
    """Amplia o importador fiscal existente sem duplicar a rota de importação.

    Esta ponte fica isolada para a etapa 16.4B/16.4C. O XML CT-e passa pelo mesmo
    fluxo transacional, vínculo com Pessoa e StorageService já usado por NF-e/NFS-e.
    """
    extrator_base = importacao_module.extrair_documento_xml
    subcategoria_base = importacao_module._subcategoria_storage

    def extrator_expandido(xml_bytes):
        if eh_cte_xml(xml_bytes):
            dados = extrair_cte_xml(xml_bytes, importacao_module.normalizar_nome_apresentacao)
            obrigatorios = ("numero_documento", "data_emissao", "cpf_cnpj_emitente")
            faltantes = [campo for campo in obrigatorios if not dados.get(campo)]
            if faltantes:
                raise ValueError(
                    "Não foi possível identificar campos obrigatórios no XML: " + ", ".join(faltantes)
                )
            if Decimal(dados.get("valor_total") or "0") <= 0:
                raise ValueError("Não foi possível identificar um valor fiscal válido no XML.")
            return dados
        return extrator_base(xml_bytes)

    def subcategoria_expandida(tipo_documento):
        if tipo_documento == "CTE":
            return "CTe_Transporte"
        return subcategoria_base(tipo_documento)

    importacao_module.extrair_documento_xml = extrator_expandido
    importacao_module._subcategoria_storage = subcategoria_expandida
