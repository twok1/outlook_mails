import os
import sys
from pathlib import Path

import pyperclip
import pathspec

# Каталоги, которые нужно обработать (включая подкаталоги)
DIRECTORIES = (
    'src',
    'tests',
    'utils',
    # добавь свои каталоги здесь
)

# Расширения файлов, которые нужно собирать из корневого каталога
ROOT_EXTENSIONS = ('.py', '.pyw')

# Расширения файлов, которые собираются из указанных каталогов
TARGET_EXTENSIONS = ('.py', '.pyw', '.txt', '.md', '.json', '.yaml', '.yml',
                     '.toml', '.cfg', '.ini')

# Файл, который будет сохранять результат (опционально)
OUTPUT_FILE = 'project_dump.txt'

# Дополнительные каталоги для пропуска (помимо .gitignore)
EXTRA_SKIP_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env', '.idea', '.vscode',
    'node_modules', '.mypy_cache', '.pytest_cache', 'build', 'dist',
    '.tox', '.eggs',
}


class GitIgnoreFilter:
    """Фильтр файлов и каталогов на основе .gitignore."""

    def __init__(self, root: Path):
        self.root = root
        self.specs: list[tuple[Path, pathspec.PathSpec]] = []
        self._load_gitignores(root)

    def _load_gitignores(self, root: Path):
        """Загружает все .gitignore, найденные в дереве проекта."""
        for dirpath, dirnames, filenames in os.walk(root):
            # Не заходим в служебные каталоги
            dirnames[:] = [d for d in dirnames if d not in EXTRA_SKIP_DIRS
                           and not d.endswith('.egg-info')]

            if '.gitignore' in filenames:
                gi_path = Path(dirpath) / '.gitignore'
                try:
                    lines = gi_path.read_text(encoding='utf-8').splitlines()
                except Exception:
                    continue
                spec = pathspec.PathSpec.from_lines('gitwildmatch', lines)
                self.specs.append((Path(dirpath), spec))

    def is_ignored(self, path: Path, is_dir: bool = False) -> bool:
        """Проверяет, игнорируется ли путь хотя бы одним .gitignore."""
        try:
            path = path.resolve()
        except OSError:
            return False

        for base, spec in self.specs:
            try:
                rel = path.relative_to(base.resolve())
            except ValueError:
                continue
            rel_str = rel.as_posix()
            if is_dir:
                rel_str += '/'
            if spec.match_file(rel_str):
                return True
        return False


def is_self(path: Path, self_path: Path) -> bool:
    """Проверяет, является ли файл самим скриптом."""
    try:
        return path.resolve() == self_path.resolve()
    except OSError:
        return False


def should_skip_dir(dir_name: str) -> bool:
    """Пропускает служебные каталоги."""
    return dir_name in EXTRA_SKIP_DIRS or dir_name.endswith('.egg-info')


def collect_files(root: Path, self_path: Path,
                  gitignore: GitIgnoreFilter) -> list[Path]:
    """Собирает список файлов для обработки."""
    files = []
    seen = set()

    def add_file(path: Path):
        if is_self(path, self_path):
            return
        if gitignore.is_ignored(path, is_dir=False):
            return
        try:
            resolved = path.resolve()
        except OSError:
            return
        if resolved not in seen:
            seen.add(resolved)
            files.append(path)

    # 1. Файлы .py и .pyw в корневом каталоге
    for entry in sorted(root.iterdir()):
        if entry.is_file() and entry.suffix.lower() in ROOT_EXTENSIONS:
            add_file(entry)

    # 2. Файлы в указанных каталогах и их подкаталогах
    for dir_name in DIRECTORIES:
        target_dir = root / dir_name
        if not target_dir.exists() or not target_dir.is_dir():
            print(f'[!] Каталог не найден: {target_dir}', file=sys.stderr)
            continue

        if gitignore.is_ignored(target_dir, is_dir=True):
            print(f'[i] Каталог пропущен по .gitignore: {target_dir}')
            continue

        for dirpath, dirnames, filenames in os.walk(target_dir):
            # Пропускаем служебные каталоги и игнорируемые .gitignore
            pruned = []
            for d in sorted(dirnames):
                if should_skip_dir(d):
                    continue
                full = Path(dirpath) / d
                if gitignore.is_ignored(full, is_dir=True):
                    continue
                pruned.append(d)
            dirnames[:] = pruned

            for filename in sorted(filenames):
                file_path = Path(dirpath) / filename
                if file_path.suffix.lower() in TARGET_EXTENSIONS:
                    add_file(file_path)

    return files


def read_file_safe(path: Path) -> str:
    """Пытается прочитать файл, возвращает строку с содержимым или ошибкой."""
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding='cp1251')
        except Exception as e:
            return f'<не удалось прочитать файл: {e}>'
    except Exception as e:
        return f'<не удалось прочитать файл: {e}>'


def build_dump(root: Path, files: list[Path],
               gitignore: GitIgnoreFilter) -> str:
    """Формирует итоговый текст."""
    parts = []

    # Заголовок со структурой проекта
    parts.append('=' * 80)
    parts.append('# СТРУКТУРА ПРОЕКТА')
    parts.append('=' * 80)
    parts.append('')

    tree_lines = []
    for dirpath, dirnames, filenames in os.walk(root):
        pruned = []
        for d in sorted(dirnames):
            if should_skip_dir(d):
                continue
            full = Path(dirpath) / d
            if gitignore.is_ignored(full, is_dir=True):
                continue
            pruned.append(d)
        dirnames[:] = pruned

        rel_dir = Path(dirpath).relative_to(root)
        depth = len(rel_dir.parts)
        if str(rel_dir) == '.':
            depth = 0
            display = '.'
        else:
            display = rel_dir.name

        tree_lines.append('    ' * depth + f'{display}/')

        for filename in sorted(filenames):
            full = Path(dirpath) / filename
            if gitignore.is_ignored(full, is_dir=False):
                continue
            tree_lines.append('    ' * (depth + 1) + filename)

    parts.append('\n'.join(tree_lines))
    parts.append('')
    parts.append('=' * 80)
    parts.append('# СОДЕРЖИМОЕ ФАЙЛОВ')
    parts.append('=' * 80)
    parts.append('')

    for file_path in files:
        rel_path = file_path.relative_to(root)
        parts.append('')
        parts.append('#' * 80)
        parts.append(f'### FILE_PATH: {rel_path}')
        parts.append('#' * 80)
        parts.append('')
        content = read_file_safe(file_path)
        parts.append(content)
        if not content.endswith('\n'):
            parts.append('')
        parts.append('')

    return '\n'.join(parts)


def main():
    root = Path.cwd()
    self_path = Path(__file__).resolve()

    print(f'[i] Корневой каталог: {root}')
    print(f'[i] Каталоги для обхода: {DIRECTORIES}')

    gitignore = GitIgnoreFilter(root)
    if gitignore.specs:
        print(f'[i] Загружено .gitignore-файлов: {len(gitignore.specs)}')
    else:
        print('[i] .gitignore не найдены — фильтрация отключена.')

    files = collect_files(root, self_path, gitignore)
    print(f'[i] Найдено файлов: {len(files)}')
    for f in files:
        print(f'    - {f.relative_to(root)}')

    dump = build_dump(root, files, gitignore)

    output_path = root / OUTPUT_FILE
    output_path.write_text(dump, encoding='utf-8')
    print(f'\n[i] Сохранено в: {output_path}')

    try:
        pyperclip.copy(dump)
        print('[i] Скопировано в буфер обмена.')
    except Exception as e:
        print(f'[!] Не удалось скопировать в буфер обмена: {e}', file=sys.stderr)
        print('    Установите: pip install pyperclip')


if __name__ == '__main__':
    main()