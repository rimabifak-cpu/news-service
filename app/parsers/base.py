"""
Базовый класс для парсеров
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ParsedItem:
    """Результат парсинга"""
    title: str
    content: str
    url: str
    image_url: Optional[str] = None
    published_at: Optional[datetime] = None
    author: Optional[str] = None


class BaseParser(ABC):
    """Базовый класс парсера"""
    
    def __init__(self, source_config: Dict[str, Any]):
        self.source_config = source_config
        self.url = source_config.get("url", "")
        self.name = source_config.get("name", "")
    
    @abstractmethod
    async def parse(self) -> List[ParsedItem]:
        """Парсинг источника"""
        pass
    
    @abstractmethod
    async def parse_single(self, url: str) -> Optional[ParsedItem]:
        """Парсинг отдельной страницы"""
        pass
    
    def extract_text(self, html_content: str, selector: Optional[str] = None) -> str:
        """Извлечение текста из HTML"""
        if not html_content:
            return ""
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')
        
        if selector:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return soup.get_text(strip=True)
