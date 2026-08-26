from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "financeiro_titulo_detalhes.html"

ANTIGO = '<tr><td colspan="4" class="text-center text-muted py-3">Título lançado manualmente, sem vínculo automático com NF, rota ou documento.</td></tr>'

NOVO = '''{% if titulo.origem == 'DOCUMENTO_FISCAL' %}
                                <tr>
                                    <td>Documento fiscal</td>
                                    <td>
                                        <a href="{{ url_for('documentos.detalhes_documento_fiscal', id=titulo.origem_id) }}">
                                            Documento Fiscal #{{ titulo.origem_id }}
                                        </a>
                                    </td>
                                    <td>{{ titulo.descricao }}</td>
                                    <td class="text-end">{{ titulo.valor_liquido|moeda_br }}</td>
                                </tr>
                                {% else %}
                                <tr><td colspan="4" class="text-center text-muted py-3">Título lançado manualmente, sem vínculo automático com NF, rota ou documento.</td></tr>
                                {% endif %}'''


def main():
    texto = TEMPLATE.read_text(encoding="utf-8")
    if NOVO in texto:
        print("[ok] Correção já aplicada.")
        return
    if ANTIGO not in texto:
        raise SystemExit("Trecho esperado não localizado no template.")
    TEMPLATE.write_text(texto.replace(ANTIGO, NOVO, 1), encoding="utf-8")
    print("[ok] Origem DOCUMENTO_FISCAL exibida corretamente no detalhe do título.")


if __name__ == "__main__":
    main()
