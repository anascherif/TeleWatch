"""Client de monitoring qui envoie les métriques système au serveur."""

import socket
import time
import platform
import random
import signal
import sys
import threading
import json
from datetime import datetime
from config import config, LOGS_DIR

class TeleinfoClient:
    def __init__(self):
        self.server_ip = config.get("client", "server_ip")
        self.server_port = config.get("client", "server_port")
        self.period = config.get("client", "period")
        self.agent_id = config.get("client", "agent_id") or f"agent_{random.randint(1000,9999)}"
        self.hostname = platform.node()
        self.running = True
        self.connected = False
        self.retry_delay = config.get("client", "retry_delay")
        self.max_retries = config.get("client", "max_retries")
        self.socket = None
        self.stats = {"sent": 0, "failed": 0, "start_time": time.time()}
        self.lock = threading.Lock()
    
    def get_system_metrics(self):
        cpu_pct = round(random.uniform(5.0, 85.0), 2)
        ram_mb = round(random.uniform(512.0, 8192.0), 2)
        
        try:
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'loadpercentage'],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        cpu_pct = float(lines[1].strip())
            
            elif platform.system() == "Linux":
                try:
                    with open('/proc/loadavg', 'r') as f:
                        load = float(f.read().split()[0])
                        cpu_pct = min(load * 25, 100)
                except:
                    pass
        except:
            pass
        
        return cpu_pct, ram_mb
    
    def connect(self):
        retries = 0
        while retries < self.max_retries and self.running:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10)
                self.socket.connect((self.server_ip, self.server_port))
                
                hello_msg = f"HELLO {self.agent_id} {self.hostname}\n"
                self.socket.sendall(hello_msg.encode('utf-8'))
                
                response = self.socket.recv(1024).decode('utf-8').strip()
                if response == "OK":
                    self.connected = True
                    print(f"[{self.timestamp()}] Connecté au serveur {self.server_ip}:{self.server_port}")
                    return True
                else:
                    print(f"[{self.timestamp()}] Réponse serveur invalide: {response}")
            
            except (ConnectionRefusedError, socket.timeout) as e:
                retries += 1
                wait = self.retry_delay * min(retries, 5)
                print(f"[{self.timestamp()}] Connexion échouée (tentative {retries}/{self.max_retries}): {e}")
                print(f"[{self.timestamp()}] Nouvelle tentative dans {wait}s...")
                time.sleep(wait)
            
            except Exception as e:
                print(f"[{self.timestamp()}] Erreur: {e}")
                break
        
        return False
    
    def disconnect(self):
        if self.socket and self.connected:
            try:
                bye_msg = f"BYE {self.agent_id}\n"
                self.socket.sendall(bye_msg.encode('utf-8'))
                response = self.socket.recv(1024).decode('utf-8').strip()
                print(f"[{self.timestamp()}] Déconnexion: {response}")
            except:
                pass
        
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False
    
    def send_report(self):
        cpu, ram = self.get_system_metrics()
        timestamp = int(time.time())
        
        try:
            report_msg = f"REPORT {self.agent_id} {timestamp} {cpu} {ram}\n"
            self.socket.sendall(report_msg.encode('utf-8'))
            
            response = self.socket.recv(1024).decode('utf-8').strip()
            
            if response == "OK":
                with self.lock:
                    self.stats["sent"] += 1
                return True
            else:
                with self.lock:
                    self.stats["failed"] += 1
                print(f"[{self.timestamp()}] Erreur serveur: {response}")
                return False
        
        except socket.timeout:
            with self.lock:
                self.stats["failed"] += 1
            return False
        except Exception as e:
            with self.lock:
                self.stats["failed"] += 1
            print(f"[{self.timestamp()}] Erreur envoi: {e}")
            return False
    
    def timestamp(self):
        return datetime.now().strftime("%H:%M:%S")
    
    def print_stats(self):
        uptime = time.time() - self.stats["start_time"]
        total = self.stats["sent"] + self.stats["failed"]
        success_rate = (self.stats["sent"] / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 40)
        print(f"  STATISTIQUES CLIENT {self.agent_id}")
        print("=" * 40)
        print(f"  Uptime: {int(uptime)}s")
        print(f"  Rapports envoyés: {self.stats['sent']}")
        print(f"  Échecs: {self.stats['failed']}")
        print(f"  Taux de succès: {success_rate:.1f}%")
        print("=" * 40)
    
    def run(self):
        print("=" * 50)
        print("  TELEINFO MONITORING CLIENT")
        print("=" * 50)
        print(f"  Agent ID: {self.agent_id}")
        print(f"  Hostname: {self.hostname}")
        print(f"  Serveur: {self.server_ip}:{self.server_port}")
        print(f"  Période: {self.period}s")
        print("=" * 50)
        
        def signal_handler(sig, frame):
            print(f"\n[{self.timestamp()}] Arrêt en cours...")
            self.running = False
            self.disconnect()
            self.print_stats()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while self.running:
            if not self.connected:
                if not self.connect():
                    continue
            
            if self.send_report():
                pass
            else:
                self.connected = False
                continue
            
            time.sleep(self.period)

def main():
    client = TeleinfoClient()
    client.run()

if __name__ == "__main__":
    main()
