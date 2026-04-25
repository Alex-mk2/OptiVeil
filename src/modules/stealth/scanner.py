import os
import socket
import time
import concurrent.futures
import random
import threading
from scapy.all import IP, TCP, conf, send, sniff

conf.verb = 0


class StealthScanner:
    def __init__(self, target_ip: str, config: dict):
        self.target_ip = target_ip
        self.wait_time = config["wait_time_ms"] / 1000.0
        self.packet_size = config["packet_size"]
        self.threads = int(config["threads"])
        self.open_ports = []
        self._open_ports_lock = threading.Lock()
        self._stop_sniffer = threading.Event()
        self._scan_completed = threading.Event()
        self._sniffer_thread = None

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
        """Callback de Scapy: procesa cada paquete capturado."""
        if not (pkt.haslayer(IP) and pkt.haslayer(TCP)):
            return
        if pkt[IP].src != self.target_ip:
            return

        flags = pkt[TCP].flags
        src_port = pkt[TCP].sport

        
        if flags == 0x12:
            with self._open_ports_lock:
                already_found = src_port in self.open_ports
                if not already_found:
                    self.open_ports.append(src_port)

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

    def run(self, ports_to_scan: list) -> list:
        random.shuffle(ports_to_scan)

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.threads
        ) as executor:
            executor.map(self.scan_port, ports_to_scan)

        
        drain_time = max(2.0, self.wait_time * 5)
        time.sleep(drain_time)

        self._scan_completed.set()
        return sorted(self.open_ports)