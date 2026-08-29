from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "database" / "migrations" / "20260829_blueprint17_1_pessoa_vinculos.sql"


def _migration():
    return MIGRATION.read_text(encoding="utf-8")


def test_migration_cria_tabela_pessoa_vinculos_sem_destruir_legado():
    migration = _migration()

    assert "CREATE TABLE IF NOT EXISTS pessoa_vinculos" in migration
    assert "UNIQUE KEY uq_pessoa_vinculos_empresa_pessoa_tipo" in migration
    assert "empresa_id INT(11) NOT NULL" in migration
    assert "pessoa_id INT(11) NOT NULL" in migration
    assert "ALTER TABLE pessoas" not in migration
    assert "DROP TABLE" not in migration
    assert "DROP COLUMN" not in migration


def test_migration_separa_papel_de_prestador_e_funcao_operacional():
    migration = _migration()

    assert "'PRESTADOR_SERVICO'" in migration
    assert "'MOTORISTA'" in migration
    assert "'AJUDANTE'" in migration
    assert "p.tipo_cadastro" in migration
    assert "p.tipo_prestador" in migration


def test_migration_mapeia_fornecedor_e_funcionario():
    migration = _migration()

    assert "'FORNECEDOR'" in migration
    assert "'FUNCIONARIO'" in migration
    assert "tipo_cadastro = Fornecedor" in migration
    assert "tipo_cadastro = Funcionario" in migration


def test_migration_e_idempotente_por_empresa_pessoa_e_tipo():
    migration = _migration()

    assert migration.count("AND NOT EXISTS (") >= 5
    assert "pv.empresa_id = p.empresa_id" in migration
    assert "pv.pessoa_id = p.id" in migration
    assert "pv.tipo_vinculo = 'MOTORISTA'" in migration
    assert "pv.tipo_vinculo = 'AJUDANTE'" in migration


def test_outros_e_acesso_portal_nao_viram_vinculo_automatico():
    migration = _migration()

    # "Outros" aparece somente na documentação de decisão; não deve existir INSERT desse papel.
    assert "'OUTROS'" not in migration
    assert "'PORTAL'" not in migration
    assert "permite_acesso_portal também não é vínculo" in migration


def test_migration_preserva_campos_legados_motorista_e_ajudante():
    migration = _migration()

    assert "motorista_id" in migration.splitlines()[2]
    assert "ajudante_id" in migration.splitlines()[2]
    assert "RENAME COLUMN" not in migration
    assert "CHANGE COLUMN motorista_id" not in migration
    assert "CHANGE COLUMN ajudante_id" not in migration
