"""SPEC-0007: matcher de datos sensibles (puro, sin red)."""
from inter.sensitive_data import validate_rut, find_sensitive, mask_pii_in_text

RUT_VALIDO_BODY, RUT_VALIDO_DV = "12345678", "5"   # 12.345.678-5 es válido (módulo 11)


def test_validate_rut_valido():
    assert validate_rut("12.345.678", "5") is True
    assert validate_rut("11111111", "1") is True


def test_validate_rut_invalido():
    assert validate_rut("12345678", "9") is False
    assert validate_rut("no-es-rut", "5") is False


def test_find_sensitive_rut_valido_enmascarado():
    out = find_sensitive("cliente con rut 12.345.678-5 en el sistema")
    kinds = {m["kind"] for m in out}
    assert "rut" in kinds
    # nunca el RUT completo en claro
    dump = str(out)
    assert "12345678" not in dump and "12.345.678" not in dump


def test_find_sensitive_rut_invalido_no_dispara():
    out = find_sensitive("numero 12.345.678-9 cualquiera")
    assert all(m["kind"] != "rut" for m in out)


def test_find_sensitive_email_y_env_y_dirlisting():
    assert any(m["kind"] == "email" for m in find_sensitive("correo juan@acme.cl aquí"))
    assert any(m["kind"] == "env-file" for m in find_sensitive("API_URL=http://x\nDB_HOST=db"))
    assert any(m["kind"] == "secret" for m in find_sensitive("token=abc.def.ghi"))
    assert any(m["kind"] == "directory-listing" for m in find_sensitive("<title>Index of /</title>"))


def test_find_sensitive_vacio():
    assert find_sensitive("") == []
    assert find_sensitive("nada interesante por aquí") == []


def test_mask_pii_in_text_no_filtra():
    masked = mask_pii_in_text("rut 12.345.678-5 y correo juan@acme.cl")
    assert "12345678" not in masked and "12.345.678" not in masked
    assert "juan@acme.cl" not in masked
