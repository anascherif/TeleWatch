"""Module de base de données SQLite pour stocker les métriques."""

import sqlite3
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from config import config, DATA_DIR

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.get("database", "path")
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT UNIQUE NOT NULL,
                    hostname TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active INTEGER DEFAULT 1
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    cpu_percent REAL,
                    ram_mb REAL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_agent_time 
                ON metrics(agent_id, timestamp)
            """)
            conn.commit()
    
    def register_agent(self, agent_id, hostname):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agents (agent_id, hostname, last_seen, active)
                VALUES (?, ?, CURRENT_TIMESTAMP, 1)
            """, (agent_id, hostname))
            conn.commit()
    
    def update_agent_seen(self, agent_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE agents SET last_seen = CURRENT_TIMESTAMP
                WHERE agent_id = ?
            """, (agent_id,))
            conn.commit()
    
    def insert_metric(self, agent_id, timestamp, cpu, ram):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metrics (agent_id, timestamp, cpu_percent, ram_mb)
                VALUES (?, ?, ?, ?)
            """, (agent_id, timestamp, cpu, ram))
            conn.commit()
    
    def get_metrics(self, agent_id=None, start_time=None, end_time=None, limit=1000):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM metrics WHERE 1=1"
            params = []
            
            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_agents(self, active_only=False):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM agents"
            if active_only:
                query += " WHERE active = 1"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self, agent_id=None, hours=24):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            since = int((datetime.now() - timedelta(hours=hours)).timestamp())
            
            query = """
                SELECT 
                    agent_id,
                    COUNT(*) as sample_count,
                    AVG(cpu_percent) as avg_cpu,
                    MAX(cpu_percent) as max_cpu,
                    MIN(cpu_percent) as min_cpu,
                    AVG(ram_mb) as avg_ram,
                    MAX(ram_mb) as max_ram,
                    MIN(ram_mb) as min_ram
                FROM metrics
                WHERE timestamp >= ?
            """
            params = [since]
            
            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)
            
            query += " GROUP BY agent_id"
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, days=None):
        retention = days or config.get("database", "retention_days") or 30
        cutoff = int((datetime.now() - timedelta(days=retention)).timestamp())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
    
    def export_to_json(self, filepath):
        data = {
            "export_date": datetime.now().isoformat(),
            "agents": self.get_agents(),
            "metrics": self.get_metrics(limit=100000),
            "statistics": self.get_statistics(hours=168)
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return filepath
    
    def export_to_csv(self, filepath, agent_id=None):
        metrics = self.get_metrics(agent_id=agent_id, limit=100000)
        
        if not metrics:
            return None
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
            writer.writeheader()
            writer.writerows(metrics)
        
        return filepath
    
    def close_inactive_agents(self, minutes=10):
        cutoff = int((datetime.now() - timedelta(minutes=minutes)).timestamp())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE agents 
                SET active = 0 
                WHERE last_seen < datetime('now', '-' || ? || ' minutes')
                AND active = 1
            """, (minutes,))
            conn.commit()
            return cursor.rowcount

if __name__ == "__main__":
    db = Database()
    print(f"Base de données initialisée: {db.db_path}")
    print(f"Agents: {db.get_agents()}")
