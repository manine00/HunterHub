from abc import ABC, abstractmethod
from typing import List, Dict

class JobScraper(ABC):
    """
    The Base Strategy interface for all job scrapers.
    """
    
    @abstractmethod
    def fetch_jobs(self, keyword: str, location: str) -> List[Dict]:
        """
        Must return a list of dictionaries containing:
        - title
        - company
        - description
        - url
        - date_posted
        """
        pass