import json
from typing import List, Dict

from src.utils import Config
from src.models import EmailData

class ProcessedMessagesStorage:
    """класс для хранения обработанных писем в таком формате:
    id_письма: [модули, которым оно передавалось]
    """
    def __init__(self, settings: Config) -> None:
        self.file_path = settings.data_path / 'processed_messages.json'
        self._ensure_exists()
        
    def _ensure_exists(self):
        """Создает пустой JSON-словарь, если файла еще нет."""
        if not self.file_path.exists():
            self._write({})

    def _read(self) -> Dict[str, List[str]]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write(self, data: Dict[str, List[str]]):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def filter_new(self, messages: List[EmailData], module_name: str) -> List[EmailData]:
        """Возвращает только те письма, которые указанный модуль еще не обрабатывал."""
        history = self._read()
        return [
            msg for msg in messages
            if module_name not in history.get(msg.message_id, [])
        ]

    def mark_as_processed(self, messages: List[EmailData], module_name: str):
        """Добавляет имя модуля в список обработчиков для каждого письма."""
        if not messages:
            return
            
        history = self._read()
        for msg in messages:
            if msg.message_id not in history:
                history[msg.message_id] = []
            if module_name not in history[msg.message_id]:
                history[msg.message_id].append(module_name)
                
        self._write(history)