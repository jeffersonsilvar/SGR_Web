# -*- coding: utf-8 -*-
"""
Parser robusto para XML de NFS-e / DANFSe no SGR Web.

Objetivo:
- Ler XML de NFS-e nacional/municipal mesmo com namespaces diferentes.
- Extrair os campos principais para a tela visualizar_danfse_nf.html.
- Corrigir formatação de valores monetários, evitando transformar 1042.80 em 104.280,00.

Uso esperado no app.py:
    from danfse_parser import parse_nfse_xml
    dados = parse_nfse_xml(xml_bytes_ou_string)
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
import xml.etree.ElementTree as ET


def _strip_namespace(tag: str) -> str:
    if not tag:
        return ""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _text(el) -> str:
    if el is None or el.text is None:
        return ""
    return str(el.text).strip()


def _all(root):
    return list(root.iter()) if root is not None else []


def _find_first(root, names, parent_names=None) -> str:
    """Busca o primeiro texto por nome local da tag, ignorando namespace.

    names: lista de possíveis nomes da tag final.
    parent_names: opcional, limita a busca a tags filhas de pais compatíveis.
    """
    wanted = {_norm_name(n) for n in names}
    parents = {_norm_name(n) for n in (parent_names or [])}

    if not parent_names:
        for el in _all(root):
            if _norm_name(_strip_namespace(el.tag)) in wanted and _text(el):
                return _text(el)
        return ""

    for parent in _all(root):
        if _norm_name(_strip_namespace(parent.tag)) in parents:
            for el in parent.iter():
                if el is parent:
                    continue
                if _norm_name(_strip_namespace(el.tag)) in wanted and _text(el):
                    return _text(el)
    return ""


def _find_any_attr(root, attr_names) -> str:
    wanted = {_norm_name(a) for a in attr_names}
    for el in _all(root):
        for k, v in el.attrib.items():
            if _norm_name(_strip_namespace(k)) in wanted and v:
                return str(v).strip()
    return ""


def _find_context(root, context_names):
    contexts = {_norm_name(n) for n in context_names}
    for el in _all(root):
        if _norm_name(_strip_namespace(el.tag)) in contexts:
            return el
    return None


def _first_non_empty(*values) -> str:
    for v in values:
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def _only_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _format_cpf_cnpj(value: str) -> str:
    digits = _only_digits(value)
    if len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    return value or "-"


def _format_cep(value: str) -> str:
    digits = _only_digits(value)
    if len(digits) == 8:
        return f"{digits[:5]}-{digits[5:]}"
    return value or "-"


def _format_date(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "-"

    # 2026-06-25T06:41:17-03:00 ou 2026-06-25T06:41:17
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}:\d{2}:\d{2})", value)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)} {m.group(4)}"

    # 2026-06-25
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", value)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"

    return value


def _parse_decimal(value: str):
    if value is None:
        return None
    s = str(value).strip()
    if not s or s == "-":
        return None
    s = s.replace("R$", "").replace(" ", "")

    # BR: 1.042,80 -> 1042.80
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    # Padrão XML: 1042.80 fica 1042.80, sem remover ponto decimal.

    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _format_money(value: str) -> str:
    dec = _parse_decimal(value)
    if dec is None:
        return "-"
    q = dec.quantize(Decimal("0.01"))
    inteiro, centavos = f"{q:.2f}".split(".")
    inteiro = f"{int(inteiro):,}".replace(",", ".")
    return f"R$ {inteiro},{centavos}"


def _format_percent(value: str) -> str:
    dec = _parse_decimal(value)
    if dec is None:
        return "-"
    s = f"{dec.normalize()}".replace(".", ",")
    return f"{s}%"


def _compose_address(ctx) -> str:
    if ctx is None:
        return "-"

    # Padrões mais comuns da NFS-e nacional/municipal
    logradouro = _first_non_empty(
        _find_first(ctx, ["xLgr", "logradouro", "endereco"]),
        _find_first(ctx, ["xLogradouro"]),
    )
    numero = _find_first(ctx, ["nro", "numero", "nLogradouro"])
    complemento = _find_first(ctx, ["xCpl", "complemento"])
    bairro = _find_first(ctx, ["xBairro", "bairro"])

    partes = []
    if logradouro:
        partes.append(logradouro)
    if numero:
        partes.append(numero)
    if complemento:
        partes.append(complemento)
    if bairro:
        partes.append(bairro)

    return ", ".join(partes) if partes else "-"


def _extract_person(root, context_names):
    ctx = _find_context(root, context_names)
    source = ctx if ctx is not None else root

    cpf_cnpj = _first_non_empty(
        _find_first(source, ["CNPJ", "CPF", "NIF", "cpfCnpj", "cnpjCpf"]),
        _find_first(source, ["CNPJ"], ["CNPJ"]),
        _find_first(source, ["CPF"], ["CPF"]),
    )

    nome = _first_non_empty(
        _find_first(source, ["xNome", "nome", "nomeEmpresarial", "razaoSocial", "xNomeEmp"]),
        _find_first(source, ["Nome", "NomeEmpresarial"]),
    )

    telefone = _first_non_empty(
        _find_first(source, ["fone", "telefone", "tel"]),
        _find_first(source, ["Telefone"]),
    )
    email = _first_non_empty(_find_first(source, ["email", "eMail"]), _find_first(source, ["Email"]))
    im = _first_non_empty(_find_first(source, ["IM", "inscricaoMunicipal", "inscMun"]), "-")
    municipio = _first_non_empty(
        _find_first(source, ["xMun", "municipio", "nomeMunicipio"]),
        _find_first(source, ["cMun"]),
    )
    uf = _find_first(source, ["UF", "uf"])
    if municipio and uf and uf not in municipio:
        municipio = f"{municipio} - {uf}"

    cep = _format_cep(_find_first(source, ["CEP", "cep"]))
    endereco = _compose_address(source)

    return {
        "cpf_cnpj": _format_cpf_cnpj(cpf_cnpj) if cpf_cnpj else "-",
        "inscricao_municipal": im or "-",
        "telefone": telefone or "-",
        "nome": nome or "-",
        "email": email or "-",
        "endereco": endereco or "-",
        "municipio": municipio or "-",
        "cep": cep or "-",
    }


def parse_nfse_xml(xml_content):
    """Retorna dict pronto para o template visualizar_danfse_nf.html."""
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8-sig", errors="replace")
    elif xml_content is None:
        xml_content = ""
    else:
        xml_content = str(xml_content)

    xml_content = xml_content.strip()
    if not xml_content:
        raise ValueError("XML vazio ou não encontrado.")

    root = ET.fromstring(xml_content.encode("utf-8"))

    prestador = _extract_person(root, ["prest", "prestador", "emit", "emissor", "prestadorservico"])
    tomador = _extract_person(root, ["toma", "tomador", "dest", "tomadorservico"])

    numero_nfse = _first_non_empty(
        _find_first(root, ["nNFSe", "numeroNfse", "numero", "nNFS", "numeroNota"]),
        _find_first(root, ["nNFSe"], ["infNFSe", "NFSe"]),
    )

    chave_acesso = _first_non_empty(
        _find_first(root, ["chNFSe", "chaveAcesso", "chave", "codigoVerificacao"]),
        _find_any_attr(root, ["Id", "id"]),
    )
    # Se vier como NFS-e + chave em atributo Id="NFS2611...", limpa prefixos comuns.
    if chave_acesso and chave_acesso.upper().startswith("NFS") and len(chave_acesso) > 20:
        chave_acesso = re.sub(r"^[A-Za-z]+", "", chave_acesso)

    competencia = _format_date(_first_non_empty(
        _find_first(root, ["dCompet", "competencia", "dataCompetencia"]),
        _find_first(root, ["dtCompetencia"]),
    ))
    data_emissao = _format_date(_first_non_empty(
        _find_first(root, ["dhEmi", "dataEmissao", "dataHoraEmissao", "dhEmissao"]),
        _find_first(root, ["dtEmissao"]),
    ))

    numero_dps = _first_non_empty(_find_first(root, ["nDPS", "numeroDps", "numeroDPS"]), "-")
    serie_dps = _first_non_empty(_find_first(root, ["serie", "serieDps", "serieDPS", "sDPS"]), "-")

    codigo_tributacao = _first_non_empty(
        _find_first(root, ["cTribNac", "codigoTributacaoNacional", "codigoTributacao", "itemListaServico"]),
        _find_first(root, ["cServ"]),
        "-",
    )
    codigo_tributacao_municipal = _first_non_empty(
        _find_first(root, ["cTribMun", "codigoTributacaoMunicipal"]),
        "-",
    )
    descricao_servico = _first_non_empty(
        _find_first(root, ["xDescServ", "descricaoServico", "discriminacao", "descServ", "descricao"]),
        _find_first(root, ["Discriminacao"]),
        "-",
    )
    local_prestacao = _first_non_empty(
        _find_first(root, ["xLocPrestacao", "localPrestacao", "municipioPrestacao", "xMunPrestacao"]),
        _find_first(root, ["cLocPrestacao", "cMunPrestacao"]),
        "-",
    )

    valor_servico_raw = _first_non_empty(
        _find_first(root, ["vServ", "valorServicos", "valorServico", "valorDoServico"]),
        _find_first(root, ["ValorServicos"]),
        _find_first(root, ["vServico"]),
    )
    valor_liquido_raw = _first_non_empty(
        _find_first(root, ["vLiq", "valorLiquido", "valorLiquidoNfse", "valorLiquidoNFS-e"]),
        _find_first(root, ["ValorLiquidoNfse"]),
        valor_servico_raw,
    )

    return {
        "cabecalho": {
            "titulo": "DANFSe v1.0",
            "subtitulo": "Documento Auxiliar da NFS-e",
            "orgao": _first_non_empty(_find_first(root, ["xOrgao", "orgao", "prefeitura"]), "Prefeitura / Portal Nacional da NFS-e"),
            "secretaria": _first_non_empty(_find_first(root, ["secretaria"]), "Documento Auxiliar da Nota Fiscal de Serviço Eletrônica"),
        },
        # Mantém os dois nomes para compatibilidade com templates diferentes.
        # Algumas telas usam danfse.numero_nf, outras usam danfse.numero_nfse.
        "numero_nf": numero_nfse or "-",
        "numero_nfse": numero_nfse or "-",
        "chave_acesso": chave_acesso or "-",
        "competencia": competencia or "-",
        "data_emissao": data_emissao or "-",
        "numero_dps": numero_dps or "-",
        "serie_dps": serie_dps or "-",
        "prestador": prestador,
        "tomador": tomador,
        "servico": {
            "codigo_tributacao": codigo_tributacao,
            "codigo_tributacao_municipal": codigo_tributacao_municipal,
            "local_prestacao": local_prestacao,
            "descricao": descricao_servico,
        },
        "tributacao": {
            "bc_issqn": _format_money(_first_non_empty(_find_first(root, ["vBC", "baseCalculo", "bcIssqn", "baseCalculoIssqn"]), "")),
            "aliquota_aplicada": _format_percent(_first_non_empty(_find_first(root, ["pAliq", "aliquota", "aliquotaAplicada"]), "")),
            "retencao_issqn": _first_non_empty(_find_first(root, ["indISSRet", "retencaoIssqn", "issRetido", "retido"]), "-"),
        },
        "valores": {
            "valor_servico": _format_money(valor_servico_raw),
            "valor_liquido": _format_money(valor_liquido_raw),
            "desconto_condicionado": _format_money(_find_first(root, ["vDescCond", "descontoCondicionado"])),
            "desconto_incondicionado": _format_money(_find_first(root, ["vDescIncond", "descontoIncondicionado"])),
            "issqn_retido": _format_money(_find_first(root, ["vISSRet", "issqnRetido", "valorIssRetido"])),
            "retencoes_federais": _format_money(_find_first(root, ["vRetFed", "totalRetencoesFederais"])),
        },
        "informacoes_complementares": _first_non_empty(
            _find_first(root, ["infCpl", "informacoesComplementares", "outrasInformacoes"]),
            "-",
        ),
    }

# Compatibilidade com versões anteriores do app.py
# Algumas versões importam parse_danfse_xml; outras importam parse_nfse_xml.
def parse_danfse_xml(xml_content):
    return parse_nfse_xml(xml_content)
