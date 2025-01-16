import json
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

class ResponseCache:
    def __init__(self, cache_dir: str = ".cache", ttl_hours: int = 24):
        """
        Initialize the response cache.
        
        Args:
            cache_dir (str): Directory to store cache files
            ttl_hours (int): Time-to-live in hours for cache entries
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(hours=ttl_hours)
        self.stats = {
            "hits": 0,
            "misses": 0,
            "expired": 0,
            "errors": 0
        }
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _generate_cache_key(self, query: str, context_hash: str) -> str:
        """Generate a unique cache key from query and context."""
        combined = f"{query}:{context_hash}".encode('utf-8')
        return hashlib.sha256(combined).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{cache_key}.json"

    def _context_hash(self, context: list) -> str:
        """Generate a hash of the context messages."""
        # Sort and stringify context to ensure consistent hashing
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.sha256(context_str.encode('utf-8')).hexdigest()

    def get(self, query: str, context: list) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Retrieve a cached response if available and not expired.
        
        Args:
            query (str): The original query
            context (list): The context messages used
            
        Returns:
            Tuple[Optional[Dict[str, Any]], Dict[str, Any]]: 
                - Cached response or None if not found/expired
                - Current cache statistics
        """
        context_hash = self._context_hash(context)
        cache_key = self._generate_cache_key(query, context_hash)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            self.stats["misses"] += 1
            return None, self.stats

        try:
            with cache_path.open('r', encoding='utf-8') as f:
                cached_data = json.load(f)

            # Check if cache has expired
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                cache_path.unlink()  # Remove expired cache
                self.stats["expired"] += 1
                return None, self.stats

            self.stats["hits"] += 1
            cached_data["cached"] = True  # Mark as cached
            return cached_data, self.stats

        except (json.JSONDecodeError, KeyError, ValueError):
            # Remove corrupted cache file
            cache_path.unlink(missing_ok=True)
            self.stats["errors"] += 1
            return None, self.stats

    def set(self, query: str, context: list, response: Dict[str, Any]) -> None:
        """
        Store a response in the cache.
        
        Args:
            query (str): The original query
            context (list): The context messages used
            response (Dict[str, Any]): The response to cache
        """
        context_hash = self._context_hash(context)
        cache_key = self._generate_cache_key(query, context_hash)
        cache_path = self._get_cache_path(cache_key)

        try:
            with cache_path.open('w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.stats["errors"] += 1
            print(f"Warning: Failed to cache response: {str(e)}")

    def clear_expired(self) -> Tuple[int, Dict[str, Any]]:
        """
        Clear expired cache entries.
        
        Returns:
            Tuple[int, Dict[str, Any]]:
                - Number of cache entries cleared
                - Current cache statistics
        """
        cleared_count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with cache_file.open('r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                cached_time = datetime.fromisoformat(cached_data['timestamp'])
                if datetime.now() - cached_time > self.ttl:
                    cache_file.unlink()
                    cleared_count += 1
                    self.stats["expired"] += 1
            except:
                # Remove corrupted cache file
                cache_file.unlink()
                cleared_count += 1
                self.stats["errors"] += 1
        
        return cleared_count, self.stats

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        return self.stats 