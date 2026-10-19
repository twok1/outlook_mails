import json
import os
import sys
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import logging

from ...models import Reminder

logger = logging.getLogger(__name__)

class ReminderStorage:
    """Класс для хранения и управления напоминаниями в JSON-файле."""
    
    def __init__(self):
        # Определяем правильный путь для хранения данных
        self.storage_dir = self._get_data_dir()
        self.storage_dir.mkdir(exist_ok=True)
        self.storage_file = self.storage_dir / 'existing_reminds.json'
        self._ensure_storage_exists()
    
    def _get_data_dir(self) -> Path:
        """
        Определяет правильную директорию для хранения данных.
        Для exe использует папку рядом с исполняемым файлом.
        Для разработки использует папку src/data.
        """
        if getattr(sys, 'frozen', False):
            # Запуск из exe
            # Используем папку рядом с exe-файлом
            exe_dir = Path(os.path.dirname(sys.executable))
            data_dir = exe_dir / 'data'
        else:
            # Запуск из скрипта (разработка)
            # Используем папку в корне проекта
            data_dir = Path(__file__).parent.parent / 'data'
        
        # Создаем директорию, если её нет
        data_dir.mkdir(exist_ok=True)
        return data_dir
    
    def _ensure_storage_exists(self):
        """Создает файл хранилища, если он не существует."""
        if not self.storage_file.exists():
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def _read_storage(self) -> List[dict]:
        """Читает данные из файла хранилища."""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_storage(self, data: List[dict]):
        """Записывает данные в файл хранилища."""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def get_all_reminders(self) -> List[Reminder]:
        """Получает все сохраненные напоминания."""
        data = self._read_storage()
        reminders = []
        for item in data:
            try:
                reminder = Reminder(
                    reminder_date=datetime.fromisoformat(item['date']),
                    subject=item['subject'],
                    text=item['text']
                )
                if 'id' in item:
                    reminder.reminder_id = item['id']
                reminders.append(reminder)
            except Exception as e:
                logger.error(f"Ошибка загрузки напоминания", exc_info=True)
        return reminders
    
    def get_reminder_key(self, reminder: Reminder) -> Tuple[str, str]:
        """Создает уникальный ключ для напоминания."""
        date_str = reminder.reminder_date.strftime('%Y-%m-%d')
        return (date_str, reminder.subject)
    
    def add_reminder(self, reminder: Reminder) -> bool:
        """Добавляет напоминание в хранилище."""
        data = self._read_storage()
        
        # Проверяем, существует ли уже такое напоминание
        key = self.get_reminder_key(reminder)
        for item in data:
            if (item['date'] == key[0] and item['subject'] == key[1]):
                return False  # Уже существует
        
        # Добавляем новое напоминание
        new_item = {
            'date': key[0],
            'subject': reminder.subject,
            'text': reminder.text,
            'id': getattr(reminder, 'reminder_id', None)
        }
        data.append(new_item)
        self._write_storage(data)
        return True
    
    def add_reminders(self, reminders: List[Reminder]) -> int:
        """Добавляет несколько напоминаний в хранилище."""
        added_count = 0
        for reminder in reminders:
            if self.add_reminder(reminder):
                added_count += 1
        return added_count
    
    def remove_reminder(self, reminder: Reminder) -> bool:
        """Удаляет напоминание из хранилища."""
        data = self._read_storage()
        key = self.get_reminder_key(reminder)
        
        initial_count = len(data)
        data = [item for item in data 
                if not (item['date'] == key[0] and item['subject'] == key[1])]
        
        if len(data) < initial_count:
            self._write_storage(data)
            return True
        return False
    
    def remove_reminders(self, reminders: List[Reminder]) -> int:
        """Удаляет несколько напоминаний из хранилища."""
        removed_count = 0
        for reminder in reminders:
            if self.remove_reminder(reminder):
                removed_count += 1
        return removed_count
    
    def clear(self):
        """Очищает все напоминания."""
        self._write_storage([])
    
    def get_reminders_to_add(self, new_reminders: List[Reminder]) -> List[Reminder]:
        """Возвращает список напоминаний, которые еще не созданы."""
        existing = self.get_all_reminders()
        existing_keys = {self.get_reminder_key(r) for r in existing}
        
        to_add = []
        for reminder in new_reminders:
            if self.get_reminder_key(reminder) not in existing_keys:
                to_add.append(reminder)
        
        return to_add
    
    def get_reminders_to_remove(self, current_reminders: List[Reminder]) -> List[Reminder]:
        """Возвращает список напоминаний, которые нужно удалить (существуют
        в хранилище, но отсутствуют в текущем списке)."""
        existing = self.get_all_reminders()
        current_keys = {self.get_reminder_key(r) for r in current_reminders}
        
        to_remove = []
        for reminder in existing:
            if self.get_reminder_key(reminder) not in current_keys:
                to_remove.append(reminder)
        
        return to_remove