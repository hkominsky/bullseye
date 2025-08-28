import os
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Any

class CacheInterface(ABC):
    @abstractmethod
    def is_expired(self, filepath: str, max_age_days: int) -> bool:
        pass
    
    @abstractmethod
    def read(self, filepath: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def write(self, filepath: str, data: str) -> None:
        pass

class FileCache(CacheInterface):
    SECONDS_IN_DAY = 86400
    
    def is_expired(self, filepath: str, max_age_days: int) -> bool:
        if not os.path.exists(filepath):
            return True
        file_age = time.time() - os.path.getmtime(filepath)
        return file_age > (max_age_days * self.SECONDS_IN_DAY)
    
    def read(self, filepath: str) -> Dict[str, Any]:
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def write(self, filepath: str, data: str) -> None:
        with open(filepath, 'w') as f:
            f.write(data)
