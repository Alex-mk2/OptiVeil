import os
import socket
import time
import concurrent.futures
import random
import threading
from scapy.all import IP, TCP, conf, send, sniff

conf.verb = 0


def build_scan_stats(total: int, open_count: int, responded_count: int,
                     attempts: int, recovered_on_retry: int) -> dict:
    """Resume la calidad del escaneo (función pura, testeable).

    - response_rate: fracción de puertos que dieron CUALQUIER respuesta (SYN-ACK o RST).
    - loss_rate: fracción sin respuesta tras los reintentos (filtrados o paquetes perdidos).
    - recovered_on_retry: puertos abiertos detectados solo gracias a los reintentos.
    """
    total = max(total, 0)
    responded_count = min(responded_count, total)
    unanswered = total - responded_count
    rate = (responded_count / total) if total else 0.0
    loss = (1.0 - rate) if total else 0.0
    return {
        "total_ports": total,
        "open_ports": open_count,
        "responded": responded_count,
        "unanswered": unanswered,
        "response_rate": round(rate, 4),
        "loss_rate": round(loss, 4),
        "attempts": attempts,
        "recovered_on_retry": recovered_on_retry,
    }


class StealthScanner:
    def __init__(self, target_ip: str, config: dict):
        self.target_ip = target_ip
        self.wait_time = config["wait_time_ms"] / 1000.0
        self.packet_size = config["packet_size"]
        self.threads = int(config["threads"])
        self.open_ports = []
        self._open_ports_lock = threading.Lock()
        self._responded = set()
        self._stop_sniffer = threading.Event()
        self._scan_completed = threading.Event()
        self._sniffer_thread = None
        self.scan_stats = {}


    def __enter__(self):
        if os.name == 'nt':
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                raise PermissionError(
                    "OptiVeil requiere privilegios de Administrador en Windows.\n"
                    "Ejecuta la terminal como Administrador e intenta de nuevo."
                )

        self._sniffer_thread = threading.Thread(
            target=self._sniffer_worker, daemon=True
        )
        self._sniffer_thread.start()
        time.sleep(0.5)
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and not self._scan_completed.is_set():
            raise RuntimeError(
                "Scanner cerrado antes de completar el escaneo. "
                "Llama a run() antes de salir del contexto."
            )
        self._stop_sniffer.set()
        if self._sniffer_thread:
            self._sniffer_thread.join(timeout=3)
        return False


    def _handle_packet(self, pkt):
        if not (pkt.haslayer(IP) and pkt.haslayer(TCP)):
            return
        if pkt[IP].src != self.target_ip:
            return

        flags = pkt[TCP].flags
        src_port = pkt[TCP].sport

        # Cualquier respuesta (SYN-ACK=open o RST=closed) marca el puerto como
        # "respondido"; lo que no respondió es candidato a reintento.
        if flags == 0x12 or (flags & 0x04):
            with self._open_ports_lock:
                self._responded.add(src_port)

        if flags == 0x12:
            ttl = pkt[IP].ttl
            if ttl <= 64:
                os_guess = "Linux/Unix"
            elif ttl <= 128:
                os_guess = "Windows"
            else:
                os_guess = "Network/Cisco"

            with self._open_ports_lock:
                already_found = any(p[0] == src_port for p in self.open_ports)
                if not already_found:
                    self.open_ports.append((src_port, os_guess))

            if not already_found:
                rst = IP(dst=self.target_ip) / TCP(dport=src_port, flags="R")
                send(rst, verbose=0)


    def _sniffer_worker(self):
        """Usa Scapy sniff() — opera bajo el firewall via Npcap."""
        sniff(
            filter=f"tcp and src host {self.target_ip}",
            prn=self._handle_packet,
            store=False,
            stop_filter=lambda _: self._stop_sniffer.is_set()
        )


    def _craft_and_send(self, dport: int):
        ip_layer = IP(dst=self.target_ip)
        tcp_layer = TCP(dport=dport, flags="S")
        pad_len = max(0, self.packet_size - 40)
        payload = b"\x00" * pad_len
        send(ip_layer / tcp_layer / payload, verbose=0)
        
    
    
    def scan_port(self, port: int):
        self._craft_and_send(port)
        time.sleep(self.wait_time)


    def _send_batch(self, ports: list):
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max(1, min(self.threads, len(ports)))
        ) as executor:
            executor.map(self.scan_port, ports)

    def run(self, ports_to_scan: list, retries: int = 1) -> list:
        """Escanea los puertos con reintentos de los que no respondieron.

        Un SYN-ACK/RST perdido por timing o descarte haría que un puerto abierto
        pase inadvertido; reintentar solo los puertos sin respuesta recupera esos
        casos sin re-sondear todo. Expone métricas en `self.scan_stats`.
        """
        all_ports = list(ports_to_scan)
        random.shuffle(all_ports)
        total = len(all_ports)
        drain_time = max(2.0, self.wait_time * 5)

        pending = all_ports
        attempts = 0
        open_after_first = 0

        for attempt in range(retries + 1):
            if not pending:
                break
            self._send_batch(pending)
            time.sleep(drain_time)
            attempts += 1

            with self._open_ports_lock:
                responded = set(self._responded)
                if attempt == 0:
                    open_after_first = len(self.open_ports)
            pending = [p for p in pending if p not in responded]

        self._scan_completed.set()

        with self._open_ports_lock:
            open_sorted = sorted(self.open_ports, key=lambda x: x[0])
            responded_count = len(self._responded)

        recovered = max(0, len(open_sorted) - open_after_first)
        self.scan_stats = build_scan_stats(
            total=total,
            open_count=len(open_sorted),
            responded_count=responded_count,
            attempts=attempts,
            recovered_on_retry=recovered,
        )
        return open_sorted