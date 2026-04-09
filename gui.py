"""Interface graphique pour le monitoring en temps réel."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
from database import Database
from config import config

class MonitoringDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Teleinfo Monitor - Dashboard")
        self.root.geometry("900x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.db = Database()
        self.running = True
        self.agent_colors = {}
        self.color_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
        self.color_index = 0
        
        self.setup_ui()
        self.start_refresh()
    
    def get_agent_color(self, agent_id):
        if agent_id not in self.agent_colors:
            self.agent_colors[agent_id] = self.color_palette[self.color_index % len(self.color_palette)]
            self.color_index += 1
        return self.agent_colors[agent_id]
    
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="Teleinfo Monitor", 
                 font=('Arial', 20, 'bold')).pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(title_frame, text="● Connecté", 
                                     foreground='green', font=('Arial', 10))
        self.status_label.pack(side=tk.RIGHT)
        
        self.clock_label = ttk.Label(title_frame, text="", font=('Arial', 10))
        self.clock_label.pack(side=tk.RIGHT, padx=20)
        
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=2)
        
        self.create_agents_panel(left_frame)
        self.create_stats_panel(left_frame)
        
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)
        
        self.create_metrics_panel(right_frame)
        self.create_log_panel(right_frame)
        
        self.create_control_panel(main_frame)
    
    def create_agents_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Agents Connectés", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.agents_tree = ttk.Treeview(frame, columns=('Hostname', 'Status', 'Last Seen'), 
                                        show='headings', height=6)
        self.agents_tree.heading('Hostname', text='Hostname')
        self.agents_tree.heading('Status', text='Status')
        self.agents_tree.heading('Last Seen', text='Dernière connexion')
        
        self.agents_tree.column('Status', width=80)
        self.agents_tree.column('Last Seen', width=150)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.agents_tree.yview)
        self.agents_tree.configure(yscrollcommand=scrollbar.set)
        
        self.agents_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_stats_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Statistiques Rapides", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_labels = {}
        stats = [
            ('Agents Actifs', 'active_agents'),
            ('Rapports (1h)', 'reports_1h'),
            ('CPU Moy.', 'cpu_avg'),
            ('RAM Moy.', 'ram_avg')
        ]
        
        for i, (label_text, key) in enumerate(stats):
            col = i % 2
            row = i // 2
            
            card = tk.Frame(frame, bg='#667eea', padx=15, pady=10)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            
            tk.Label(card, text="0", font=('Arial', 18, 'bold'), 
                    bg='#667eea', fg='white').pack()
            tk.Label(card, text=label_text, font=('Arial', 9), 
                    bg='#667eea', fg='white').pack()
            
            self.stats_labels[key] = card.winfo_children()[0]
        
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
    
    def create_metrics_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Métriques en Temps Réel", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.metrics_text = scrolledtext.ScrolledText(frame, height=12, 
                                                       font=('Consolas', 9),
                                                       bg='#1e1e1e', fg='#00ff00')
        self.metrics_text.pack(fill=tk.BOTH, expand=True)
        
        self.metrics_text.tag_configure('header', foreground='yellow', font=('Consolas', 10, 'bold'))
        self.metrics_text.tag_configure('agent', foreground='cyan')
        self.metrics_text.tag_configure('cpu', foreground='#FF6B6B')
        self.metrics_text.tag_configure('ram', foreground='#4ECDC4')
        self.metrics_text.tag_configure('timestamp', foreground='gray')
    
    def create_log_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Journal d'Activité", padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(frame, height=8, 
                                                   font=('Consolas', 9),
                                                   bg='#1e1e1e', fg='#ffffff')
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_control_panel(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(frame, text="Rafraîchir", command=self.refresh_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Générer Rapport", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Exporter JSON", command=self.export_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Nettoyer Ancien", command=self.cleanup).pack(side=tk.LEFT, padx=5)
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Auto-refresh", 
                       variable=self.auto_refresh_var).pack(side=tk.RIGHT, padx=10)
    
    def add_log(self, message, level='info'):
        colors = {'info': '#ffffff', 'success': '#4ECDC4', 'warning': '#FFEAA7', 'error': '#FF6B6B'}
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        self.log_text.insert(tk.END, f"{message}\n", f'log_{level}')
        self.log_text.see(tk.END)
    
    def refresh_data(self):
        try:
            agents = self.db.get_agents(active_only=False)
            active_agents = [a for a in agents if a.get('active')]
            
            for item in self.agents_tree.get_children():
                self.agents_tree.delete(item)
            
            for agent in agents:
                status = "🟢 Actif" if agent.get('active') else "⚪ Inactif"
                self.agents_tree.insert('', 0, values=(
                    f"{agent['agent_id']} ({agent['hostname']})",
                    status,
                    agent.get('last_seen', 'N/A')
                ))
            
            stats = self.db.get_statistics(hours=1)
            total_samples = sum(s.get('sample_count', 0) for s in stats)
            avg_cpu = sum(s.get('avg_cpu', 0) for s in stats) / max(len(stats), 1)
            avg_ram = sum(s.get('avg_ram', 0) for s in stats) / max(len(stats), 1)
            
            self.stats_labels['active_agents'].config(text=str(len(active_agents)))
            self.stats_labels['reports_1h'].config(text=str(total_samples))
            self.stats_labels['cpu_avg'].config(text=f"{avg_cpu:.1f}%")
            self.stats_labels['ram_avg'].config(text=f"{avg_ram:.0f}MB")
            
            self.metrics_text.delete('1.0', tk.END)
            self.metrics_text.insert(tk.END, "=" * 60 + "\n", 'header')
            self.metrics_text.insert(tk.END, f"  MÉTRIQUES EN TEMPS RÉEL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", 'header')
            self.metrics_text.insert(tk.END, "=" * 60 + "\n\n", 'header')
            
            metrics = self.db.get_metrics(limit=20)
            by_agent = {}
            for m in metrics:
                aid = m['agent_id']
                if aid not in by_agent:
                    by_agent[aid] = []
                by_agent[aid].append(m)
            
            for agent_id, m_list in by_agent.items():
                color = self.get_agent_color(agent_id)
                self.metrics_text.insert(tk.END, f"[{agent_id}]\n", f"agent_{agent_id}")
                
                for m in m_list[:5]:
                    ts = datetime.fromtimestamp(m['timestamp']).strftime("%H:%M:%S")
                    cpu = m.get('cpu_percent', 0)
                    ram = m.get('ram_mb', 0)
                    self.metrics_text.insert(tk.END, f"  {ts} | CPU: {cpu:5.1f}% | RAM: {ram:7.0f} MB\n")
                
                self.metrics_text.insert(tk.END, "\n")
            
            self.clock_label.config(text=datetime.now().strftime("%H:%M:%S"))
            
        except Exception as e:
            self.add_log(f"Erreur refresh: {e}", 'error')
    
    def start_refresh(self):
        def updater():
            while self.running:
                if self.auto_refresh_var.get():
                    self.refresh_data()
                time.sleep(3)
        
        thread = threading.Thread(target=updater, daemon=True)
        thread.start()
    
    def generate_report(self):
        from reports import ReportGenerator
        try:
            generator = ReportGenerator()
            report = generator.generate_summary_report(hours=24)
            filepath = generator.save_report_json(report)
            html_path = generator.save_html_report(report)
            self.add_log(f"Rapports générés: {filepath.name}, {html_path.name}", 'success')
            messagebox.showinfo("Succès", f"Rapports générés:\n{filepath}\n{html_path}")
        except Exception as e:
            self.add_log(f"Erreur rapport: {e}", 'error')
            messagebox.showerror("Erreur", str(e))
    
    def export_json(self):
        try:
            filepath = self.db.export_to_json(f"data/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            self.add_log(f"Export JSON: {filepath}", 'success')
            messagebox.showinfo("Succès", f"Exporté: {filepath}")
        except Exception as e:
            self.add_log(f"Erreur export: {e}", 'error')
    
    def cleanup(self):
        try:
            deleted = self.db.cleanup_old_data()
            self.add_log(f"Nettoyage: {deleted} entrées supprimées", 'success')
            messagebox.showinfo("Succès", f"{deleted} anciennes entrées supprimées")
        except Exception as e:
            self.add_log(f"Erreur cleanup: {e}", 'error')
    
    def on_closing(self):
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MonitoringDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
