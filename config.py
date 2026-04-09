"""Configuration centralisée du projet Teleinfo Monitor."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path(__file__).parent
DATA_DIR = CONFIG_DIR / "data"
REPORTS_DIR = CONFIG_DIR / "reports"
LOGS_DIR = CONFIG_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

DEFAULT_CONFIG = {
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
        "path": str(DATA_DIR / "teleinfo.db"),
        "retention_days": 30
    },
    "reports": {
        "output_dir": str(REPORTS_DIR),
        "format": "json"
    }
}

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        config_file = CONFIG_DIR / "config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                config = DEFAULT_CONFIG.copy()
                for section, values in user_config.items():
                    if section in config:
                        config[section].update(values)
                return config
        return DEFAULT_CONFIG.copy()
    
    def save(self):
        config_file = CONFIG_DIR / "config.json"
        with open(config_file, 'w') as f:
            json.dump(self._config, f, indent=4)
    
    def get(self, section, key=None):
        if key:
            return self._config.get(section, {}).get(key)
        return self._config.get(section)
    
    def set(self, section, key, value):
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value

config = Config()
