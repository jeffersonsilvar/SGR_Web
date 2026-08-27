from __future__ import annotations

from flask import Blueprint, jsonify, render_template, session

from app_modules.storage import StorageService


def _persistir_status(cur, resultado):
    cur.execute(
        """
        INSERT INTO storage_health_status
            (provider, status_integracao, mensagem, latencia_ms, verificado_em)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status_integracao = VALUES(status_integracao),
            mensagem = VALUES(mensagem),
            latencia_ms = VALUES(latencia_ms),
            verificado_em = VALUES(verificado_em),
            atualizado_em = CURRENT_TIMESTAMP
        """,
        (
            resultado.get("provider"),
            resultado.get("status"),
            resultado.get("mensagem"),
            resultado.get("latencia_ms"),
            resultado.get("verificado_em"),
        ),
    )


def criar_integracoes_blueprint(services):
    login_required = services["login_required"]
    perfis_permitidos = services["perfis_permitidos"]
    obter_conexao = services["obter_conexao"]

    bp = Blueprint("integracoes", __name__)

    @bp.get("/administracao/integracoes/armazenamento")
    @login_required
    @perfis_permitidos("Administrador")
    def armazenamento():
        con = obter_conexao()
        status = None
        if con is not None:
            cur = con.cursor(dictionary=True)
            try:
                cur.execute(
                    """
                    SELECT provider,
                           status_integracao AS status,
                           mensagem,
                           latencia_ms,
                           verificado_em
                    FROM storage_health_status
                    WHERE provider = %s
                    LIMIT 1
                    """,
                    (StorageService().provider,),
                )
                status = cur.fetchone()
            except Exception:
                status = None
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
                try:
                    con.close()
                except Exception:
                    pass

        if not status:
            status = {
                "provider": StorageService().provider,
                "status": "NAO_CONFIGURADO",
                "mensagem": "Ainda não existe verificação registrada para este provider.",
                "latencia_ms": None,
                "verificado_em": None,
            }

        return render_template(
            "integracoes_armazenamento.html",
            status_storage=status,
            usuario_logado=session.get("usuario_nome", "Usuário"),
        )

    @bp.post("/administracao/integracoes/armazenamento/api/testar")
    @login_required
    @perfis_permitidos("Administrador")
    def testar_armazenamento():
        resultado = StorageService().health_check()
        con = obter_conexao()
        if con is not None:
            cur = con.cursor(dictionary=True)
            try:
                _persistir_status(cur, resultado)
                con.commit()
            except Exception:
                try:
                    con.rollback()
                except Exception:
                    pass
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
                try:
                    con.close()
                except Exception:
                    pass

        return jsonify(
            provider=resultado.get("provider"),
            status=resultado.get("status"),
            mensagem=resultado.get("mensagem"),
            latencia_ms=resultado.get("latencia_ms"),
            verificado_em=resultado.get("verificado_em").strftime("%d/%m/%Y %H:%M:%S") if resultado.get("verificado_em") else None,
        )

    return bp
