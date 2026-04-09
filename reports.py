"""Génération de rapports pour les données de monitoring."""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO
from database import Database
from config import config, REPORTS_DIR

class ReportGenerator:
    def __init__(self, db=None):
        self.db = db or Database()
        self.output_dir = Path(config.get("reports", "output_dir") or REPORTS_DIR)
    
    def generate_summary_report(self, hours=24, agent_id=None):
        stats = self.db.get_statistics(agent_id=agent_id, hours=hours)
        agents = self.db.get_agents(active_only=True)
        
        report = {
            "report_type": "summary",
            "generated_at": datetime.now().isoformat(),
            "period_hours": hours,
            "active_agents": len(agents),
            "statistics": stats,
            "agents_detail": [
                {
                    "agent_id": a["agent_id"],
                    "hostname": a["hostname"],
                    "first_seen": a["first_seen"],
                    "last_seen": a["last_seen"],
                    "status": "active" if a["active"] else "inactive"
                }
                for a in agents
            ]
        }
        
        return report
    
    def generate_detailed_report(self, agent_id, hours=24):
        metrics = self.db.get_metrics(agent_id=agent_id, limit=10000)
        
        since = int((datetime.now() - timedelta(hours=hours)).timestamp())
        recent_metrics = [m for m in metrics if m["timestamp"] >= since]
        
        if not recent_metrics:
            return {"error": "Aucune donnée trouvée"}
        
        cpu_values = [m["cpu_percent"] for m in recent_metrics if m["cpu_percent"]]
        ram_values = [m["ram_mb"] for m in recent_metrics if m["ram_mb"]]
        
        report = {
            "report_type": "detailed",
            "generated_at": datetime.now().isoformat(),
            "agent_id": agent_id,
            "period_hours": hours,
            "sample_count": len(recent_metrics),
            "cpu": {
                "min": min(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "values": cpu_values[-100:]
            },
            "ram": {
                "min": min(ram_values) if ram_values else 0,
                "max": max(ram_values) if ram_values else 0,
                "avg": sum(ram_values) / len(ram_values) if ram_values else 0,
                "values": ram_values[-100:]
            },
            "time_series": [
                {
                    "timestamp": m["timestamp"],
                    "datetime": datetime.fromtimestamp(m["timestamp"]).isoformat(),
                    "cpu": m["cpu_percent"],
                    "ram": m["ram_mb"]
                }
                for m in recent_metrics[-50:]
            ]
        }
        
        return report
    
    def generate_comparison_report(self, agent_ids, hours=24):
        comparison = {
            "report_type": "comparison",
            "generated_at": datetime.now().isoformat(),
            "compared_agents": agent_ids,
            "period_hours": hours,
            "agents": []
        }
        
        for agent_id in agent_ids:
            stats = self.db.get_statistics(agent_id=agent_id, hours=hours)
            if stats:
                comparison["agents"].append(stats[0])
        
        return comparison
    
    def generate_alert_report(self, cpu_threshold=80, ram_threshold=8000):
        metrics = self.db.get_metrics(limit=10000)
        
        since = int((datetime.now() - timedelta(hours=24)).timestamp())
        recent = [m for m in metrics if m["timestamp"] >= since]
        
        alerts = []
        for m in recent:
            if m["cpu_percent"] and m["cpu_percent"] > cpu_threshold:
                alerts.append({
                    "timestamp": m["timestamp"],
                    "datetime": datetime.fromtimestamp(m["timestamp"]).isoformat(),
                    "agent_id": m["agent_id"],
                    "type": "CPU_HIGH",
                    "value": m["cpu_percent"],
                    "threshold": cpu_threshold
                })
            if m["ram_mb"] and m["ram_mb"] > ram_threshold:
                alerts.append({
                    "timestamp": m["timestamp"],
                    "datetime": datetime.fromtimestamp(m["timestamp"]).isoformat(),
                    "agent_id": m["agent_id"],
                    "type": "RAM_HIGH",
                    "value": m["ram_mb"],
                    "threshold": ram_threshold
                })
        
        return {
            "report_type": "alerts",
            "generated_at": datetime.now().isoformat(),
            "thresholds": {"cpu": cpu_threshold, "ram": ram_threshold},
            "alert_count": len(alerts),
            "alerts": alerts
        }
    
    def save_report_json(self, report, filename=None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{report['report_type']}_{timestamp}.json"
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def save_report_csv(self, agent_id=None, filename=None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{agent_id or 'all'}_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        self.db.export_to_csv(filepath, agent_id=agent_id)
        return filepath
    
    def generate_html_report(self, report_data):
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Rapport Teleinfo - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card.warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .stat-card.success {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .stat-value {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .alert {{ background: #ffcccc; border-left: 4px solid #f44336; padding: 10px; margin: 5px 0; }}
        .timestamp {{ color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Rapport de Monitoring Teleinfo</h1>
        <p class="timestamp">Généré le: {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}</p>
"""
        
        if "active_agents" in report_data:
            html += f"""
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value">{report_data.get('active_agents', 0)}</div>
                <div class="stat-label">Agents Actifs</div>
            </div>
            <div class="stat-card success">
                <div class="stat-value">{report_data.get('period_hours', 24)}h</div>
                <div class="stat-label">Période</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-value">{len(report_data.get('statistics', []))}</div>
                <div class="stat-label">Statistiques</div>
            </div>
        </div>
"""
        
        if report_data.get("statistics"):
            html += """
        <h2>Statistiques des Agents</h2>
        <table>
            <tr>
                <th>Agent</th>
                <th>Échantillons</th>
                <th>CPU Moy.</th>
                <th>CPU Max</th>
                <th>RAM Moy.</th>
                <th>RAM Max</th>
            </tr>
"""
            for stat in report_data["statistics"]:
                html += f"""
            <tr>
                <td>{stat.get('agent_id', 'N/A')}</td>
                <td>{stat.get('sample_count', 0)}</td>
                <td>{stat.get('avg_cpu', 0):.1f}%</td>
                <td>{stat.get('max_cpu', 0):.1f}%</td>
                <td>{stat.get('avg_ram', 0):.0f} MB</td>
                <td>{stat.get('max_ram', 0):.0f} MB</td>
            </tr>
"""
            html += "</table>"
        
        if report_data.get("agents_detail"):
            html += """
        <h2>Détail des Agents</h2>
        <table>
            <tr>
                <th>Agent ID</th>
                <th>Hostname</th>
                <th>Premier vu</th>
                <th>Dernière connexion</th>
                <th>Status</th>
            </tr>
"""
            for agent in report_data["agents_detail"]:
                status_color = "#4CAF50" if agent["status"] == "active" else "#f44336"
                html += f"""
            <tr>
                <td>{agent['agent_id']}</td>
                <td>{agent['hostname']}</td>
                <td>{agent['first_seen']}</td>
                <td>{agent['last_seen']}</td>
                <td><span style="color:{status_color};font-weight:bold;">{agent['status'].upper()}</span></td>
            </tr>
"""
            html += "</table>"
        
        html += """
    </div>
</body>
</html>"""
        
        return html
    
    def save_html_report(self, report_data, filename=None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{report_data.get('report_type', 'summary')}_{timestamp}.html"
        
        filepath = self.output_dir / filename
        html = self.generate_html_report(report_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath

def main():
    print("=" * 50)
    print("  GÉNÉRATEUR DE RAPPORTS")
    print("=" * 50)
    
    generator = ReportGenerator()
    
    print("\n1. Rapport résumé (24h)")
    print("2. Rapport détaillé par agent")
    print("3. Rapport comparatif")
    print("4. Rapport d'alertes")
    print("5. Exporter en CSV")
    print("6. Générer tous les rapports")
    
    choice = input("\nVotre choix: ").strip()
    
    if choice == "1":
        report = generator.generate_summary_report(hours=24)
        filepath = generator.save_report_json(report)
        print(f"Rapport JSON: {filepath}")
        html_path = generator.save_html_report(report)
        print(f"Rapport HTML: {html_path}")
    
    elif choice == "2":
        agents = generator.db.get_agents()
        if agents:
            print("\nAgents disponibles:")
            for a in agents:
                print(f"  - {a['agent_id']} ({a['hostname']})")
            agent_id = input("\nAgent ID: ").strip()
            if agent_id:
                report = generator.generate_detailed_report(agent_id)
                if "error" in report:
                    print(f"Aucune donnee pour cet agent: {agent_id}")
                else:
                    filepath = generator.save_report_json(report)
                    print(f"Rapport: {filepath}")
        else:
            print("Aucun agent enregistre.")
    
    elif choice == "3":
        agents = generator.db.get_agents()
        if len(agents) >= 1:
            agent_ids = [a['agent_id'] for a in agents[:5]]
            report = generator.generate_comparison_report(agent_ids)
            filepath = generator.save_report_json(report)
            print(f"Rapport: {filepath}")
        else:
            print("Aucun agent enregistre.")
    
    elif choice == "4":
        report = generator.generate_alert_report()
        filepath = generator.save_report_json(report)
        print(f"Rapport: {filepath}")
        if report["alerts"]:
            print(f"\n{len(report['alerts'])} alertes trouvées")
    
    elif choice == "5":
        filepath = generator.save_report_csv()
        print(f"Export CSV: {filepath}")
    
    elif choice == "6":
        report = generator.generate_summary_report()
        generator.save_report_json(report)
        generator.save_html_report(report)
        
        agents = generator.db.get_agents()
        for agent in agents[:3]:
            detailed = generator.generate_detailed_report(agent['agent_id'])
            generator.save_report_json(detailed)
        
        alert = generator.generate_alert_report()
        generator.save_report_json(alert)
        
        generator.save_report_csv()
        print("Tous les rapports générés!")
    
    print("\nTerminé!")

if __name__ == "__main__":
    main()
