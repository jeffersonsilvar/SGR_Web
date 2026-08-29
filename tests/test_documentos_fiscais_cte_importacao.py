from pathlib import Path

from app_modules.documentos.cte_importacao import eh_cte_xml, extrair_cte_xml


ROOT = Path(__file__).resolve().parents[1]


CTE_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<cteProc xmlns="http://www.portalfiscal.inf.br/cte" versao="4.00">
  <CTe>
    <infCte Id="CTe26260812345678000190570010000043211234567890" versao="4.00">
      <ide>
        <cUF>26</cUF><mod>57</mod><serie>1</serie><nCT>4321</nCT>
        <dhEmi>2026-08-27T12:00:00-03:00</dhEmi>
        <xMunIni>Recife</xMunIni><UFIni>PE</UFIni>
        <xMunFim>Jaboatao dos Guararapes</xMunFim><UFFim>PE</UFFim>
      </ide>
      <emit><CNPJ>12345678000190</CNPJ><IE>123456789</IE><xNome>TRANSPORTADORA TESTE LTDA</xNome></emit>
      <rem><CNPJ>11111111000191</CNPJ><xNome>REMETENTE TESTE LTDA</xNome></rem>
      <dest><CNPJ>37671532001132</CNPJ><xNome>GW EXPRESS LTDA</xNome></dest>
      <vPrest><vTPrest>350.90</vTPrest><vRec>350.90</vRec><Comp><xNome>FRETE VALOR</xNome><vComp>350.90</vComp></Comp></vPrest>
    </infCte>
  </CTe>
</cteProc>'''


def test_detecta_xml_cte():
    assert eh_cte_xml(CTE_XML) is True
    assert eh_cte_xml(b"<nfeProc><NFe/></nfeProc>") is False


def test_extrai_campos_principais_cte():
    dados = extrair_cte_xml(CTE_XML, lambda nome: nome.title())
    assert dados["tipo_documento"] == "CTE"
    assert dados["modelo_detectado"] == "CT-e"
    assert dados["numero_documento"] == "4321"
    assert dados["serie"] == "1"
    assert dados["data_emissao"] == "2026-08-27"
    assert dados["valor_total"] == "350.90"
    assert dados["cpf_cnpj_emitente"] == "12345678000190"
    assert dados["cpf_cnpj_destinatario"] == "37671532001132"
    assert dados["chave_acesso"] == "26260812345678000190570010000043211234567890"


def test_cte_descricao_carrega_rota_e_remetente():
    dados = extrair_cte_xml(CTE_XML)
    assert "Recife / PE" in dados["descricao"]
    assert "Jaboatao dos Guararapes / PE" in dados["descricao"]
    assert "REMETENTE TESTE LTDA" in dados["descricao"]


def test_importador_principal_instala_suporte_cte():
    import app_modules.documentos.importacao_xml as importacao

    dados = importacao.extrair_documento_xml(CTE_XML)
    assert dados["tipo_documento"] == "CTE"
    assert importacao._subcategoria_storage("CTE") == "CTe_Transporte"


def test_visualizador_ja_possui_dacte_cte():
    fonte = (ROOT / "app_modules" / "documentos" / "visualizacao_fiscal.py").read_text(encoding="utf-8")
    assert "_parse_cte_visual" in fonte
    assert '"titulo": "CT-e"' in fonte
    assert '"modelo": "CTE"' in fonte
