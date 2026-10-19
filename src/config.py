# src/config.py
import configparser
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

def get_app_root() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(os.path.dirname(sys.executable))
    return Path(__file__).resolve().parent.parent

@dataclass(frozen=True)  # frozen=True делает конфиг неизменяемым после создания
class Config:
    # Пути
    app_root: Path
    trips_base_path: Path
    
    # Настройки уведомлений
    start_lock: int
    end_lock: int
    start_notification_offsets: List[int]
    end_notification_offsets: List[int]

    @classmethod
    def load(cls):
        """Фабричный метод для загрузки из файла"""
        root = get_app_root()
        config_path = root / 'config_mails.ini'
        
        if not config_path.exists():
            raise FileNotFoundError(f"Конфигурационный файл не найден: {config_path}")

        parser = configparser.ConfigParser()
        parser.read(str(config_path), encoding='utf-8')

        return cls(
            app_root=root,
            trips_base_path=Path(parser.get('files', 'TRIPS_BASE_PATH')),
            start_lock=parser.getint('mails', 'START_LOCK'),
            end_lock=parser.getint('mails', 'END_LOCK'),
            start_notification_offsets=[
                int(x.strip()) for x in parser.get('mails', 'START_NOTIFICATION').split(',')
            ],
            end_notification_offsets=[
                int(x.strip()) for x in parser.get('mails', 'END_NOTIFICATION').split(',')
            ]
        )

# Создаем экземпляр-синглтон на уровне модуля
try:
    settings = Config.load()
except Exception as e:
    print(f"Критическая ошибка загрузки конфигурации: {e}")
    sys.exit(1)