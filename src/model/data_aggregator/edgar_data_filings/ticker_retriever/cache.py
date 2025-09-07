import os
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Any

class CacheInterface(ABC):
    """
    Abstract base class defining the interface for cache implementations.
    
    This interface provides a contract for cache operations including
    expiration checking, reading, and writing cache data.
    """
    
    @abstractmethod
    def is_expired(self, filepath: str, max_age_days: int) -> bool:
        """
        Check if a cached file has expired based on its age.
        """
        pass
    
    @abstractmethod
    def read(self, filepath: str) -> Dict[str, Any]:
        """
        Read and parse cached data from a file.
        """
        pass
    
    @abstractmethod
    def write(self, filepath: str, data: str) -> None:
        """
        Write data to a cache file.
        """
        pass

class FileCache(CacheInterface):
    """
    This class provides caching functionality using the local filesystem,
    with support for expiration checking based on file modification time.
    """
    
    SECONDS_IN_DAY = 86400
    
    def is_expired(self, filepath: str, max_age_days: int) -> bool:
        """
        Check if a cached file has expired based on its modification time.
        """
        if not os.path.exists(filepath):
            return True
        file_age = time.time() - os.path.getmtime(filepath)
        return file_age > (max_age_days * self.SECONDS_IN_DAY)
    
    def read(self, filepath: str) -> Dict[str, Any]:
        """
        Read and parse JSON data from a cached file.
        """
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def write(self, filepath: str, data: str) -> None:
        """
        Write string data to a cache file.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            f.write(data)