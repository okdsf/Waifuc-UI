"""
配置管理器模块 - 管理应用程序的配置和设置
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path


class ConfigManager:
    """
    管理应用程序配置和用户设置
    """
    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为用户目录下的 .image_processor
        """
        if config_dir is None:
            config_dir = os.path.join(str(Path.home()), '.image_processor')
        
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, 'config.json')
        
        # 创建配置目录
        os.makedirs(config_dir, exist_ok=True)
        
        # 默认配置
        self.default_config = {
            'general': {
                'output_directory': str(Path.home() / 'Pictures' / 'ProcessedImages'),
                'temp_directory': None,  # 使用系统临时目录
                'log_level': 'INFO',
            },
            'ui': {
                'theme': 'default',
                'language': 'zh_CN',
                'show_tooltips': True,
            },
            'processing': {
                'default_prefix': 'output',
                'default_sizes': {
                    '1:1': 1024,
                    '2:3': 960,
                    '3:2': 960
                },
            },
            'sources': {
                'danbooru': {
                    'default_limit': 100,
                },
                'sankaku': {
                    'username': '',
                    'password': '',
                    'default_limit': 100,
                },
                'pixiv': {
                    'username': '',
                    'password': '',
                    'default_limit': 100,
                },
            },
            'recent_workflows': [],  # 最近使用的工作流
            'recent_sources': [],    # 最近使用的图像来源
            'recent_directories': [], # 最近使用的目录
        }
        
        # 加载配置
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件，如果不存在则使用默认配置
        
        Returns:
            配置字典
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # 合并配置，保留新增的默认值
                return self.merge_configs(self.default_config, loaded_config)
            else:
                # 配置文件不存在，使用默认配置并保存
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置，默认为当前配置
            
        Returns:
            保存是否成功
        """
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置项键名，使用点号分隔嵌套字典，例如 'general.output_directory'
            default: 未找到时的默认值
            
        Returns:
            配置项值或默认值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key: 配置项键名，使用点号分隔嵌套字典，例如 'general.output_directory'
            value: 配置项值
        """
        keys = key.split('.')
        target = self.config
        
        # 遍历到倒数第二级
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        # 设置值
        target[keys[-1]] = value
        
        # 保存配置
        self.save_config()
    
    def add_recent_workflow(self, workflow_id: str) -> None:
        """
        添加最近使用的工作流
        
        Args:
            workflow_id: 工作流ID
        """
        recent = self.get('recent_workflows', [])
        
        # 如果已存在，移到列表首位
        if workflow_id in recent:
            recent.remove(workflow_id)
        
        # 添加到列表首位
        recent.insert(0, workflow_id)
        
        # 最多保留10个
        recent = recent[:10]
        
        self.set('recent_workflows', recent)
    
    def add_recent_source(self, source_config: Dict[str, Any]) -> None:
        """
        添加最近使用的图像来源
        
        Args:
            source_config: 图像来源配置
        """
        recent = self.get('recent_sources', [])
        
        # 检查是否存在相同配置
        for i, item in enumerate(recent):
            if item.get('type') == source_config.get('type') and \
               item.get('params') == source_config.get('params'):
                recent.pop(i)
                break
        
        # 添加到列表首位
        recent.insert(0, source_config)
        
        # 最多保留10个
        recent = recent[:10]
        
        self.set('recent_sources', recent)
    
    def add_recent_directory(self, directory: str) -> None:
        """
        添加最近使用的目录
        
        Args:
            directory: 目录路径
        """
        recent = self.get('recent_directories', [])
        
        # 如果已存在，移到列表首位
        if directory in recent:
            recent.remove(directory)
        
        # 添加到列表首位
        recent.insert(0, directory)
        
        # 最多保留10个
        recent = recent[:10]
        
        self.set('recent_directories', recent)
    
    @staticmethod
    def merge_configs(default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并配置，保留新增的默认值
        
        Args:
            default: 默认配置
            loaded: 加载的配置
            
        Returns:
            合并后的配置
        """
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result


# 创建全局实例
config_manager = ConfigManager()
