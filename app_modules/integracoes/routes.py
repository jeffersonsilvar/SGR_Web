from __future__ import annotations

from functools import wraps

from flask import Blueprint, flash, jsonify, redirect, render_template, session, url_for

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
    obter_conexao = services["obter_conexao"]
    usuario_eh_super_admin_global = services.get("usuario_eh_super_admin_global")

    def administrador_required(func):
        """Gate local e sem efeitos colaterais para o painel de infraestrutura."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_super_admin = False
            if usuario_eh_super_admin_global:
                try:
                    is_super_admin = bool(usuario_eh_super_admin_global())
                except Exception:
                    is_super_admin = False
            if not is_super_admin:
                is_super_admin = bool(session.get("is_super_admin"))

            perfil = str(session.get("perfil_de_acesso") or "").strip()
            if not is_super_admin and perfil != "Administrador":
                flash("Acesso restrito à Administração do sistema.", "warning")
                return redirect(url_for("inicio"))
            return func(*args, **kwargs)
        return wrapper

    bp = Blueprint("integracoes", __name__)

    @bp.get("/administracao/integracoes/armazenamento")
    @login_required
    @administrador_required
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
    @administrador_required
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
