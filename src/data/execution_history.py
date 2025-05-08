"""
执行历史模块 - 跟踪和记录图像处理任务的执行历史
"""
import os
import json
import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

from .config_manager import config_manager


class ExecutionRecord:
    """
    执行记录类，代表一次图像处理任务的执行记录
    """
    def __init__(self, workflow_id: str = None, workflow_name: str = None,
                 source_type: str = None, source_params: Dict[str, Any] = None,
                 output_directory: str = None, id: str = None):
        """
        初始化执行记录
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            source_type: 图像来源类型
            source_params: 图像来源参数
            output_directory: 输出目录
            id: 记录ID，如果不提供则自动生成
        """
        self.id = id or str(uuid.uuid4())
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.source_type = source_type
        self.source_params = source_params or {}
        self.output_directory = output_directory
        
        self.start_time = datetime.now().isoformat()
        self.end_time = None
        self.status = "running"  # running, completed, failed
        self.error_message = None
        
        self.total_images = 0
        self.processed_images = 0
        self.success_images = 0
        self.failed_images = 0
        
        self.step_logs: List[Dict[str, Any]] = []
    
    def add_step_log(self, step_id: str, step_name: str, status: str, 
                    message: str = None, details: Dict[str, Any] = None) -> None:
        """
        添加步骤日志
        
        Args:
            step_id: 步骤ID
            step_name: 步骤名称
            status: 状态（started, completed, failed）
            message: 消息
            details: 详细信息
        """
        log = {
            'step_id': step_id,
            'step_name': step_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'details': details
        }
        self.step_logs.append(log)
    
    def complete(self, total_images: int, processed_images: int, 
                success_images: int, failed_images: int) -> None:
        """
        标记执行为已完成
        
        Args:
            total_images: 总图像数
            processed_images: 已处理图像数
            success_images: 成功处理图像数
            failed_images: 处理失败图像数
        """
        self.end_time = datetime.now().isoformat()
        self.status = "completed"
        self.total_images = total_images
        self.processed_images = processed_images
        self.success_images = success_images
        self.failed_images = failed_images
    
    def fail(self, error_message: str) -> None:
        """
        标记执行为失败
        
        Args:
            error_message: 错误消息
        """
        self.end_time = datetime.now().isoformat()
        self.status = "failed"
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将执行记录转换为字典
        
        Returns:
            执行记录字典
        """
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'workflow_name': self.workflow_name,
            'source_type': self.source_type,
            'source_params': self.source_params,
            'output_directory': self.output_directory,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status,
            'error_message': self.error_message,
            'total_images': self.total_images,
            'processed_images': self.processed_images,
            'success_images': self.success_images,
            'failed_images': self.failed_images,
            'step_logs': self.step_logs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionRecord':
        """
        从字典创建执行记录
        
        Args:
            data: 执行记录字典
            
        Returns:
            执行记录对象
        """
        record = cls(
            workflow_id=data.get('workflow_id'),
            workflow_name=data.get('workflow_name'),
            source_type=data.get('source_type'),
            source_params=data.get('source_params', {}),
            output_directory=data.get('output_directory'),
            id=data.get('id')
        )
        
        record.start_time = data.get('start_time', record.start_time)
        record.end_time = data.get('end_time')
        record.status = data.get('status', 'running')
        record.error_message = data.get('error_message')
        
        record.total_images = data.get('total_images', 0)
        record.processed_images = data.get('processed_images', 0)
        record.success_images = data.get('success_images', 0)
        record.failed_images = data.get('failed_images', 0)
        
        record.step_logs = data.get('step_logs', [])
        
        return record
    
    def __repr__(self) -> str:
        return f"ExecutionRecord(id={self.id}, workflow='{self.workflow_name}', status={self.status})"


class ExecutionHistoryManager:
    """
    执行历史管理器，负责执行记录的存储和加载
    """
    def __init__(self):
        """
        初始化执行历史管理器
        """
        self.history_dir = os.path.join(config_manager.config_dir, 'history')
        os.makedirs(self.history_dir, exist_ok=True)
        
        self._records: Dict[str, ExecutionRecord] = {}
        self._load_records()
    
    def _load_records(self) -> None:
        """
        加载所有保存的执行记录
        """
        for filename in os.listdir(self.history_dir):
            if filename.endswith('.json'):
                try:
                    record_path = os.path.join(self.history_dir, filename)
                    with open(record_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    record = ExecutionRecord.from_dict(data)
                    self._records[record.id] = record
                except Exception as e:
                    logging.error(f"加载执行记录 {filename} 失败: {e}")
    
    def get_record(self, record_id: str) -> Optional[ExecutionRecord]:
        """
        获取执行记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            执行记录对象或None
        """
        return self._records.get(record_id)
    
    def get_all_records(self) -> List[ExecutionRecord]:
        """
        获取所有执行记录
        
        Returns:
            执行记录列表
        """
        # 按开始时间排序，最新的在前
        return sorted(
            self._records.values(),
            key=lambda r: r.start_time if r.start_time else "",
            reverse=True
        )
    
    def create_record(self, workflow_id: str = None, workflow_name: str = None,
                    source_type: str = None, source_params: Dict[str, Any] = None,
                    output_directory: str = None) -> ExecutionRecord:
        """
        创建新的执行记录
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            source_type: 图像来源类型
            source_params: 图像来源参数
            output_directory: 输出目录
            
        Returns:
            新的执行记录对象
        """
        record = ExecutionRecord(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            source_type=source_type,
            source_params=source_params,
            output_directory=output_directory
        )
        
        # 保存到内存
        self._records[record.id] = record
        
        # 保存到文件
        self.save_record(record)
        
        return record
    
    def save_record(self, record: ExecutionRecord) -> bool:
        """
        保存执行记录
        
        Args:
            record: 执行记录对象
            
        Returns:
            是否成功保存
        """
        try:
            # 保存到内存
            self._records[record.id] = record
            
            # 保存到文件
            record_path = os.path.join(self.history_dir, f"{record.id}.json")
            with open(record_path, 'w', encoding='utf-8') as f:
                json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logging.error(f"保存执行记录 {record.id} 失败: {e}")
            return False
    
    def delete_record(self, record_id: str) -> bool:
        """
        删除执行记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否成功删除
        """
        if record_id not in self._records:
            return False
        
        try:
            # 从内存中删除
            del self._records[record_id]
            
            # 从文件中删除
            record_path = os.path.join(self.history_dir, f"{record_id}.json")
            if os.path.exists(record_path):
                os.remove(record_path)
            
            return True
        except Exception as e:
            logging.error(f"删除执行记录 {record_id} 失败: {e}")
            return False
    
    def clear_records(self, days: int = None) -> int:
        """
        清理执行记录
        
        Args:
            days: 保留最近几天的记录，如果为None则清理所有记录
            
        Returns:
            清理的记录数量
        """
        if days is None:
            # 清理所有记录
            count = len(self._records)
            self._records.clear()
            
            for filename in os.listdir(self.history_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.history_dir, filename))
            
            return count
        else:
            # 清理特定天数之前的记录
            cutoff = datetime.now().timestamp() - days * 24 * 60 * 60
            to_delete = []
            
            for record_id, record in self._records.items():
                try:
                    record_time = datetime.fromisoformat(record.start_time).timestamp()
                    if record_time < cutoff:
                        to_delete.append(record_id)
                except (ValueError, TypeError):
                    # 如果时间格式有问题，默认保留
                    pass
            
            # 删除记录
            for record_id in to_delete:
                self.delete_record(record_id)
            
            return len(to_delete)


# 创建全局实例
history_manager = ExecutionHistoryManager()
