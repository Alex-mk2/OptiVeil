import socket
import re


class ServiceIdentifier:
    def __init__(self, timeout=2):
        self.timeout = timeout
        self.signatures = {
            "ssh": r"(SSH-\d+\.\d+-[^\r\n]+)",
            "http": r"(HTTP/\d+\.\d+\s+\d+\s+[^\r\n]+)",
            "ftp": r"(220\s+[^\r\n]+)",
            "mysql": r"(.+mysql_native_password.*)",
            "rdp": r"^\x03\x00\x00\x13", 
            "smb": r"(\xffSMB[\x00-\xff]*)", 
            "vnc": r"(RFB\s+\d+\.\d+)",
            "redis": r"(-ERR\s+.*password.*|PONG)"
        }
    
    
    def identify(self, ip: str, port: int) -> dict:
        try:
            with socket.create_connection((ip, port), timeout=self.timeout) as sock:
                if port in [80, 443, 8080, 8443]:
                    sock.sendall(b"HEAD / HTTP/1.0\r\nHost: " + ip.encode() + b"\r\n\r\n")
                elif port == 3389:
                    sock.sendall(b"\x03\x00\x00\x13\x0e\xe0\x00\x00\x00\x00\x00\x01\x00\x08\x00\x03\x00\x00\x00")
                elif port == 445:
                    sock.sendall(b"\x00\x00\x00\x2f\xff\x53\x4d\x42\x72\x00\x00\x00\x00\x18\x53\xc8\x00\x00")

                banner_bytes = sock.recv(2048)
                return self._analyze_banner(banner_bytes, port)

        except (socket.timeout, ConnectionRefusedError, OSError):
            return {"port": port, "service": "unknown", "banner": None}

    def _analyze_banner(self, banner_bytes: bytes, port: int) -> dict:
        banner_text = banner_bytes.decode(errors="ignore").strip()
        result = {"port": port, "service": "unknown", "banner": banner_text[:100]}
        
        for service, pattern in self.signatures.items():
            if isinstance(pattern, str):
                match = re.search(pattern, banner_text, re.IGNORECASE)
                if match:
                    result["service"] = service
                    result["banner"] = match.group(1) if match.groups() else banner_text[:100]
                    break
            else:
                if pattern in banner_bytes:
                    result["service"] = service
                    result["banner"] = f"Binary match for {service.upper()}"
                    break
        return result