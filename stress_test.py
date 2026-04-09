"""Script de Stress Test - Envoi massif de metriques au serveur."""

import socket
import time
import random
import platform
import threading
import argparse
from datetime import datetime
from config import config

class StressTest:
    def __init__(self, agent_id=None, count=1000, delay=0):
        self.server_ip = config.get("client", "server_ip")
        self.server_port = config.get("client", "server_port")
        self.agent_id = agent_id or f"stress_{random.randint(1000,9999)}"
        self.hostname = platform.node()
        self.target_count = count
        self.delay = delay
        self.socket = None
        self.stats = {
            "sent": 0,
            "failed": 0,
            "total_time": 0,
            "response_times": [],
            "start_time": 0
        }
    
    def connect(self):
        print(f"[{self.timestamp()}] Connexion au serveur {self.server_ip}:{self.server_port}...")
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.server_ip, self.server_port))
            
            hello_msg = f"HELLO {self.agent_id} {self.hostname}\n"
            self.socket.sendall(hello_msg.encode('utf-8'))
            
            response = self.socket.recv(1024).decode('utf-8').strip()
            if response == "OK":
                print(f"[{self.timestamp()}] Connexion etablie!")
                return True
            else:
                print(f"[{self.timestamp()}] Erreur: Reponse serveur = {response}")
                return False
        except ConnectionRefusedError:
            print(f"[ERREUR] Connexion refusee. Le serveur est-il lance?")
            print(f"[ERREUR] Lancez d'abord: python main.py server")
            return False
        except socket.timeout:
            print(f"[ERREUR] Delai de connexion expire")
            return False
        except Exception as e:
            print(f"[ERREUR] Erreur de connexion: {e}")
            return False
    
    def send_burst(self):
        try:
            cpu = round(random.uniform(5.0, 95.0), 2)
            ram = round(random.uniform(512.0, 8192.0), 2)
            timestamp = int(time.time())
            
            start = time.perf_counter()
            
            report_msg = f"REPORT {self.agent_id} {timestamp} {cpu} {ram}\n"
            self.socket.sendall(report_msg.encode('utf-8'))
            
            response = self.socket.recv(1024).decode('utf-8').strip()
            
            elapsed = (time.perf_counter() - start) * 1000
            
            if response == "OK":
                self.stats["sent"] += 1
                self.stats["response_times"].append(elapsed)
                return True
            else:
                self.stats["failed"] += 1
                return False
        except Exception as e:
            self.stats["failed"] += 1
            return False
    
    def run_continuous(self, duration=60):
        if not self.connect():
            return
        
        print(f"\n{'='*50}")
        print(f"  STRESS TEST - MODE CONTINU")
        print(f"{'='*50}")
        print(f"  Duree: {duration} secondes")
        print(f"  Cible: {self.server_ip}:{self.server_port}")
        print(f"{'='*50}\n")
        
        self.stats["start_time"] = time.time()
        self.stats["peak_speed"] = 0
        
        start = time.time()
        batch_start = start
        batch_count = 0
        
        try:
            while time.time() - start < duration:
                if self.send_burst():
                    batch_count += 1
                    
                    if self.delay > 0:
                        time.sleep(self.delay)
                    
                    now = time.time()
                    if now - batch_start >= 1.0:
                        speed = batch_count / (now - batch_start)
                        self.stats["peak_speed"] = max(self.stats["peak_speed"], speed)
                        
                        elapsed = now - self.stats["start_time"]
                        avg_speed = self.stats["sent"] / elapsed if elapsed > 0 else 0
                        
                        print(f"[{self.timestamp()}] {self.stats['sent']} envois | "
                              f"{speed:.0f}/s | Avg: {avg_speed:.0f}/s | "
                              f"Failed: {self.stats['failed']}")
                        
                        batch_count = 0
                        batch_start = now
            
            self.print_stats()
        
        except KeyboardInterrupt:
            print(f"\n[{self.timestamp()}] Arret demande par l'utilisateur...")
            self.print_stats()
        
        finally:
            self.disconnect()
    
    def run_burst(self, count=None):
        if not self.connect():
            return
        
        target = count or self.target_count
        
        print(f"\n{'='*50}")
        print(f"  STRESS TEST - MODE BURST")
        print(f"{'='*50}")
        print(f"  Nombre de rapports: {target}")
        print(f"  Cible: {self.server_ip}:{self.server_port}")
        print(f"{'='*50}\n")
        
        self.stats["start_time"] = time.time()
        start = time.perf_counter()
        
        try:
            for i in range(target):
                success = self.send_burst()
                
                if self.delay > 0 and i < target - 1:
                    time.sleep(self.delay)
                
                if (i + 1) % 100 == 0:
                    elapsed = time.perf_counter() - start
                    speed = (i + 1) / elapsed
                    print(f"Progression: {i+1}/{target} ({speed:.0f} msg/s)")
            
            self.stats["total_time"] = time.perf_counter() - start
            self.print_stats()
        
        except KeyboardInterrupt:
            print(f"\n[{self.timestamp()}] Arret demande...")
            self.stats["total_time"] = time.perf_counter() - start
            self.print_stats()
        
        finally:
            self.disconnect()
    
    def run_flood(self, duration=30):
        if not self.connect():
            return
        
        print(f"\n{'='*50}")
        print(f"  FLOOD ATTACK SIMULATION")
        print(f"{'='*50}")
        print(f"  Mode: ENVOI MASSIF SANS DELAI")
        print(f"  Duree: {duration} secondes")
        print(f"  Cible: {self.server_ip}:{self.server_port}")
        print(f"{'='*50}")
        print(f"  ATTENTION: Ce test envoie le maximum de requetes possibles\n")
        
        self.stats["start_time"] = time.time()
        start = time.perf_counter()
        
        try:
            while time.time() - start < duration:
                self.send_burst()
                
                if self.stats["sent"] % 500 == 0 and self.stats["sent"] > 0:
                    elapsed = time.perf_counter() - start
                    speed = self.stats["sent"] / elapsed
                    print(f"[{self.timestamp()}] Flood: {self.stats['sent']} @ {speed:.0f} msg/s")
            
            self.stats["total_time"] = time.perf_counter() - start
            self.print_stats()
        
        except KeyboardInterrupt:
            print(f"\n[{self.timestamp()}] Arret flood...")
            self.stats["total_time"] = time.perf_counter() - start
            self.print_stats()
        
        finally:
            self.disconnect()
    
    def run_multi_threaded(self, threads=5, duration=30):
        print(f"\n{'='*50}")
        print(f"  STRESS TEST - MULTI-THREADED")
        print(f"{'='*50}")
        print(f"  Threads: {threads}")
        print(f"  Duree: {duration} secondes")
        print(f"  Cible: {self.server_ip}:{self.server_port}")
        print(f"{'='*50}\n")
        
        print(f"[{self.timestamp()}] Verification de la connexion au serveur...")
        
        test_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_conn.settimeout(5)
        try:
            test_conn.connect((self.server_ip, self.server_port))
            test_conn.close()
            print(f"[{self.timestamp()}] Serveur joignable. Demarrage des threads...\n")
        except Exception as e:
            print(f"\n[ERREUR] Serveur non joignable sur {self.server_ip}:{self.server_port}")
            print(f"[ERREUR] Assurez-vous que le serveur est lance (python main.py server)")
            return
        
        results = {}
        lock = threading.Lock()
        
        def worker(thread_id):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((self.server_ip, self.server_port))
                
                agent_id = f"{self.agent_id}_t{thread_id}"
                hello_msg = f"HELLO {agent_id} {self.hostname}\n"
                sock.sendall(hello_msg.encode('utf-8'))
                response = sock.recv(1024).decode('utf-8').strip()
                
                if response != "OK":
                    print(f"[Thread-{thread_id}] Erreur inscription: {response}")
                    sock.close()
                    return
                
                thread_start = time.time()
                count = 0
                
                while time.time() - thread_start < duration:
                    cpu = round(random.uniform(5.0, 95.0), 2)
                    ram = round(random.uniform(512.0, 8192.0), 2)
                    timestamp = int(time.time())
                    
                    report_msg = f"REPORT {agent_id} {timestamp} {cpu} {ram}\n"
                    sock.sendall(report_msg.encode('utf-8'))
                    sock.recv(1024)
                    count += 1
                
                bye_msg = f"BYE {agent_id}\n"
                sock.sendall(bye_msg.encode('utf-8'))
                sock.recv(1024)
                sock.close()
                
                with lock:
                    results[thread_id] = count
                print(f"[Thread-{thread_id}] Termine: {count} envois")
            
            except Exception as e:
                print(f"[Thread-{thread_id}] Erreur: {e}")
                with lock:
                    results[thread_id] = 0
        
        thread_list = []
        for i in range(threads):
            t = threading.Thread(target=worker, args=(i,))
            t.start()
            thread_list.append(t)
        
        for t in thread_list:
            t.join()
        
        total = sum(results.values())
        print(f"\n[{self.timestamp()}] Tous les threads termines")
        print(f"[{self.timestamp()}] Total des envois: {total}")
    
    def print_stats(self):
        elapsed = self.stats.get("total_time", time.time() - self.stats.get("start_time", time.time()))
        
        total = self.stats["sent"] + self.stats["failed"]
        success_rate = (self.stats["sent"] / total * 100) if total > 0 else 0
        
        avg_response = sum(self.stats["response_times"]) / len(self.stats["response_times"]) if self.stats["response_times"] else 0
        min_response = min(self.stats["response_times"]) if self.stats["response_times"] else 0
        max_response = max(self.stats["response_times"]) if self.stats["response_times"] else 0
        
        avg_speed = self.stats["sent"] / elapsed if elapsed > 0 else 0
        
        print(f"\n{'='*50}")
        print(f"  RAPPORT DE STRESS TEST")
        print(f"{'='*50}")
        print(f"  Agent: {self.agent_id}")
        print(f"  Duree: {elapsed:.2f} secondes")
        print(f"  ---------------------------")
        print(f"  Envoye: {self.stats['sent']}")
        print(f"  Echoue: {self.stats['failed']}")
        print(f"  Total: {total}")
        print(f"  Taux de reussite: {success_rate:.1f}%")
        print(f"  ---------------------------")
        print(f"  Vitesse moyenne: {avg_speed:.1f} msg/s")
        if hasattr(self.stats, 'peak_speed'):
            print(f"  Vitesse max: {self.stats['peak_speed']:.1f} msg/s")
        print(f"  ---------------------------")
        print(f"  Temps de reponse moyen: {avg_response:.2f}ms")
        print(f"  Temps de reponse min: {min_response:.2f}ms")
        print(f"  Temps de reponse max: {max_response:.2f}ms")
        print(f"{'='*50}\n")
    
    def disconnect(self):
        if self.socket:
            try:
                bye_msg = f"BYE {self.agent_id}\n"
                self.socket.sendall(bye_msg.encode('utf-8'))
                self.socket.recv(1024)
            except:
                pass
            self.socket.close()
            self.socket = None
    
    def timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

def main():
    parser = argparse.ArgumentParser(description="Stress Test pour Teleinfo Monitor")
    parser.add_argument('--mode', choices=['burst', 'continuous', 'flood', 'multi'], 
                       default='burst', help='Mode de test')
    parser.add_argument('--count', type=int, default=1000, help='Nombre de rapports (burst)')
    parser.add_argument('--duration', type=int, default=30, help='Duree en secondes')
    parser.add_argument('--threads', type=int, default=5, help='Nombre de threads (multi)')
    parser.add_argument('--delay', type=float, default=0, help='Delai entre envois (secondes)')
    parser.add_argument('--agent', type=str, help='ID de lagent')
    
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print("  TELEINFO - STRESS TEST")
    print("="*50)
    
    test = StressTest(agent_id=args.agent, count=args.count, delay=args.delay)
    
    if args.mode == 'burst':
        test.run_burst(count=args.count)
    elif args.mode == 'continuous':
        test.run_continuous(duration=args.duration)
    elif args.mode == 'flood':
        test.run_flood(duration=args.duration)
    elif args.mode == 'multi':
        test.run_multi_threaded(threads=args.threads, duration=args.duration)

if __name__ == "__main__":
    main()
