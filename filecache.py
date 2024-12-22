import os
from pathlib import Path
from functools import wraps
import json
from typing import Any, Callable

def file_cache(cache_dir: str = "cache"):
    """
    A decorator that caches function results to files.
    Results are stored as JSON in the specified cache directory.
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(exist_ok=True)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            # Use a hash to avoid filename length/character issues
            cache_file = cache_path / f"{hash(cache_key)}.json"
            
            # Return cached result if it exists
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
                    
            # Calculate result and cache it
            result = func(*args, **kwargs)
            with open(cache_file, 'w') as f:
                json.dump(result, f)
                
            return result
            
        return wrapper
    return decorator
