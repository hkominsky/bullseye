import os
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.model.utils.logger_config import LoggerSetup


class CacheInterface(ABC):
    """
    Abstract base class defining the interface for cache implementations
    
    including expiration checking, reading, and writing cache data.
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
    
    def __init__(self):
        self.logger = LoggerSetup.setup_logger(__name__)
        self.logger.info("FileCache initialized")
    
    def is_expired(self, filepath: str, max_age_days: int) -> bool:
        """
        Check if a cached file has expired based on its modification time.
        """
        if not os.path.exists(filepath):
            self.logger.debug(f"Cache file does not exist: {filepath}")
            return True
        
        file_age = time.time() - os.path.getmtime(filepath)
        age_days = file_age / self.SECONDS_IN_DAY
        is_expired = file_age > (max_age_days * self.SECONDS_IN_DAY)
        
        self.logger.debug(f"Cache file {filepath} age: {age_days:.2f} days, max age: {max_age_days} days, expired: {is_expired}")
        return is_expired
    
    def read(self, filepath: str) -> Dict[str, Any]:
        """
        Read and parse JSON data from a cached file.
        """
        try:
            self.logger.debug(f"Reading cache file: {filepath}")
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.logger.debug(f"Successfully read cache file with {len(data)} entries")
            return data
        except Exception as e:
            self.logger.error(f"Error reading cache file {filepath}: {e}")
            raise
    
    def write(self, filepath: str, data: str) -> None:
        """
        Write string data to a cache file.
        """
        try:
            self.logger.debug(f"Writing cache file: {filepath}")
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                f.write(data)
            self.logger.debug(f"Successfully wrote cache file: {filepath}")
        except Exception as e:
            self.logger.error(f"Error writing cache file {filepath}: {e}")
            raise