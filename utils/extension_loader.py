"""확장 로더"""
from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Any
import discord

logger = logging.getLogger(__name__)


class ExtensionLoader:
    """Discord Bot 확장(명령어) 로더"""
    
    def __init__(self, bot: discord.Bot, module_name: str = "Stack"):
        self.bot = bot
        self.module_name = module_name
        self.loaded_extensions: list[str] = []
        self.failed_extensions: dict[str, str] = {}
    
    def load_all_extensions(self, commands_dir: str = "commands") -> None:
        """모든 확장 로드"""
        base_path = Path(__file__).parent.parent
        commands_path = base_path / commands_dir
        
        if not commands_path.exists():
            return
        
        extension_files = self._discover_extensions(commands_path, commands_dir)
        
        if not extension_files:
            return
        
        for extension in extension_files:
            self.load_extension(extension)
    
    def _discover_extensions(self, commands_path: Path, commands_dir: str) -> list[str]:
        """확장 파일 탐색"""
        extension_files = []
        group_folders = set()
        
        for folder_path in commands_path.rglob('*'):
            if folder_path.is_dir() and self._is_valid_extension_directory(folder_path):
                if self._has_init_file(folder_path):
                    group_folders.add(folder_path)
                    relative_path = folder_path.relative_to(commands_path.parent)
                    extension_name = str(relative_path).replace(os.sep, '.')
                    extension_files.append(extension_name)
        
        for file_path in commands_path.rglob('*.py'):
            if self._is_valid_extension_file(file_path):
                is_in_group = any(file_path.is_relative_to(gf) for gf in group_folders)
                if not is_in_group:
                    relative_path = file_path.relative_to(commands_path.parent)
                    extension_name = str(relative_path.with_suffix('')).replace(os.sep, '.')
                    extension_files.append(extension_name)
        
        return sorted(extension_files)
    
    def _is_valid_extension_file(self, file_path: Path) -> bool:
        """유효한 확장 파일인지 확인"""
        return (not file_path.name.startswith('__') and 
                not file_path.name.startswith('.') and
                file_path.suffix == '.py')
    
    def _is_valid_extension_directory(self, dir_path: Path) -> bool:
        """유효한 확장 디렉토리인지 확인"""
        invalid_names = {'__pycache__', '.git'}
        return (not dir_path.name.startswith('__') and 
                not dir_path.name.startswith('.') and
                dir_path.name not in invalid_names)
    
    def _has_init_file(self, dir_path: Path) -> bool:
        """__init__.py 파일이 있는지 확인"""
        return (dir_path / '__init__.py').exists()
    
    def load_extension(self, extension_name: str) -> tuple[bool, int]:
        """확장 로드"""
        try:
            self.bot.load_extension(extension_name)
            self.loaded_extensions.append(extension_name)
            return True, 1
        except Exception as e:
            self.failed_extensions[extension_name] = str(e)
            logger.error(f"확장 로드 실패: {extension_name} - {e}")
            return False, 1
    
    def get_loaded_extensions(self) -> list[str]:
        """로드된 확장 목록"""
        return self.loaded_extensions.copy()
    
    def get_failed_extensions(self) -> dict[str, str]:
        """실패한 확장 목록"""
        return self.failed_extensions.copy()
