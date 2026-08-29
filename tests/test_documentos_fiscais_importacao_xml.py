from pathlib import Path

from app_modules.documentos.importacao_xml import extrair_documento_xml, normalizar_nome_apresentacao


ROOT = Path(__file__).resolve().parents[1]


NFE_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe26260812345678000190550010001000011234567890">
      <ide><serie>1</serie><nNF>100001</nNF><dhEmi>2026-08-26T09:30:00-03:00</dhEmi></ide>
      <emit><CNPJ>12345678000190</CNPJ><xNome>FORNECEDOR TESTE SERVICOS LTDA</xNome></emit>
      <dest><CNPJ>37671532001132</CNPJ><xNome>GW EXPRESS LTDA</xNome></dest>
      <det nItem="1"><prod><xProd>MATERIAL DE ESCRITORIO</xProd></prod></det>
      <total><ICMSTot><vNF>150.00</vNF></ICMSTot></total>
    </infNFe>
  </NFe>
</nfeProc>'''


def test_parser_nfe_extrai_dados_principais():
    dados = extrair_documento_xml(NFE_XML)
    assert dados["tipo_documento"] == "NFE_USO_CONSUMO"
    assert dados["numero_documento"] == "100001"
    assert dados["serie"] == "1"
    assert dados["chave_acesso"] == "26260812345678000190550010001000011234567890"
    assert dados["data_emissao"] == "2026-08-26"
    assert dados["valor_total"] == "150.00"
    assert dados["cpf_cnpj_emitente"] == "12345678000190"
    assert dados["cpf_cnpj_destinatario"] == "37671532001132"
    assert dados["nome_emitente_original"] == "FORNECEDOR TESTE SERVICOS LTDA"
    assert dados["nome_emitente"] == "Fornecedor Teste Servicos Ltda"


def test_normalizacao_preserva_preposicoes_e_sufixos():
    assert normalizar_nome_apresentacao("EMPRESA DE TESTE LTDA") == "Empresa de Teste Ltda"
    assert normalizar_nome_apresentacao("ALFA E BETA EPP") == "Alfa e Beta EPP"


def test_importacao_registra_rota_e_gate_de_pessoa():
    fonte = (ROOT / "app_modules" / "documentos" / "importacao_xml.py").read_text(encoding="utf-8")
    assert '/documentos-fiscais/importar' in fonte
    assert "_buscar_pessoa_por_documento" in fonte
    assert "Fornecedor ainda não está cadastrado" in fonte
    assert "IMPORTACAO_XML" in fonte
    assert "session[SESSAO_RASCUNHO]" in fonte


def test_importacao_preserva_xml_original_e_nao_gera_titulo():
    fonte = (ROOT / "app_modules" / "documentos" / "importacao_xml.py").read_text(encoding="utf-8")
    assert "_salvar_temporario" in fonte
    assert "StorageService" in fonte
    assert "storage.armazenar_arquivo" in fonte
    assert "_mover_para_documento" not in fonte
    assert "arquivo_xml" in fonte
    assert "INSERT INTO titulos_financeiros" not in fonte
    assert "INSERT INTO movimentacoes_caixa" not in fonte


def test_template_expoe_importacao_e_bloqueio_cadastral():
    central = (ROOT / "templates" / "documentos_fiscais.html").read_text(encoding="utf-8")
    importar = (ROOT / "templates" / "documento_fiscal_importar.html").read_text(encoding="utf-8")
    assert "Importar XML" in central
    assert "Emitente original do XML" in importar
    assert "Apresentação normalizada" in importar
    assert "Fornecedor não localizado" in importar
    assert "Verificar cadastro e concluir" in importar


def test_decisao_arquitetural_registra_parametro_futuro():
    adr = (ROOT / "docs" / "arquitetura" / "DECISAO_DOCUMENTOS_FISCAIS_PESSOAS.md").read_text(encoding="utf-8")
    assert "cadastros.normalizacao_texto" in adr
    assert "Pessoa é o cadastro mestre" in adr
    assert "Fornecedor inexistente bloqueia" in adr
