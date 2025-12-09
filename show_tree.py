#!/usr/bin/env python3
"""
tree.py - Вывод структуры каталогов с учетом .gitignore
Использование: python tree.py [путь] [--level N] [--all] [--gitignore]
"""

import os
import sys
import argparse
from pathlib import Path
import fnmatch

class TreePrinter:
    def __init__(self, root_dir, max_level=None, show_all=False, use_gitignore=True):
        self.root_dir = Path(root_dir).resolve()
        self.max_level = max_level
        self.show_all = show_all
        self.use_gitignore = use_gitignore
        self.gitignore_patterns = []
        
        if self.use_gitignore:
            self._load_gitignore_patterns()
    
    def _load_gitignore_patterns(self):
        """Загружает и парсит .gitignore файлы"""
        current_dir = self.root_dir
        
        while current_dir != current_dir.parent:  # Пока не достигли корня
            gitignore_file = current_dir / '.gitignore'
            
            if gitignore_file.exists():
                with open(gitignore_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        
                        # Пропускаем пустые строки и комментарии
                        if not line or line.startswith('#'):
                            continue
                        
                        # Преобразуем шаблоны .gitignore в fnmatch
                        pattern = line
                        
                        # Обработка директорий (оканчивающихся на /)
                        if pattern.endswith('/'):
                            pattern = pattern[:-1]
                        
                        # Преобразуем **
                        if '**' in pattern:
                            pattern = pattern.replace('**', '*')
                        
                        # Добавляем в список с учетом относительного пути
                        rel_path = gitignore_file.parent.relative_to(self.root_dir)
                        if str(rel_path) != '.':
                            pattern = str(rel_path / pattern)
                        
                        self.gitignore_patterns.append(pattern)
            
            current_dir = current_dir.parent
        
        # Добавляем стандартные игнорируемые папки
        default_ignores = [
            '.git',
            '__pycache__',
            '.pytest_cache',
            '.vscode',
            '.idea',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.Python',
            'build/',
            'develop-eggs/',
            'dist/',
            'downloads/',
            'eggs/',
            '.eggs/',
            'lib/',
            'lib64/',
            'parts/',
            'sdist/',
            'var/',
            'wheels/',
            '*.egg-info/',
            '.installed.cfg',
            '*.egg',
            'venv/',
            'env/',
            '.env',
            '.venv',
            'node_modules/',
            'target/',
            '.DS_Store',
            'thumbs.db',
        ]
        
        self.gitignore_patterns.extend(default_ignores)
    
    def _is_ignored(self, path):
        """Проверяет, должен ли файл/папка быть проигнорирован"""
        if not self.use_gitignore:
            return False
        
        # Проверяем скрытые файлы (начинающиеся с точки)
        if not self.show_all and path.name.startswith('.'):
            # Но не игнорируем сам .gitignore
            if path.name == '.gitignore':
                return False
            # И не игнорируем .env если нужно показать все
            if not self.show_all:
                return True
        
        rel_path = str(path.relative_to(self.root_dir))
        
        # Проверяем все паттерны
        for pattern in self.gitignore_patterns:
            # Для простых совпадений
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # Для совпадений внутри директорий
            if fnmatch.fnmatch(str(path.name), pattern):
                return True
            # Для путей, начинающихся с pattern
            if pattern.endswith('/') and rel_path.startswith(pattern[:-1]):
                return True
        
        return False
    
    def print_tree(self):
        """Выводит дерево каталогов"""
        print(f"\033[1m{self.root_dir}\033[0m")
        self._print_directory(self.root_dir, 0, [], is_last=True)
        print()
    
    def _print_directory(self, directory, level, parent_prefix, is_last=True):
        """Рекурсивно выводит содержимое директории"""
        if self.max_level is not None and level >= self.max_level:
            return
        
        try:
            # Получаем список элементов, исключая игнорируемые
            items = []
            for item in sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if not self._is_ignored(item):
                    items.append(item)
        except PermissionError:
            items = []
        
        for index, item in enumerate(items):
            is_last_item = (index == len(items) - 1)
            
            # Определяем префиксы
            if level == 0:
                current_prefix = ""
            else:
                current_prefix = "".join(parent_prefix)
                current_prefix += "└── " if is_last else "├── "
            
            # Выводим текущий элемент
            icon = "📁 " if item.is_dir() else "📄 "
            if item.is_dir():
                print(f"{current_prefix}{icon}\033[1;34m{item.name}\033[0m")
            elif item.suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h']:
                print(f"{current_prefix}{icon}\033[1;32m{item.name}\033[0m")  # Зеленый для кода
            elif item.suffix in ['.md', '.txt', '.rst']:
                print(f"{current_prefix}{icon}\033[1;33m{item.name}\033[0m")  # Желтый для текста
            elif item.suffix in ['.json', '.yaml', '.yml', '.xml']:
                print(f"{current_prefix}{icon}\033[1;35m{item.name}\033[0m")  # Пурпурный для конфигов
            else:
                print(f"{current_prefix}{icon}{item.name}")
            
            # Рекурсивно обрабатываем директории
            if item.is_dir():
                new_prefix = parent_prefix.copy()
                new_prefix.append("    " if is_last else "│   ")
                self._print_directory(item, level + 1, new_prefix, is_last_item)

def main():
    parser = argparse.ArgumentParser(
        description="Вывод структуры каталогов с учетом .gitignore",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python tree.py                        # Текущая директория
  python tree.py /path/to/project       # Указанная директория
  python tree.py --level 3              # Ограничить глубину
  python tree.py --all                  # Показать все файлы (включая .git)
  python tree.py --no-gitignore         # Игнорировать .gitignore
  python tree.py --gitignore-only       # Только .gitignore правила
        """
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Путь к директории (по умолчанию: текущая)'
    )
    parser.add_argument(
        '--level', '-L',
        type=int,
        help='Максимальная глубина отображения'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Показать все файлы (включая скрытые)'
    )
    parser.add_argument(
        '--no-gitignore',
        action='store_true',
        help='Не учитывать .gitignore'
    )
    parser.add_argument(
        '--gitignore-only',
        action='store_true',
        help='Использовать только .gitignore без стандартных исключений'
    )
    parser.add_argument(
        '--dirs-only', '-d',
        action='store_true',
        help='Показывать только директории'
    )
    
    args = parser.parse_args()
    
    # Проверяем существование пути
    if not os.path.exists(args.path):
        print(f"Ошибка: путь '{args.path}' не существует", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(args.path):
        print(f"Ошибка: '{args.path}' не является директорией", file=sys.stderr)
        sys.exit(1)
    
    # Создаем и запускаем tree printer
    use_gitignore = not args.no_gitignore
    show_all = args.all
    
    printer = TreePrinter(
        root_dir=args.path,
        max_level=args.level,
        show_all=show_all,
        use_gitignore=use_gitignore
    )
    
    printer.print_tree()

if __name__ == "__main__":
    main()