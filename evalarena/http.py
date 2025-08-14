"""HTTP client with caching and retry logic for EvalArena API."""

import asyncio
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, Optional

import diskcache
import httpx
from platformdirs import user_cache_dir
from rich.console import Console

from .auth import get_auth_headers
from .config import get_config

console = Console()

# Cache setup
CACHE_DIR = Path(user_cache_dir("evalarena"))
cache = diskcache.Cache(str(CACHE_DIR))


class EvalArenaHTTPError(Exception):
    """Custom exception for EvalArena API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


def create_client() -> httpx.AsyncClient:
    """Create configured HTTP client."""
    config = get_config()
    
    # Set up timeouts
    timeout = httpx.Timeout(
        connect=10.0,
        read=config.timeout_s,
        write=10.0,
        pool=5.0
    )
    
    # Set up retries for transient failures
    transport = httpx.AsyncHTTPTransport(retries=3)
    
    return httpx.AsyncClient(
        base_url=config.base_url,
        timeout=timeout,
        transport=transport,
        headers={
            "User-Agent": "evalarena-cli/0.1.0",
            "Accept": "application/json",
        }
    )


def get_cache_key(url: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Generate cache key for URL and parameters."""
    # Create a deterministic key based on URL and params
    content = f"{url}:{params or {}}"
    return hashlib.md5(content.encode()).hexdigest()


async def cached_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    bypass_cache: bool = False,
    cache_ttl: Optional[int] = None
) -> Dict[str, Any]:
    """
    Make cached GET request to EvalArena API.
    
    Args:
        url: API endpoint URL
        params: Query parameters
        bypass_cache: If True, skip cache and fetch fresh data
        cache_ttl: Cache TTL in seconds (uses config default if None)
    
    Returns:
        JSON response data
    
    Raises:
        EvalArenaHTTPError: On API errors
    """
    config = get_config()
    
    # Generate cache key
    cache_key = get_cache_key(url, params)
    
    # Check cache first (unless bypassing)
    if not bypass_cache and config.cache_enabled:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            # Check if cache entry is still valid
            cached_time, cached_response = cached_data
            ttl = cache_ttl or config.cache_ttl_seconds
            if time.time() - cached_time < ttl:
                return cached_response
    
    # Make fresh request
    async with create_client() as client:
        # Add auth headers
        headers = get_auth_headers()
        
        try:
            response = await client.get(url, params=params, headers=headers)
            
            # Handle different response codes
            if response.status_code == 200:
                data = response.json()
                
                # Cache successful response
                if config.cache_enabled:
                    cache.set(cache_key, (time.time(), data))
                
                return data
            
            elif response.status_code == 401:
                raise EvalArenaHTTPError(
                    "Authentication required. Run 'evalarena auth login' first.",
                    status_code=401
                )
            
            elif response.status_code == 403:
                raise EvalArenaHTTPError(
                    "Access forbidden. Check your API token permissions.",
                    status_code=403
                )
            
            elif response.status_code == 404:
                raise EvalArenaHTTPError(
                    f"Endpoint not found: {url}",
                    status_code=404
                )
            
            elif response.status_code == 429:
                raise EvalArenaHTTPError(
                    "Rate limit exceeded. Please try again later.",
                    status_code=429
                )
            
            else:
                # Try to get error details from response
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", f"HTTP {response.status_code}")
                except Exception:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                
                raise EvalArenaHTTPError(
                    f"API request failed: {error_msg}",
                    status_code=response.status_code
                )
        
        except httpx.RequestError as e:
            raise EvalArenaHTTPError(f"Network error: {str(e)}")
        
        except httpx.TimeoutException:
            raise EvalArenaHTTPError(f"Request timeout after {config.timeout_s}s")


async def health_check() -> tuple[bool, str]:
    """
    Check API health and connectivity.
    
    Returns:
        (is_healthy, status_message)
    """
    try:
        # Try the ping endpoint first
        try:
            response = await cached_get("/api/ping/", bypass_cache=True, cache_ttl=0)
            return True, "API is healthy"
        except EvalArenaHTTPError:
            # Ping endpoint might not exist, try models endpoint
            pass
        
        # Fallback to models endpoint with minimal data
        response = await cached_get("/api/models/", params={"limit": 1}, bypass_cache=True, cache_ttl=0)
        if isinstance(response, list):
            return True, f"API is healthy ({len(response)} models available)"
        else:
            return True, "API is healthy"
    
    except EvalArenaHTTPError as e:
        return False, f"API error: {e}"
    
    except Exception as e:
        return False, f"Unexpected error: {e}"


def clear_cache() -> int:
    """
    Clear all cached API responses.
    
    Returns:
        Number of cache entries cleared
    """
    count = len(cache)
    cache.clear()
    return count


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return {
        "size": len(cache),
        "cache_dir": str(CACHE_DIR),
        "enabled": get_config().cache_enabled,
        "ttl_seconds": get_config().cache_ttl_seconds,
    }


# Synchronous wrapper for simple cases
def sync_get(url: str, **kwargs: Any) -> Dict[str, Any]:
    """Synchronous wrapper for cached_get."""
    return asyncio.run(cached_get(url, **kwargs))
