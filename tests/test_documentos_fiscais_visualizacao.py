from pathlib import Path

from app_modules.documentos.visualizacao_fiscal import interpretar_xml_fiscal


ROOT = Path(__file__).resolve().parents[1]


NFE_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe><infNFe Id="NFe26260812345678000190550010001000021234567891">
    <ide><serie>1</serie><nNF>100002</nNF><dhEmi>2026-08-27T11:10:00-03:00</dhEmi></ide>
    <emit><CNPJ>12345678000190</CNPJ><xNome>FORNECEDOR TESTE LTDA</xNome><IE>123</IE></emit>
    <dest><CNPJ>37671532001132</CNPJ><xNome>EMPRESA DESTINO LTDA</xNome></dest>
    <det nItem="1"><prod><cProd>MAT-002</cProd><xProd>MATERIAL TESTE</xProd><NCM>48201000</NCM><CFOP>5102</CFOP><uCom>UN</uCom><qCom>1.0000</qCom><vUnCom>175.50</vUnCom><vProd>175.50</vProd></prod></det>
    <total><ICMSTot><vProd>175.50</vProd><vICMS>31.59</vICMS><vNF>175.50</vNF></ICMSTot></total>
  </infNFe></NFe>
  <protNFe><infProt><nProt>126260000000002</nProt><xMotivo>Autorizado o uso da NF-e</xMotivo></infProt></protNFe>
</nfeProc>'''


CTE_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<cteProc xmlns="http://www.portalfiscal.inf.br/cte">
  <CTe><infCte Id="CTe26260812345678000190570010000001231234567890">
    <ide><serie>1</serie><nCT>123</nCT><dhEmi>2026-08-27T09:00:00-03:00</dhEmi><xMunIni>Recife</xMunIni><UFIni>PE</UFIni><xMunFim>Jaboatao dos Guararapes</xMunFim><UFFim>PE</UFFim></ide>
    <emit><CNPJ>12345678000190</CNPJ><xNome>TRANSPORTADORA TESTE LTDA</xNome><IE>456</IE></emit>
    <rem><CNPJ>11111111000111</CNPJ><xNome>REMETENTE TESTE LTDA</xNome></rem>
    <dest><CNPJ>37671532001132</CNPJ><xNome>DESTINATARIO TESTE LTDA</xNome></dest>
    <vPrest><vTPrest>250.00</vTPrest><vRec>250.00</vRec><Comp><xNome>FRETE VALOR</xNome><vComp>250.00</vComp></Comp></vPrest>
  </infCte></CTe>
  <protCTe><infProt><nProt>126260000000123</nProt><xMotivo>Autorizado o uso do CT-e</xMotivo></infProt></protCTe>
</cteProc>'''


def test_visualizador_nfe_extrai_itens_totais_e_protocolo():
    dados = interpretar_xml_fiscal(NFE_XML)
    assert dados["modelo"] == "NFE"
    assert dados["titulo"] == "NF-e"
    assert dados["numero"] == "100002"
    assert dados["emitente"]["documento"] == "12345678000190"
    assert dados["itens"][0]["descricao"] == "MATERIAL TESTE"
    assert str(dados["totais"]["total"]) == "175.50"
    assert dados["protocolo"] == "126260000000002"


def test_visualizador_cte_detecta_modelo_e_dados_transporte():
    dados = interpretar_xml_fiscal(CTE_XML)
    assert dados["modelo"] == "CTE"
    assert dados["titulo"] == "CT-e"
    assert dados["numero"] == "123"
    assert dados["transporte"]["municipio_inicio"] == "Recife"
    assert dados["transporte"]["municipio_fim"] == "Jaboatao dos Guararapes"
    assert str(dados["totais"]["total"]) == "250.00"


def test_endpoints_visualizacao_fiscal_registrados(app):
    regras = {regra.endpoint: regra.rule for regra in app.url_map.iter_rules()}
    assert regras["documentos.visualizar_documento_fiscal"] == "/documentos-fiscais/<int:id>/visualizar"
    assert regras["documentos.baixar_xml_original"] == "/documentos-fiscais/<int:id>/xml-original"


def test_visualizacao_le_storage_privado_sem_url_publica():
    fonte = (ROOT / "app_modules" / "documentos" / "visualizacao_fiscal.py").read_text(encoding="utf-8")
    assert "FROM arquivos_sistema" in fonte
    assert "StorageService" in fonte
    assert "storage.baixar_arquivo(arquivo)" in fonte
    assert "drive_view_url" not in fonte
    assert "drive_download_url" not in fonte


def test_detalhe_separa_visualizacao_de_xml_original():
    template = (ROOT / "templates" / "documento_fiscal_detalhes.html").read_text(encoding="utf-8")
    assert "Visualizar documento" in template
    assert "Baixar XML original" in template
    assert "Abrir PDF original" in template
    assert "Etapa 16.3" not in template


def test_template_visualizador_deixa_claro_que_e_representacao_auxiliar():
    template = (ROOT / "templates" / "documento_fiscal_visualizacao.html").read_text(encoding="utf-8")
    assert "Representação auxiliar gerada pelo SGR" in template
    assert "XML armazenado permanece inalterado" in template
    assert "window.print()" in template
