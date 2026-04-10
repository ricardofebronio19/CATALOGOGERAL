import logging
import logging.config
import os
from datetime import datetime

# Configuração de logging estruturado para CGI
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO'
        },
        'file_app': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        },
        'file_error': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'detailed',
            'level': 'ERROR',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 3,
            'encoding': 'utf-8'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file_app', 'file_error']
    },
    'loggers': {
        'app': {
            'level': 'DEBUG',
            'handlers': ['file_app'],
            'propagate': False
        },
        'routes': {
            'level': 'DEBUG', 
            'handlers': ['file_app'],
            'propagate': False
        },
        'tasks': {
            'level': 'INFO',
            'handlers': ['file_app'],
            'propagate': False
        },
        'werkzeug': {
            'level': 'WARNING',
            'handlers': ['file_app'],
            'propagate': False
        }
    }
}

def setup_logging(app_data_path):
    """Configura o sistema de logging para a aplicação CGI"""
    
    # Define os caminhos dos arquivos de log
    logs_dir = os.path.join(app_data_path, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Atualiza os caminhos dos handlers
    LOGGING_CONFIG['handlers']['file_app']['filename'] = os.path.join(logs_dir, 'app.log')
    LOGGING_CONFIG['handlers']['file_error']['filename'] = os.path.join(logs_dir, 'error.log')
    
    # Configura o logging
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Logger principal da aplicação
    logger = logging.getLogger('app')
    logger.info("Sistema de logging configurado com sucesso")
    logger.info(f"Logs salvos em: {logs_dir}")
    
    return logger

def get_logger(name):
    """Retorna um logger personalizado para módulos específicos"""
    return logging.getLogger(name)

# Decorador para log automático de funções
def log_function_call(func):
    """Decorador para fazer log automático de chamadas de função"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('app')
        logger.debug(f"Chamando função {func.__name__} com args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Função {func.__name__} executada com sucesso")
            return result
        except Exception as e:
            logger.error(f"Erro na função {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper

# Classe para logging de performance
class PerformanceLogger:
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_time = None
        self.logger = logging.getLogger('app')
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Iniciando operação: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type:
            self.logger.error(f"Operação {self.operation_name} falhou após {duration:.2f}s: {exc_val}")
        else:
            self.logger.info(f"Operação {self.operation_name} concluída em {duration:.2f}s")