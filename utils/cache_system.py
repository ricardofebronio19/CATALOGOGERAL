"""
Sistema de Cache em Memória para CGI
Implementa cache inteligente para otimizar performance de consultas e operações
"""

import time
import hashlib
import json
from functools import wraps
from typing import Any, Dict, List, Optional, Union
from threading import RLock
from datetime import datetime, timedelta

from flask import current_app, request
from app import get_logger

logger = get_logger('cache')

class InMemoryCache:
    """
    Cache em memória thread-safe com TTL (Time To Live)
    """
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Inicializa o cache
        
        Args:
            default_ttl: Tempo de vida padrão em segundos (5 min default)
            max_size: Tamanho máximo do cache (número de entradas)
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict] = {}
        self._lock = RLock()
        self._hit_count = 0
        self._miss_count = 0
        logger.info(f"Cache inicializado com TTL={default_ttl}s, max_size={max_size}")
    
    def _generate_key(self, key_data: Union[str, Dict, List]) -> str:
        """Gera chave única para os dados"""
        if isinstance(key_data, str):
            return key_data
        
        # Para dicts/lists, cria hash dos dados
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_expired(self, cache_entry: Dict) -> bool:
        """Verifica se uma entrada do cache expirou"""
        if cache_entry.get('ttl') == -1:  # Cache permanente
            return False
        return time.time() > cache_entry['expires_at']
    
    def _evict_expired(self):
        """Remove entradas expiradas (sem lock - deve ser chamado dentro de with self._lock)"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if entry.get('ttl') != -1 and current_time > entry['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cache: removidas {len(expired_keys)} entradas expiradas")
    
    def _evict_lru(self):
        """Remove entrada menos recentemente usada se cache estiver cheio"""
        if len(self._cache) >= self.max_size:
            # Encontra entrada menos recentemente acessada
            oldest_key = min(self._cache.keys(), 
                           key=lambda k: self._cache[k]['last_access'])
            del self._cache[oldest_key]
            logger.debug(f"Cache: removida entrada LRU '{oldest_key}' (cache cheio)")
    
    def get(self, key: Union[str, Dict, List]) -> Optional[Any]:
        """Recupera valor do cache"""
        cache_key = self._generate_key(key)
        
        with self._lock:
            if cache_key not in self._cache:
                self._miss_count += 1
                logger.debug(f"Cache MISS: {cache_key}")
                return None
            
            entry = self._cache[cache_key]
            
            # Verifica expiração
            if self._is_expired(entry):
                del self._cache[cache_key]
                self._miss_count += 1
                logger.debug(f"Cache EXPIRED: {cache_key}")
                return None
            
            # Atualiza último acesso
            entry['last_access'] = time.time()
            self._hit_count += 1
            logger.debug(f"Cache HIT: {cache_key}")
            return entry['value']
    
    def set(self, key: Union[str, Dict, List], value: Any, ttl: Optional[int] = None):
        """Armazena valor no cache"""
        cache_key = self._generate_key(key)
        ttl = ttl if ttl is not None else self.default_ttl
        
        with self._lock:
            # Remove expirados antes de adicionar novo
            self._evict_expired()
            
            # Remove LRU se necessário
            self._evict_lru()
            
            # Calcula tempo de expiração
            if ttl == -1:  # Cache permanente
                expires_at = float('inf')
            else:
                expires_at = time.time() + ttl
            
            # Armazena entrada
            self._cache[cache_key] = {
                'value': value,
                'ttl': ttl,
                'expires_at': expires_at,
                'last_access': time.time(),
                'created_at': time.time()
            }
            
            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
    
    def delete(self, key: Union[str, Dict, List]):
        """Remove entrada específica do cache"""
        cache_key = self._generate_key(key)
        
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug(f"Cache DELETE: {cache_key}")
    
    def clear(self):
        """Limpa todo o cache"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hit_count = 0
            self._miss_count = 0
            logger.info(f"Cache limpo: {count} entradas removidas")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_count': self._hit_count,
                'miss_count': self._miss_count,
                'hit_rate': round(hit_rate, 2),
                'default_ttl': self.default_ttl
            }
    
    def cleanup(self):
        """Força limpeza de entradas expiradas"""
        with self._lock:
            self._evict_expired()

# Instância global do cache
app_cache = InMemoryCache(default_ttl=300, max_size=1000)

# Cache específico para consultas de busca
search_cache = InMemoryCache(default_ttl=120, max_size=500)

# Cache para dados estáticos (montadoras, grupos, etc.)
static_cache = InMemoryCache(default_ttl=3600, max_size=100)  # 1 hora

def cached(ttl: int = None, cache_instance: InMemoryCache = None):
    """
    Decorador para cache automático de funções
    
    Args:
        ttl: Tempo de vida em segundos (None = padrão do cache)
        cache_instance: Instância específica do cache (None = cache principal)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = cache_instance or app_cache
            
            # Gera chave baseada na função e argumentos
            cache_key = {
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            
            # Tenta buscar no cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executa função e cacheia resultado
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Adiciona método para invalidar cache da função
        wrapper.cache_clear = lambda: cache.delete({
            'function': func.__name__,
            'args': (),
            'kwargs': {}
        })
        
        return wrapper
    return decorator

def cache_search_results(func):
    """Decorador específico para cachear resultados de busca"""
    return cached(ttl=120, cache_instance=search_cache)(func)

def cache_static_data(func):
    """Decorador específico para cachear dados estáticos"""
    return cached(ttl=3600, cache_instance=static_cache)(func)

def invalidate_product_cache(produto_id: int = None):
    """
    Invalida caches relacionados a produtos
    
    Args:
        produto_id: ID específico do produto (None = invalida tudo relacionado)
    """
    if produto_id:
        # Invalida caches específicos do produto
        keys_to_invalidate = [
            f"produto_{produto_id}",
            f"produto_similares_{produto_id}",
            f"produto_aplicacoes_{produto_id}"
        ]
        
        for key in keys_to_invalidate:
            app_cache.delete(key)
            search_cache.delete(key)
    else:
        # Invalida todo cache relacionado a produtos
        search_cache.clear()
        logger.info("Cache de busca invalidado devido a alteração em produtos")

def invalidate_search_cache():
    """Invalida apenas o cache de busca"""
    search_cache.clear()

def get_cache_stats() -> Dict[str, Any]:
    """Retorna estatísticas de todos os caches"""
    return {
        'app_cache': app_cache.get_stats(),
        'search_cache': search_cache.get_stats(),
        'static_cache': static_cache.get_stats()
    }

def cleanup_all_caches():
    """Limpa entradas expiradas de todos os caches"""
    app_cache.cleanup()
    search_cache.cleanup() 
    static_cache.cleanup()
    logger.info("Limpeza de cache concluída")

class RequestCache:
    """Cache específico para a duração de uma requisição"""
    
    def __init__(self):
        self._data = {}
    
    def get(self, key: str, default=None):
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any):
        self._data[key] = value
    
    def has(self, key: str) -> bool:
        return key in self._data

# Cache por requisição (limpo automaticamente)
request_cache = RequestCache()

def request_cached(func):
    """Decorador para cache válido apenas durante a requisição"""
    @wraps(func)  
    def wrapper(*args, **kwargs):
        # Gera chave única
        cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
        
        # Verifica se já está em cache na requisição
        if request_cache.has(cache_key):
            return request_cache.get(cache_key)
        
        # Executa e armazena
        result = func(*args, **kwargs)
        request_cache.set(cache_key, result)
        
        return result
    return wrapper

# Integração com Flask para limpar cache por requisição
def init_cache_system(app):
    """Inicializa o sistema de cache com a aplicação Flask"""
    
    @app.before_request
    def clear_request_cache():
        """Limpa cache por requisição no início de cada request"""
        global request_cache
        request_cache = RequestCache()
    
    @app.after_request  
    def log_cache_stats(response):
        """Log das estatísticas de cache após cada request (apenas em debug)"""
        if app.debug and request.path.startswith('/api/'):
            stats = get_cache_stats()
            app.logger.debug(f"Cache stats - App: {stats['app_cache']['hit_rate']}% hit rate")
        return response
    
    logger.info("Sistema de cache inicializado com Flask")

# Funções auxiliares para uso comum
def cache_key_for_search(params: Dict) -> str:
    """Gera chave padronizada para buscas"""
    # Remove parâmetros vazios e ordena
    clean_params = {k: v for k, v in params.items() if v}
    return f"search_{hashlib.md5(json.dumps(clean_params, sort_keys=True).encode()).hexdigest()}"

def warm_up_cache():
    """Aquece o cache com dados mais utilizados"""
    try:
        # Podemos implementar aquecimento do cache aqui
        # Ex: pré-carregar dados de montadoras, grupos mais acessados
        logger.info("Aquecimento do cache iniciado")
        
        # Exemplo: buscar dados estáticos comuns
        from core_utils import _get_form_datalists
        datalists = _get_form_datalists()
        static_cache.set('form_datalists', datalists, ttl=-1)  # Cache permanente
        
        logger.info("Aquecimento do cache concluído")
        
    except Exception as e:
        logger.error(f"Erro no aquecimento do cache: {str(e)}")

# Middleware de monitoramento
class CacheMonitor:
    """Monitor de performance do cache"""
    
    def __init__(self):
        self.enabled = False
        self.slow_queries = []
        self.threshold_ms = 100  # Queries > 100ms são consideradas lentas
    
    def log_query_time(self, operation: str, duration_ms: float):
        """Log de tempo de query"""
        if duration_ms > self.threshold_ms:
            self.slow_queries.append({
                'operation': operation,
                'duration_ms': duration_ms,
                'timestamp': datetime.utcnow()
            })
            
            # Mantém apenas os últimos 50 registros
            self.slow_queries = self.slow_queries[-50:]
    
    def get_slow_queries(self) -> List[Dict]:
        """Retorna queries lentas registradas"""
        return self.slow_queries

cache_monitor = CacheMonitor()