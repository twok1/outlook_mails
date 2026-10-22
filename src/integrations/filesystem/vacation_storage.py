# src/integrations/filesystem/vacation_storage.py
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from src.models import VacationData
from src.utils import Config

logger = logging.getLogger(__name__)

class VacationStorage:
    """Класс для сохранения информации об отпусках в JSON-файл."""
    
    def __init__(self, settings: Config):
        self.storage_dir = settings.data_path
        self.storage_dir.mkdir(exist_ok=True)
        self.storage_file = self.storage_dir / 'vacations.json'
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Создает файл хранилища, если он не существует."""
        if not self.storage_file.exists():
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump({"vacations": []}, f, ensure_ascii=False, indent=4)
    
    def save_vacations(self, vacations: List[VacationData]):
        """Добавляет новые отпуска в файл."""
        if not vacations:
            return
            
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Избегаем дубликатов по email_id
            existing_ids = {v.get("email_id") for v in data.get("vacations", [])}
            
            new_vacations = []
            for vac in vacations:
                if vac.email_id not in existing_ids:
                    # Преобразуем Pydantic модель в словарь
                    vac_dict = vac.model_dump(mode='json')
                    new_vacations.append(vac_dict)
                    existing_ids.add(vac.email_id)
            
            if new_vacations:
                if 'vacations' not in data:
                    data['vacations'] = []
                data["vacations"].extend(new_vacations)
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                logger.info(f"Успешно сохранено {len(new_vacations)} новых записей об отпусках.")
                
        except Exception as e:
            logger.error("Ошибка при сохранении информации об отпусках", exc_info=True)