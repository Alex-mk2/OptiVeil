rule Detect_ftp_21 {
    meta:
        description = "Deteccion automatica de servicio identificado por OptiVeil"
        author = "OptiVeil AI - Variacion B"
        date = "2026-04-25"
        target_port = 21
        banner_info = "220 You will be disconnected after 10 minutes of inactivity."

    strings:
        $service_banner = "220 You will be disconnected after 10 minutes of inactivity."

    condition:
        $service_banner
}

rule Detect_smtp_25 {
    meta:
        description = "Deteccion automatica de servicio identificado por OptiVeil"
        author = "OptiVeil AI - Variacion B"
        date = "2026-04-25"
        target_port = 25
        banner_info = "N/A (Inferred by standard port)"

    strings:
        $service_banner = "N/A (Inferred by standard port)"

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
