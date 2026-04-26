rule Detect_http_80 {
    meta:
        description = "Deteccion automatica de servicio identificado por OptiVeil"
        author = "OptiVeil AI - Variacion B"
        date = "2026-04-25"
        target_port = 80
        banner_info = "HTTP/1.1 403 Forbidden"

    strings:
        $service_banner = "HTTP/1.1 403 Forbidden"

    condition:
        $service_banner
}
