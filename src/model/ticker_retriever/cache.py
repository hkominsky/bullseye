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
        
        Args:
            filepath (str): Path to the cached file
            max_age_days (int): Maximum age in days before the file is considered expired
            
        Returns:
            bool: True if the file is expired or doesn't exist, False otherwise
        """
        pass
    
    @abstractmethod
    def read(self, filepath: str) -> Dict[str, Any]:
        """
        Read and parse cached data from a file.
        
        Args:
            filepath (str): Path to the cached file to read
            
        Returns:
            Dict[str, Any]: Parsed data from the cached file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        pass
    
    @abstractmethod
    def write(self, filepath: str, data: str) -> None:
        """
        Write data to a cache file.
        
        Args:
            filepath (str): Path where the cache file should be written
            data (str): Data to write to the cache file
            
        Raises:
            IOError: If there's an error writing to the file
        """
        pass

class FileCache(CacheInterface):
    """
    File-based implementation of the cache interface.
    
    This class provides caching functionality using the local filesystem,
    with support for expiration checking based on file modification time.
    """
    
    SECONDS_IN_DAY = 86400
    
    def is_expired(self, filepath: str, max_age_days: int) -> bool:
        """
        Check if a cached file has expired based on its modification time.
        
        Args:
            filepath (str): Path to the cached file
            max_age_days (int): Maximum age in days before the file is considered expired
            
        Returns:
            bool: True if the file is expired or doesn't exist, False otherwise
        """
        if not os.path.exists(filepath):
            return True
        file_age = time.time() - os.path.getmtime(filepath)
        return file_age > (max_age_days * self.SECONDS_IN_DAY)
    
    def read(self, filepath: str) -> Dict[str, Any]:
        """
        Read and parse JSON data from a cached file.
        
        Args:
            filepath (str): Path to the cached file to read
            
        Returns:
            Dict[str, Any]: Parsed JSON data from the cached file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
            IOError: If there's an error reading the file
        """
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def write(self, filepath: str, data: str) -> None:
        """
        Write string data to a cache file.
        
        Creates the directory structure if it doesn't exist.
        
        Args:
            filepath (str): Path where the cache file should be written
            data (str): Data to write to the cache file
            
        Raises:
            IOError: If there's an error writing to the file
            OSError: If there's an error creating the directory structure
        """
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            f.write(data)