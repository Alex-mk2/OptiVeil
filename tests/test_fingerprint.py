"""Tests del identificador de servicios y cálculo de riesgo."""
import pytest

from inter.fingerprint import ServiceIdentifier


@pytest.fixture
def ident():
    return ServiceIdentifier(timeout=1)


def test_analyze_banner_ssh(ident):
    res = ident._analyze_banner(b"SSH-2.0-OpenSSH_8.2p1 Ubuntu\r\n", 22)
    assert res["service"] == "ssh"
    assert "OpenSSH_8.2p1" in res["banner"]


def test_analyze_banner_http(ident):
    res = ident._analyze_banner(b"HTTP/1.1 200 OK\r\nServer: nginx\r\n", 80)
    assert res["service"] == "http"


def test_analyze_banner_desconocido(ident):
    res = ident._analyze_banner(b"\x01\x02 basura binaria sin firma", 9999)
    assert res["service"] == "unknown"


@pytest.mark.parametrize("servicio", ["smb", "rdp", "telnet"])
def test_riesgo_servicios_criticos(ident, servicio):
    assert ident._calculate_risk(servicio, "").startswith("CRITICAL")


def test_riesgo_openssh_obsoleto(ident):
    assert ident._calculate_risk("ssh", "SSH-2.0-OpenSSH_6.6").startswith("HIGH")


def test_riesgo_ssh_moderno_es_bajo(ident):
    assert ident._calculate_risk("ssh", "SSH-2.0-OpenSSH_9.3").startswith("LOW")


def test_riesgo_vsftpd_backdoor(ident):
    assert "CVE-2011-2523" in ident._calculate_risk("ftp", "220 vsftpd 2.3.4 ready")


def test_riesgo_ftp_generico_medio(ident):
    assert ident._calculate_risk("ftp", "220 ProFTPD").startswith("MEDIUM")


def test_riesgo_desconocido_info(ident):
    assert ident._calculate_risk("unknown", None).startswith("INFO")


def test_identify_adjunta_riesgo_por_puerto_inferido(ident, monkeypatch):
    """Si la conexión falla, infiere el servicio por puerto y SIEMPRE añade riesgo."""
    import inter.fingerprint as fp

    def _boom(*args, **kwargs):
        raise OSError("sin conexion")

    monkeypatch.setattr(fp.socket, "create_connection", _boom)

    res = ident.identify("10.0.0.1", 22)
    assert res["service"] == "ssh"
    assert "risk" in res
    assert res["risk"].startswith("LOW")


def test_identify_riesgo_info_en_puerto_no_estandar(ident, monkeypatch):
    import inter.fingerprint as fp
    monkeypatch.setattr(fp.socket, "create_connection",
                        lambda *a, **k: (_ for _ in ()).throw(OSError()))
    res = ident.identify("10.0.0.1", 9999)
    assert res["service"] == "unknown"
    assert res["risk"].startswith("INFO")
