"""Tests del parser de salida XML de Nmap (función pura)."""
import xml.etree.ElementTree as ET
import pytest

from src.api.routers.scanner import parse_nmap_xml


NMAP_XML = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="8.2"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="closed"/>
        <service name="http"/>
      </port>
      <port protocol="tcp" portid="443">
        <state state="open"/>
        <service name="https"/>
      </port>
    </ports>
  </host>
</nmaprun>"""


def test_solo_puertos_abiertos():
    res = parse_nmap_xml(NMAP_XML)
    puertos = {r["port"] for r in res}
    assert puertos == {22, 443}  # 80 está cerrado -> excluido


def test_banner_de_producto_y_version():
    res = parse_nmap_xml(NMAP_XML)
    ssh = next(r for r in res if r["port"] == 22)
    assert ssh["service"] == "SSH"
    assert ssh["banner"] == "OpenSSH 8.2"


def test_banner_oculto_sin_producto():
    res = parse_nmap_xml(NMAP_XML)
    https = next(r for r in res if r["port"] == 443)
    assert https["banner"] == "BANNER OCULTO"


def test_xml_vacio_devuelve_lista_vacia():
    assert parse_nmap_xml("<nmaprun></nmaprun>") == []


def test_xml_invalido_lanza_parseerror():
    with pytest.raises(ET.ParseError):
        parse_nmap_xml("esto no es xml <<<")
