"""Configuration management for provider_research package."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .exceptions import ConfigurationError


class Config:
    """Configuration loader and manager."""
    
    DEFAULT_CONFIG = {
        'database': {
            'type': 'sqlite',  # 'sqlite' or 'postgres'
            'sqlite': {
                'path': 'data/providers.db'
            },
            'postgres': {
                'host': 'localhost',
                'port': 5432,
                'database': 'providers',
                'user': 'provider_admin',
                'password': 'provider123'
            }
        },
        'llm': {
            'provider': 'anthropic',  # 'anthropic' or 'openai'
            'api_key_env': 'ANTHROPIC_API_KEY',
            'model': 'claude-3-sonnet-20240229',
            'timeout': 60
        },
        'web_scraping': {
            'enabled': True,
            'timeout': 30,
            'user_agent': 'ProviderResearch/2.0'
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to YAML config file. If None, uses defaults.
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path:
            self.load_from_file(config_path)
        
        # Override with environment variables
        self._load_from_env()
    
    def load_from_file(self, config_path: str):
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")
        
        try:
            with open(path, 'r') as f:
                file_config = yaml.safe_load(f)
                self._merge_config(file_config)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Database
        if 'DATABASE_TYPE' in os.environ:
            self.config['database']['type'] = os.environ['DATABASE_TYPE']
        
        if 'DATABASE_URL' in os.environ:
            # Parse DATABASE_URL for postgres
            # Format: postgres://user:pass@host:port/dbname
            pass
        
        # LLM API Key
        if 'ANTHROPIC_API_KEY' in os.environ:
            self.config['llm']['api_key'] = os.environ['ANTHROPIC_API_KEY']
        elif 'OPENAI_API_KEY' in os.environ:
            self.config['llm']['api_key'] = os.environ['OPENAI_API_KEY']
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Recursively merge new config into existing config."""
        def merge(base, update):
            for key, value in update.items():
                if isinstance(value, dict) and key in base:
                    merge(base[key], value)
                else:
                    base[key] = value
        
        merge(self.config, new_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        db_type = self.config['database']['type']
        return self.config['database'].get(db_type, {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self.config['llm']


# Global config instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None or config_path is not None:
        _config = Config(config_path)
    return _config


def set_config(config: Config):
    """Set global config instance."""
    global _config
    _config = config
