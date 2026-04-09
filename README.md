# Teleinfo Monitor - Système de Monitoring Client-Serveur

> **Projet de Téléinformatique** - Application Python pour la surveillance des ressources système en temps réel via communication réseau TCP/IP.

---

## 📋 Table des Matières

1. [Description du Projet](#-description-du-projet)
2. [Architecture Générale](#-architecture-generale)
3. [Installation et Lancement](#-installation-et-lancement)
4. [Protocole de Communication](#-protocole-de-communication)
5. [Structure de la Base de Données](#-structure-de-la-base-de-donnees)
6. [Description des Fichiers](#-description-des-fichiers)
7. [Format des Rapports](#-format-des-rapports)
8. [Configuration](#-configuration)
9. [Guide d'Utilisation](#-guide-dutilisation)
10. [Stress Test](#-stress-test)
11. [Exemples de Sortie](#-exemples-de-sortie)
12. [FAQ](#-faq)

---

## 🎯 Description du Projet

### Objectif

Créer un système de **monitoring distribué** permettant de :

- Collecter les métriques système (CPU, RAM) depuis plusieurs machines
- Transmettre ces données en temps réel via TCP/IP
- Stocker les données dans une base SQLite
- Générer des rapports automatiques (JSON, CSV, HTML)

### Caractéristiques Techniques

| Caractéristique     | Valeur                     |
| ------------------- | -------------------------- |
| Langage             | Python 3.11+               |
| Protocole           | TCP/IP (Socket)            |
| Base de données     | SQLite                     |
| Interface graphique | Tkinter                    |
| Dépendances         | Aucune (stdlib uniquement) |
| Port par défaut     | 65432                      |

---

## 🏗️ Architecture Générale

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ARCHITECTURE DU SYSTÈME                        │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
    │   CLIENT 1   │         │   CLIENT 2   │         │   CLIENT N   │
    │ (Machine A)  │         │ (Machine B)  │         │ (Machine C)  │
    └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
           │                       │                       │
           │  HELLO / REPORT / BYE │                       │
           ▼                       ▼                       ▼
    ════════════════════════════════════════════════════════════════
                          RÉSEAU TCP/IP
                         Port: 65432
    ════════════════════════════════════════════════════════════════
           │                       │                       │
           ▼                       ▼                       ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                        SERVEUR                                │
    │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐  │
    │  │  Accepte   │→ │  Traite    │→ │  Stocke en base        │  │
    │  │ connexions │  │  messages  │  │  de données           │  │
    │  └────────────┘  └────────────┘  └────────────────────────┘  │
    └──────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                     BASE DE DONNÉES SQLite                    │
    │  ┌─────────────────────┐    ┌─────────────────────────────┐ │
    │  │     Table: agents   │    │      Table: metrics         │ │
    │  │  - agent_id (PK)   │    │  - id (PK)                 │ │
    │  │  - hostname        │    │  - agent_id (FK)           │ │
    │  │  - first_seen      │    │  - timestamp               │ │
    │  │  - last_seen       │    │  - cpu_percent            │ │
    │  │  - active          │    │  - ram_mb                 │ │
    │  └─────────────────────┘    └─────────────────────────────┘ │
    └──────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌──────────┐   ┌──────────┐   ┌──────────┐
              │ RAPPORTS │   │INTERFACE │   │  LOGS    │
              │  JSON/   │   │ GRAPHIQUE│   │          │
              │ CSV/HTML │   │  (GUI)   │   │          │
              └──────────┘   └──────────┘   └──────────┘
```

### Flux de Données

```
1. CLIENT → Connecte au serveur
2. CLIENT → Envoie "HELLO agent_id hostname"
3. SERVEUR → Répond "OK", enregistre l'agent
4. CLIENT → Toutes les 5 secondes: "REPORT agent_id timestamp cpu ram"
5. SERVEUR → Répond "OK", stocke les données
6. CLIENT → Ctrl+C → Envoie "BYE agent_id"
7. SERVEUR → Répond "OK", ferme la connexion
```

---

## 🚀 Installation et Lancement

### Prérequis

- Python 3.7+ installé
- Aucun module externe requis (bibliothèque standard uniquement)

### Étape 1 : Lancer le Serveur (récepteur)

```bash
# Naviguer vers le dossier du projet
ouvrir le terminal dans le dossier du projet

# Lancer le serveur
python main.py server
```

**Sortie attendue :**

```
================================================================
  TELEINFO MONITORING SERVER
================================================================
  IP: 0.0.0.0
  Port: 65432
  Database: C:\Users\*********\********\Desktop\teleinfo\data\teleinfo.db
================================================================

Ctrl+C pour arreter

2026-04-09 19:35:44 - INFO - Serveur demarre sur 0.0.0.0:65432
```

### Étape 2 : Lancer le Client (émetteur)

Ouvrir un **nouveau terminal** :

```bash
cd C:\Users\DELL 5420\OneDrive\Desktop\teleinfo
python main.py client
```

**Sortie attendue :**

```
================================================================
  TELEINFO MONITORING CLIENT
================================================================
  Agent ID: agent_default
  Hostname: DELL5420
  Serveur: 127.0.0.1:65432
  Periode: 5s
================================================================

[19:35:45] Connecte au serveur 127.0.0.1:65432
[19:35:45] CPU: 45.2% | RAM: 2048.0 MB
[19:35:50] CPU: 52.1% | RAM: 2100.0 MB
[19:35:55] CPU: 38.7% | RAM: 1980.0 MB
```

### Étape 3 : Interface Graphique (optionnel)

Ouvrir un **troisième terminal** :

```bash
python main.py gui
```

### Étape 4 : Générer des Rapports

```bash
python main.py reports
```

Choisir :

- `1` - Rapport résumé
- `2` - Rapport détaillé par agent
- `3` - Rapport comparatif
- `4` - Rapport d'alertes
- `5` - Exporter en CSV
- `6` - Générer tous les rapports

---

## 📡 Protocole de Communication

### Vue d'Ensemble

Le système utilise un protocole texte simple sur TCP/IP pour la communication client-serveur.

### Format des Messages

#### 1. HELLO (Connexion initiale)

```
CLIENT → SERVEUR:  HELLO <agent_id> <hostname>\n
SERVEUR → CLIENT:  OK\n
```

**Exemple :**

```
CLIENT → SERVEUR:  HELLO agent_001 MON-PC\n
SERVEUR → CLIENT:  OK\n
```

#### 2. REPORT (Envoi de métriques)

```
CLIENT → SERVEUR:  REPORT <agent_id> <timestamp> <cpu_percent> <ram_mb>\n
SERVEUR → CLIENT:  OK\n
```

**Exemple :**

```
CLIENT → SERVEUR:  REPORT agent_001 1712679345 45.23 2048.5\n
SERVEUR → CLIENT:  OK\n
```

**Description des champs :**
| Champ | Type | Description |
|-------|------|-------------|
| agent_id | string | Identifiant unique de l'agent |
| timestamp | integer | Unix timestamp (secondes depuis 1970) |
| cpu_percent | float | Pourcentage d'utilisation CPU (0-100) |
| ram_mb | float | Mémoire RAM utilisée en Mo |

#### 3. BYE (Déconnexion)

```
CLIENT → SERVEUR:  BYE <agent_id>\n
SERVEUR → CLIENT:  OK\n
```

**Exemple :**

```
CLIENT → SERVEUR:  BYE agent_001\n
SERVEUR → CLIENT:  OK\n
```

### Diagramme de Séquence

```
Client          Serveur           Base de Données
  │                │                     │
  │── HELLO ──────>│                     │
  │                │── register_agent()─>│
  │<── OK ─────────│                     │
  │                │                     │
  │── REPORT ──────>│                     │
  │                │── insert_metric()──>│
  │<── OK ─────────│                     │
  │                │                     │
  │ (répète toutes les 5s)               │
  │                │                     │
  │── BYE ─────────>│                     │
  │                │                     │
  │<── OK ─────────│                     │
```

---

## 💾 Structure de la Base de Données

### Schéma Entité-Association

```
┌─────────────────┐          ┌─────────────────┐
│     agents      │          │    metrics      │
├─────────────────┤          ├─────────────────┤
│ id (PK)         │──┐       │ id (PK)         │
│ agent_id (UK)   │  │       │ agent_id (FK)   │──┐
│ hostname        │  └───────│ timestamp       │  │
│ first_seen      │          │ cpu_percent     │  │
│ last_seen       │          │ ram_mb          │  │
│ active          │          │ recorded_at     │  │
└─────────────────┘          └─────────────────┘  │
                                                 │
                                           référence vers
                                           agents.agent_id
```

### Table : agents

```sql
CREATE TABLE agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT UNIQUE NOT NULL,      -- ID unique de l'agent
    hostname TEXT,                       -- Nom de la machine
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Première connexion
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    -- Dernière connexion
    active INTEGER DEFAULT 1             -- 1=connecté, 0=déconnecté
);
```

### Table : metrics

```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,             -- Référence à l'agent
    timestamp INTEGER NOT NULL,          -- Unix timestamp
    cpu_percent REAL,                   -- % CPU (0-100)
    ram_mb REAL,                        -- RAM en Mo
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Date d'enregistrement
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

### Index

```sql
CREATE INDEX idx_metrics_agent_time ON metrics(agent_id, timestamp);
```

Cet index optimise les requêtes filtrant par agent et période.

---

## 📁 Description des Fichiers

### Structure du Projet

```
teleinfo/
│
├── main.py          # Point d'entrée - Menu principal
├── config.py        # Configuration centralisée
├── server.py        # Serveur TCP (récepteur)
├── client.py        # Client de monitoring (émetteur)
├── database.py      # Module SQLite
├── reports.py       # Générateur de rapports
├── gui.py           # Interface graphique Tkinter
├── stress_test.py   # Module de stress test (simulation d'attaque)
│
├── data/            # Données (créé automatiquement)
│   └── teleinfo.db  # Base de données SQLite
│
├── reports/         # Rapports générés (créé automatiquement)
│   ├── report_*.json
│   ├── report_*.html
│   └── metrics_*.csv
│
├── logs/            # Fichiers de logs (créé automatiquement)
│   └── server.log
│
├── requirements.txt # (vide - pas de dépendances)
└── .gitignore
```

### Détail des Fichiers

#### `main.py` - Point d'Entrée

```
Rôle : Menu principal permettant de choisir le module à exécuter
Fonctions :
  - print_banner() : Affiche l'en-tête
  - print_menu() : Affiche le menu
  - run_server() : Lance le serveur
  - run_client() : Lance le client
  - run_gui() : Lance l'interface graphique
  - run_reports() : Lance le générateur de rapports
  - run_stress() : Lance le stress test
  - init_database() : Initialise la base de données
  - edit_config() : Affiche la configuration
```

#### `config.py` - Configuration

```
Rôle : Gestion centralisée de la configuration
Paramètres configurables :
  - server.host : Adresse IP d'écoute (défaut: 0.0.0.0)
  - server.port : Port TCP (défaut: 65432)
  - client.server_ip : IP du serveur (défaut: 127.0.0.1)
  - client.period : Intervalle d'envoi (défaut: 5 secondes)
  - database.retention_days : Conservation des données (défaut: 30 jours)
```

#### `server.py` - Serveur TCP

```
Rôle : Accepte les connexions et reçoit les métriques
Classes :
  - TeleinfoServer : Gestionnaire principal du serveur

Fonctions principales :
  - handle_client(conn, addr) : Gère la communication avec un client
  - status_thread() : Tâche de fond (nettoyage, statistiques)
  - start() : Démarre le serveur
  - stop() : Arrête le serveur proprement
```

#### `client.py` - Client de Monitoring

```
Rôle : Collecte et envoie les métriques système
Classes :
  - TeleinfoClient : Gestionnaire principal du client

Fonctions principales :
  - get_system_metrics() : Récupère CPU et RAM
  - connect() : Établit la connexion TCP
  - send_report() : Envoie les métriques
  - disconnect() : Ferme proprement la connexion
```

#### `database.py` - Module de Base de Données

```
Rôle : Interface avec SQLite pour stocker et récupérer les données
Classes :
  - Database : Gestionnaire de base de données

Méthodes principales :
  - register_agent(agent_id, hostname) : Enregistre un nouvel agent
  - insert_metric(agent_id, timestamp, cpu, ram) : Ajoute une métrique
  - get_metrics(agent_id, start_time, end_time) : Récupère les métriques
  - get_agents(active_only) : Liste les agents
  - get_statistics(hours) : Calcule les statistiques
  - cleanup_old_data(days) : Supprime les anciennes données
  - export_to_json/csv() : Exporte les données
```

#### `reports.py` - Générateur de Rapports

```
Rôle : Crée des rapports dans différents formats
Classes :
  - ReportGenerator : Générateur de rapports

Méthodes principales :
  - generate_summary_report(hours) : Rapport global
  - generate_detailed_report(agent_id) : Rapport par agent
  - generate_comparison_report(agent_ids) : Comparaison d'agents
  - generate_alert_report() : Détection d'anomalies
  - generate_html_report() : Rapport HTML stylisé
  - save_report_json/csv/html() : Sauvegarde
```

#### `stress_test.py` - Module de Stress Test

```
Rôle : Simule une chargemassive pour tester la robustesse du serveur
Classes :
  - StressTest : Gestionnaire de stress test

Modes disponibles :
  - burst : Envoie un nombre fixe de rapports
  - flood : Envoie le maximum possible (sans délai)
  - continuous : Envoie pendant une durée définie
  - multi : Lance plusieurs threads simultanés

Fonctions principales :
  - run_burst() : Mode burst avec compteur
  - run_flood() : Mode flood sans délai
  - run_continuous() : Mode continu avec stats temps réel
  - run_multi_threaded() : Mode multi-threads
  - print_stats() : Affiche les statistiques finales

Métriques mesurées :
  - Nombre de rapports envoyés
  - Taux de réussite (%)
  - Temps de réponse moyen/min/max (ms)
  - Débit moyen (msg/s)
  - Durée totale du test
```

---

## 📊 Format des Rapports

### Rapport JSON (Résumé)

```json
{
  "report_type": "summary",
  "generated_at": "2026-04-09T19:40:00.000000",
  "period_hours": 24,
  "active_agents": 2,
  "statistics": [
    {
      "agent_id": "agent_default",
      "sample_count": 288,
      "avg_cpu": 45.2,
      "max_cpu": 85.5,
      "min_cpu": 12.3,
      "avg_ram": 2048.5,
      "max_ram": 4096.0,
      "min_ram": 1024.0
    }
  ],
  "agents_detail": [
    {
      "agent_id": "agent_default",
      "hostname": "DELL5420",
      "first_seen": "2026-04-09 19:30:00",
      "last_seen": "2026-04-09 19:40:00",
      "status": "active"
    }
  ]
}
```

### Rapport CSV (Métriques)

```csv
id,agent_id,timestamp,cpu_percent,ram_mb,recorded_at
1,agent_default,1712679345,45.23,2048.5,2026-04-09 19:35:45
2,agent_default,1712679350,52.10,2100.0,2026-04-09 19:35:50
3,agent_default,1712679355,38.70,1980.0,2026-04-09 19:35:55
```

### Rapport HTML (Visuel)

Ouvrez le fichier `.html` dans un navigateur pour voir :

- Tableau de bord avec cartes statistiques colorées
- Liste des agents avec statut (actif/inactif)
- Statistiques (moyenne, min, max) par agent

---

## ⚙️ Configuration

Le fichier `config.json` (créé automatiquement) contient :

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 65432,
    "max_connections": 10,
    "buffer_size": 4096
  },
  "client": {
    "server_ip": "127.0.0.1",
    "server_port": 65432,
    "period": 5,
    "agent_id": "agent_default",
    "retry_delay": 3,
    "max_retries": 5
  },
  "database": {
    "path": "data/teleinfo.db",
    "retention_days": 30
  },
  "reports": {
    "output_dir": "reports",
    "format": "json"
  }
}
```

### Modifier la Configuration

Éditez le fichier `config.json` et redémarrez l'application.

---

## 📖 Guide d'Utilisation

### Scénario 1 : Test Local (une seule machine)

1. **Terminal 1** : `python main.py server`
2. **Terminal 2** : `python main.py client`
3. Attendre 1-2 minutes
4. **Terminal 3** : `python main.py reports` → Choisir `6` (tous les rapports)

### Scénario 2 : Plusieurs Machines

1. Sur la machine serveur : `python main.py server`
2. Sur chaque machine cliente : Modifier `config.json` :
   ```json
   "client": {
       "server_ip": "192.168.1.100"  // IP du serveur
   }
   ```
3. Lancer `python main.py client` sur chaque machine

### Scénario 3 : Interface Graphique

1. Lancer le serveur
2. Lancer un ou plusieurs clients
3. Lancer `python main.py gui`
4. Observer les métriques en temps réel
5. Cliquer sur "Générer Rapport" pour créer un rapport HTML

### Scénario 4 : Stress Test

1. **Terminal 1** : `python main.py server`
2. Attendre que le serveur soit prêt
3. **Terminal 2** : `python main.py stress --mode burst --count 5000`
4. Observer les statistiques de performance
5. Analyser les résultats (temps de réponse, débit)

### Arrêt Propre

- **Client** : Ctrl+C (envoie automatiquement BYE)
- **Serveur** : Ctrl+C (ferme toutes les connexions)

---

## 💥 Stress Test (Simulation d'Attaque)

Cette section permet de tester la robustesse du serveur en envoyant un grand volume de requêtes.

### Présentation

Le module `stress_test.py` simule différents scénarios de charge pour évaluer les performances du serveur :

| Mode | Description | Cas d'usage |
|------|-------------|-------------|
| **burst** | Envoie un nombre fixe de rapports | Test de charge ponctuelle |
| **flood** | Envoie le maximum possible | Test de résistance maximale |
| **continuous** | Envoie pendant une durée définie | Test de stabilité |
| **multi** | Lance plusieurs threads simultanés | Test de concurrences multiples |

### Lancement

#### Via le Menu

```bash
python main.py
# Choisir [5] STRESS TEST
```

#### Via Ligne de Commande

```bash
python main.py stress [OPTIONS]
```

### Options Disponibles

| Option | Description | Défaut |
|--------|-------------|--------|
| `--mode` | Mode de test (burst/continuous/flood/multi) | burst |
| `--count` | Nombre de rapports à envoyer (mode burst) | 1000 |
| `--duration` | Durée du test en secondes | 30 |
| `--threads` | Nombre de threads (mode multi) | 5 |
| `--delay` | Délai entre chaque envoi (secondes) | 0 |
| `--agent` | ID personnalisé pour l'agent | auto |

### Modes de Test Détaillés

#### 1. Mode BURST - Test de Charge Ponctuelle

Envoie un nombre fixe de rapports le plus rapidement possible.

```bash
python main.py stress --mode burst --count 5000
```

**Exemple de sortie :**

```
==================================================
  STRESS TEST - MODE BURST
==================================================
  Nombre de rapports: 5000
  Cible: 127.0.0.1:65432
==================================================

Progression: 100/5000 (980 msg/s)
Progression: 200/5000 (975 msg/s)
Progression: 300/5000 (982 msg/s)
...

==================================================
  RAPPORT DE STRESS TEST
==================================================
  Agent: stress_1234
  Duree: 5.12 secondes
  ---------------------------
  Envoye: 5000
  Echoue: 0
  Taux de reussite: 100.0%
  ---------------------------
  Vitesse moyenne: 976.5 msg/s
  ---------------------------
  Temps de reponse moyen: 1.02ms
  Temps de reponse min: 0.45ms
  Temps de reponse max: 15.32ms
==================================================
```

#### 2. Mode FLOOD - Test de Résistance Maximale

Envoie le maximum de requêtes possibles sans délai.

```bash
python main.py stress --mode flood --duration 60
```

**Objectif :** Trouver la limite de traitement du serveur.

```
==================================================
  FLOOD ATTACK SIMULATION
==================================================
  Mode: ENVOI MASSIF SANS DELAI
  Duree: 60 secondes
  Cible: 127.0.0.1:65432
==================================================

[19:40:00] Flood: 500 @ 950 msg/s
[19:40:05] Flood: 1200 @ 980 msg/s
[19:40:10] Flood: 2100 @ 975 msg/s
...
[19:41:00] Flood: 58000 @ 967 msg/s

==================================================
  RAPPORT DE STRESS TEST
==================================================
  Envoye: 58000
  Vitesse moyenne: 966.7 msg/s
  Taux de reussite: 99.8%
==================================================
```

#### 3. Mode CONTINUOUS - Test de Stabilité

Envoie des métriques pendant une durée définie avec stats en temps réel.

```bash
python main.py stress --mode continuous --duration 120
```

**Objectif :** Vérifier que le serveur reste stable sur une longue période.

#### 4. Mode MULTI - Test de Concurrence

Lance plusieurs threads simultanés pour simuler plusieurs clients.

```bash
python main.py stress --mode multi --threads 10 --duration 60
```

**Objectif :** Tester la gestion de multiples connexions simultanées.

```
==================================================
  STRESS TEST - MULTI-THREADED
==================================================
  Threads: 10
  Duree: 60 secondes
==================================================

[Thread-0] Termine: 5800 envois
[Thread-1] Termine: 5750 envois
[Thread-2] Termine: 5820 envois
...
[Thread-9] Termine: 5790 envois

Total: ~58000 rapports en 60 secondes
```

### Commandes Rapides

```bash
# Test rapide (1000 rapports)
python main.py stress

# Test moyen (10000 rapports)
python main.py stress --mode burst --count 10000

# Flood 30 secondes
python main.py stress --mode flood --duration 30

# 5 clients simultanés pendant 1 minute
python main.py stress --mode multi --threads 5 --duration 60

# Test avec délai entre chaque envoi
python main.py stress --mode burst --count 500 --delay 0.01
```

### Diagramme de Flux - Stress Test

```
┌─────────────────────────────────────────────────────────────┐
│                    STRESS TEST WORKFLOW                      │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │  Choix du MODE   │
                    │ burst/continuous  │
                    │ flood/multi      │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │   Burst  │      │  Flood   │      │  Multi   │
    │  N msgs  │      │   Max    │      │ N threads│
    └────┬─────┘      └────┬─────┘      └────┬─────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │ Connexion TCP  │
                   │ au Serveur    │
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │ HELLO + REPORT│
                   │ (boucle)     │
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │  Mesure des   │
                   │  Performances │
                   │ - Temps reponse│
                   │ - Debit       │
                   │ - Taux erreur │
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │   BYE + Stats │
                   │    Finales    │
                   └───────────────┘
```

### Interprétation des Résultats

| Métrique | Bon | Moyen | Mauvais |
|----------|-----|-------|---------|
| Taux de réussite | > 99% | 95-99% | < 95% |
| Temps de réponse moyen | < 5ms | 5-20ms | > 20ms |
| Débit (msg/s) | > 500 | 100-500 | < 100 |

### Précautions

⚠️ **Attention** : Le mode flood envoie un très grand volume de données. Utilisez-le uniquement sur :

- Votre propre serveur de test
- Un environnement isolé
- Avec l'accord du propriétaire du système

---



---

## 💻 Exemples de Sortie

### Sortie Serveur

```
2026-04-09 19:35:44,926 - INFO - Serveur demarre sur 0.0.0.0:65432
2026-04-09 19:35:45,123 - INFO - Connexion de ('127.0.0.1', 54321)
2026-04-09 19:35:45,124 - INFO - Recu de ('127.0.0.1', 54321): HELLO agent_default DELL5420
2026-04-09 19:35:45,125 - INFO - Agent enregistre: agent_default (DELL5420)
2026-04-09 19:35:50,234 - INFO - Recu de ('127.0.0.1', 54321): REPORT agent_default 1712679350 45.23 2048.5
2026-04-09 19:35:55,345 - INFO - Recu de ('127.0.0.1', 54321): REPORT agent_default 1712679355 52.10 2100.0
2026-04-09 19:36:00,456 - INFO - Recu de ('127.0.0.1', 54321): REPORT agent_default 1712679360 38.70 1980.0
2026-04-09 19:36:05,567 - INFO - === Status ===
2026-04-09 19:36:05,568 - INFO - Agents actifs: 1
2026-04-09 19:36:05,569 - INFO -   - agent_default (DELL5420)
```

### Sortie Client

```
[19:35:45] Connecte au serveur 127.0.0.1:65432
[19:35:45] Rapport envoye: CPU=45.23% RAM=2048.5MB
[19:35:50] Rapport envoye: CPU=52.10% RAM=2100.0MB
[19:35:55] Rapport envoye: CPU=38.70% RAM=1980.0MB
^C
[19:36:10] Arret en cours...

========================================
  STATISTIQUES CLIENT agent_default
========================================
  Uptime: 25s
  Rapports envoyes: 5
  Echecs: 0
  Taux de succes: 100.0%
========================================
```

### Sortie Stress Test

```
==================================================
  STRESS TEST - MODE BURST
==================================================
  Nombre de rapports: 1000
  Cible: 127.0.0.1:65432
==================================================

Progression: 100/1000 (950 msg/s)
Progression: 200/1000 (975 msg/s)
Progression: 300/1000 (980 msg/s)

==================================================
  RAPPORT DE STRESS TEST
==================================================
  Agent: stress_5678
  Duree: 1.03 secondes
  ---------------------------
  Envoye: 1000
  Echoue: 0
  Taux de reussite: 100.0%
  ---------------------------
  Vitesse moyenne: 970.9 msg/s
  ---------------------------
  Temps de reponse moyen: 1.03ms
  Temps de reponse min: 0.42ms
  Temps de reponse max: 8.75ms
==================================================
```

### Rapports Générés

```
C:\Users\DELL 5420\OneDrive\Desktop\teleinfo\reports\
├── report_summary_20260409_194000.json    # Rapport JSON
├── report_summary_20260409_194000.html    # Rapport HTML
├── report_detailed_agent_default_20260409_194000.json
├── report_alerts_20260409_194000.json
└── metrics_all_20260409_194000.csv        # Export CSV
```

---

## ❓ FAQ

### Q: Le client ne peut pas se connecter au serveur

**R:** Vérifiez que :

- Le serveur est lancé
- L'adresse IP et le port sont corrects dans `config.json`
- Le pare-feu autorise les connexions sur le port 65432

### Q: Comment changer la fréquence d'envoi des métriques ?

**R:** Modifiez `config.json` :

```json
"client": {
    "period": 10  // 10 secondes au lieu de 5
}
```

### Q: Comment supprimer les anciennes données ?

**R:**

- Automatiquement : Le serveur nettoie toutes les 30 secondes
- Manuellement : Lancez `python main.py reports` → option pour nettoyer

### Q: Comment ajouter plusieurs clients ?

**R:** Lancez `client.py` sur chaque machine avec la même IP serveur

### Q: Le programme nécessite-t-il des bibliothèques externes ?

**R:** Non, il utilise uniquement la bibliothèque standard Python

### Q: Comment générer un rapport pour une période spécifique ?

**R:** Modifier le code de `reports.py` pour passer le paramètre `hours` :

```python
report = generator.generate_summary_report(hours=48)  # 48 heures
```

---

## 📚 Annexe Technique

### Commandes SQL Utiles

```sql
-- Voir tous les agents
SELECT * FROM agents;

-- Voir les dernières métriques
SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 10;

-- Statistiques par agent
SELECT agent_id, AVG(cpu_percent), AVG(ram_mb)
FROM metrics
GROUP BY agent_id;

-- Métriques d'un agent sur 24h
SELECT * FROM metrics
WHERE agent_id = 'agent_default'
AND timestamp > strftime('%s', 'now', '-1 day');
```

### Commandes Réseau Utiles

```bash
# Vérifier si le port est ouvert
netstat -an | findstr 65432

# Tester la connexion
telnet 127.0.0.1 65432
```

---

## 🎓 Contexte Académique

Ce projet a été développé dans le cadre d'un **TP de Téléinformatique** pour démontrer :

1. **Communication TCP/IP** : Utilisation des sockets Python
2. **Protocole Applicatif** : Définition d'un protocole simple texte
3. **Base de données** : Stockage et interrogation avec SQLite
4. **Architecture Client-Serveur** : Séparation des rôles
5. **Traitement Multithread** : Gestion de multiples connexions simultanées
6. **Génération de Rapports** : Export de données dans multiples formats
7. **Interface Graphique** : GUI basique avec Tkinter
8. **Tests de Performance** : Simulation d'attaque et stress testing

---

## 👤 Auteur

Projet développé dans le cadre du cours de Téléinformatique.

**Version :** 1.0  
**Date :** Avril 2026

---

<div align="center">

**Bonne utilisation du système Teleinfo Monitor !**

</div>
