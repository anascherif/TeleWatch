"""Serveur de monitoring qui reçoit les métriques des agents."""

import socket
import threading
import logging
import signal
import sys
from datetime import datetime
from config import config, LOGS_DIR
from database import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TeleinfoServer:
    def __init__(self):
        self.host = config.get("server", "host")
        self.port = config.get("server", "port")
        self.db = Database()
        self.clients = {}
        self.running = False
        self.lock = threading.Lock()
    
    def handle_client(self, conn, addr):
        agent_id = None
        try:
            while self.running:
                data = conn.recv(config.get("server", "buffer_size"))
                if not data:
                    break
                
                message = data.decode('utf-8').strip()
                logger.info(f"Reçu de {addr}: {message}")
                
                parts = message.split()
                if not parts:
                    continue
                
                command = parts[0]
                
                if command == "HELLO":
                    if len(parts) >= 3:
                        agent_id = parts[1]
                        hostname = parts[2]
                        self.db.register_agent(agent_id, hostname)
                        with self.lock:
                            self.clients[agent_id] = {"conn": conn, "addr": addr}
                        conn.sendall(b"OK")
                        logger.info(f"Agent enregistré: {agent_id} ({hostname})")
                
                elif command == "REPORT":
                    if len(parts) >= 5 and agent_id:
                        timestamp = int(parts[2])
                        cpu = float(parts[3])
                        ram = float(parts[4])
                        self.db.insert_metric(agent_id, timestamp, cpu, ram)
                        self.db.update_agent_seen(agent_id)
                        conn.sendall(b"OK")
                
                elif command == "BYE":
                    if agent_id:
                        with self.lock:
                            self.clients.pop(agent_id, None)
                        logger.info(f"Agent déconnecté: {agent_id}")
                    conn.sendall(b"OK")
                    break
                
                else:
                    conn.sendall(b"UNKNOWN_COMMAND")
        
        except Exception as e:
            logger.error(f"Erreur avec {addr}: {e}")
        
        finally:
            if agent_id:
                with self.lock:
                    self.clients.pop(agent_id, None)
            conn.close()
    
    def status_thread(self):
        while self.running:
            self.db.close_inactive_agents(minutes=5)
            self.db.cleanup_old_data()
            
            with self.lock:
                active_count = len(self.clients)
            
            agents = self.db.get_agents(active_only=True)
            stats = self.db.get_statistics(hours=1)
            
            logger.info(f"=== Status ===")
            logger.info(f"Agents actifs: {active_count}")
            for agent in agents:
                logger.info(f"  - {agent['agent_id']} ({agent['hostname']}) - vu: {agent['last_seen']}")
            
            if stats:
                for s in stats:
                    logger.info(f"  Stats {s['agent_id']}: CPU avg={s['avg_cpu']:.1f}% RAM avg={s['avg_ram']:.0f}MB")
            
            threading.Event().wait(30)
    
    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(config.get("server", "max_connections"))
            logger.info(f"Serveur démarré sur {self.host}:{self.port}")
            
            status_daemon = threading.Thread(target=self.status_thread, daemon=True)
            status_daemon.start()
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    try:
                        conn, addr = self.server_socket.accept()
                        logger.info(f"Connexion de {addr}")
                        client_thread = threading.Thread(
                            target=self.handle_client,
                            args=(conn, addr),
                            daemon=True
                        )
                        client_thread.start()
                    except socket.timeout:
                        continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Erreur d'acceptation: {e}")
        
        except KeyboardInterrupt:
            logger.info("Interruption clavier")
        finally:
            self.stop()
    
    def stop(self):
        logger.info("Arrêt du serveur...")
        self.running = False
        with self.lock:
            for agent_id, client_info in self.clients.items():
                try:
                    client_info["conn"].close()
                except:
                    pass
            self.clients.clear()
        
        try:
            self.server_socket.close()
        except:
            pass
        
        logger.info("Serveur arrêté")

def main():
    server = TeleinfoServer()
    
    def signal_handler(sig, frame):
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 50)
    print("  TELEINFO MONITORING SERVER")
    print("=" * 50)
    print(f"  IP: {config.get('server', 'host')}")
    print(f"  Port: {config.get('server', 'port')}")
    print(f"  Database: {config.get('database', 'path')}")
    print("=" * 50)
    print("\nCtrl+C pour arrêter\n")
    
    server.start()

if __name__ == "__main__":
    main()
