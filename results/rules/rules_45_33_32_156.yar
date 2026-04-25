rule Detect_ssh_22 {
    meta:
        description = "Deteccion automatica de servicio identificado por OptiVeil"
        author = "OptiVeil AI - Variacion B"
        date = "2026-04-25"
        target_port = 22
        banner_info = "SSH-2.0-OpenSSH_6.6.1p1 Ubuntu-2ubuntu2.13"

    strings:
        $service_banner = "SSH-2.0-OpenSSH_6.6.1p1 Ubuntu-2ubuntu2.13"

    condition:
        $service_banner
}

rule Detect_http_80 {
    meta:
        description = "Deteccion automatica de servicio identificado por OptiVeil"
        author = "OptiVeil AI - Variacion B"
        date = "2026-04-25"
        target_port = 80
        banner_info = "HTTP/1.1 200 OK"

    strings:
        $service_banner = "HTTP/1.1 200 OK"

    condition:
        $service_banner
}
