"""Lanceur principal du projet Teleinfo Monitor."""

import sys
import argparse
from pathlib import Path

def print_banner():
    banner = """
+=================================================================+
|                                                                 |
|     TELEINFO MONITOR - SYSTEME CLIENT-SERVEUR                  |
|                                                                 |
|     Projet de Telematique / Monitoring en Temps Reel            |
|                                                                 |
+=================================================================+
    """
    print(banner)

def print_menu():
    print("""
+=================================================================+
|                         MENU PRINCIPAL                         |
+=================================================================+
|  [1] Demarrer le SERVEUR (reception des metriques)             |
|  [2] Demarrer le CLIENT (envoi des metriques)                   |
|  [3] Ouvrir le TABLEAU DE BORD (interface graphique)           |
|  [4] Generer les RAPPORTS                                     |
|  [5] Initialiser la BASE DE DONNEES                            |
|  [6] Modifier la CONFIGURATION                                 |
|  [0] Quitter                                                  |
+=================================================================+
""")

def run_server():
    from server import main as server_main
    print("Démarrage du serveur...")
    server_main()

def run_client():
    from client import main as client_main
    print("Démarrage du client...")
    client_main()

def run_gui():
    from gui import main as gui_main
    print("Ouverture de l'interface graphique...")
    gui_main()

def run_reports():
    from reports import main as reports_main
    reports_main()

def init_database():
    from database import Database
    from config import config
    
    print(f"Initialisation de la base de données...")
    print(f"  Emplacement: {config.get('database', 'path')}")
    
    db = Database()
    agents = db.get_agents()
    
    print(f"\nBase de données prête!")
    print(f"  Agents enregistrés: {len(agents)}")
    
    for agent in agents:
        print(f"    - {agent['agent_id']} ({agent['hostname']})")

def edit_config():
    from config import config
    import json
    
    print("\nConfiguration actuelle:")
    print(json.dumps(config._config, indent=2))
    
    print("\nPour modifier, éditez le fichier config.json")
    print("Redémarrez l'application pour prendre en compte les changements.")

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="Teleinfo Monitoring System")
    parser.add_argument('mode', nargs='?', choices=['server', 'client', 'gui', 'reports', 'init'],
                       help='Mode de fonctionnement')
    parser.add_argument('--config', action='store_true', help='Afficher la configuration')
    
    args = parser.parse_args()
    
    if args.config:
        from config import config
        import json
        print(json.dumps(config._config, indent=2))
        return
    
    if args.mode:
        modes = {
            'server': run_server,
            'client': run_client,
            'gui': run_gui,
            'reports': run_reports,
            'init': init_database
        }
        modes[args.mode]()
        return
    
    while True:
        print_menu()
        choice = input("Votre choix: ").strip()
        
        if choice == '1':
            run_server()
        elif choice == '2':
            run_client()
        elif choice == '3':
            run_gui()
        elif choice == '4':
            run_reports()
        elif choice == '5':
            init_database()
        elif choice == '6':
            edit_config()
        elif choice == '0':
            print("\nAu revoir!\n")
            sys.exit(0)
        else:
            print("\n⚠️  Choix invalide. Veuillez réessayer.\n")

if __name__ == "__main__":
    main()
