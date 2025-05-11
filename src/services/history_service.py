"""
历史记录服务：包装 src/data/execution_history.py，提供任务记录查询功能，
返回字典数据，供 Gradio 前端使用。
"""
from src.data.execution_history import history_manager
from typing import List, Optional, Dict

class HistoryError(Exception):
    pass

class HistoryService:
    @staticmethod
    def get_all_records() -> List[Dict]:
        """获取所有任务记录，返回字典列表"""
        records = history_manager.get_all_records()
        return [record.to_dict() for record in records]

    @staticmethod
    def get_record(record_id: str) -> Optional[Dict]:
        """获取指定任务记录，返回字典数据或 None"""
        record = history_manager.get_record(record_id)
        return record.to_dict() if record else None