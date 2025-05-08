"""
工作流模块 - 定义和管理图像处理工作流
"""
import os
import json
import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

from .config_manager import config_manager


class WorkflowStep:
    """
    工作流步骤类，代表处理流程中的一个步骤
    """
    def __init__(self, action_name: str, params: Dict[str, Any] = None, id: str = None):
        """
        初始化工作流步骤
        
        Args:
            action_name: 操作名称
            params: 操作参数
            id: 步骤ID，如果不提供则自动生成
        """
        self.action_name = action_name
        self.params = params or {}
        self.id = id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将步骤转换为字典
        
        Returns:
            步骤字典
        """
        return {
            'id': self.id,
            'action_name': self.action_name,
            'params': self.params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        """
        从字典创建步骤
        
        Args:
            data: 步骤字典
            
        Returns:
            工作流步骤对象
        """
        return cls(
            action_name=data['action_name'],
            params=data.get('params', {}),
            id=data.get('id')
        )
    
    def __repr__(self) -> str:
        return f"WorkflowStep(id={self.id}, action={self.action_name}, params={self.params})"


class Workflow:
    """
    工作流类，代表一个完整的图像处理流程
    """
    def __init__(self, name: str, description: str = "", id: str = None):
        """
        初始化工作流
        
        Args:
            name: 工作流名称
            description: 工作流描述
            id: 工作流ID，如果不提供则自动生成
        """
        self.name = name
        self.description = description
        self.id = id or str(uuid.uuid4())
        self.steps: List[WorkflowStep] = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def add_step(self, step: WorkflowStep) -> str:
        """
        添加处理步骤
        
        Args:
            step: 工作流步骤
            
        Returns:
            步骤ID
        """
        self.steps.append(step)
        self.updated_at = datetime.now().isoformat()
        return step.id
    
    def insert_step(self, index: int, step: WorkflowStep) -> str:
        """
        在指定位置插入处理步骤
        
        Args:
            index: 插入位置
            step: 工作流步骤
            
        Returns:
            步骤ID
        """
        self.steps.insert(index, step)
        self.updated_at = datetime.now().isoformat()
        return step.id
    
    def remove_step(self, step_id: str) -> bool:
        """
        移除处理步骤
        
        Args:
            step_id: 步骤ID
            
        Returns:
            是否成功移除
        """
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                self.steps.pop(i)
                self.updated_at = datetime.now().isoformat()
                return True
        return False
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """
        获取处理步骤
        
        Args:
            step_id: 步骤ID
            
        Returns:
            工作流步骤或None
        """
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def update_step(self, step_id: str, action_name: str = None, params: Dict[str, Any] = None) -> bool:
        """
        更新处理步骤
        
        Args:
            step_id: 步骤ID
            action_name: 操作名称，如果不提供则保持不变
            params: 操作参数，如果不提供则保持不变
            
        Returns:
            是否成功更新
        """
        step = self.get_step(step_id)
        if step is None:
            return False
        
        if action_name is not None:
            step.action_name = action_name
        
        if params is not None:
            step.params = params
        
        self.updated_at = datetime.now().isoformat()
        return True
    
    def move_step(self, step_id: str, new_index: int) -> bool:
        """
        移动处理步骤
        
        Args:
            step_id: 步骤ID
            new_index: 新位置
            
        Returns:
            是否成功移动
        """
        old_index = None
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                old_index = i
                break
        
        if old_index is None:
            return False
        
        if new_index < 0:
            new_index = 0
        elif new_index >= len(self.steps):
            new_index = len(self.steps) - 1
        
        if old_index == new_index:
            return True
        
        step = self.steps.pop(old_index)
        self.steps.insert(new_index, step)
        self.updated_at = datetime.now().isoformat()
        return True
    
    def clone(self, new_name: str = None) -> 'Workflow':
        """
        克隆工作流
        
        Args:
            new_name: 新工作流名称，如果不提供则使用原名称加 "的副本"
            
        Returns:
            新的工作流对象
        """
        if new_name is None:
            new_name = f"{self.name} 的副本"
        
        new_workflow = Workflow(new_name, self.description)
        
        for step in self.steps:
            new_step = WorkflowStep(step.action_name, step.params.copy())
            new_workflow.add_step(new_step)
        
        return new_workflow
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将工作流转换为字典
        
        Returns:
            工作流字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'steps': [step.to_dict() for step in self.steps],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """
        从字典创建工作流
        
        Args:
            data: 工作流字典
            
        Returns:
            工作流对象
        """
        workflow = cls(
            name=data['name'],
            description=data.get('description', ''),
            id=data.get('id')
        )
        
        workflow.created_at = data.get('created_at', workflow.created_at)
        workflow.updated_at = data.get('updated_at', workflow.updated_at)
        
        for step_data in data.get('steps', []):
            step = WorkflowStep.from_dict(step_data)
            workflow.add_step(step)
        
        return workflow
    
    def __repr__(self) -> str:
        return f"Workflow(id={self.id}, name='{self.name}', steps={len(self.steps)})"


class WorkflowManager:
    """
    工作流管理器，负责工作流的存储和加载
    """
    def __init__(self):
        """
        初始化工作流管理器
        """
        self.workflows_dir = os.path.join(config_manager.config_dir, 'workflows')
        os.makedirs(self.workflows_dir, exist_ok=True)
        
        self._workflows: Dict[str, Workflow] = {}
        self._load_workflows()
    
    def _load_workflows(self) -> None:
        """
        加载所有保存的工作流
        """
        for filename in os.listdir(self.workflows_dir):
            if filename.endswith('.json'):
                try:
                    workflow_path = os.path.join(self.workflows_dir, filename)
                    with open(workflow_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    workflow = Workflow.from_dict(data)
                    self._workflows[workflow.id] = workflow
                except Exception as e:
                    logging.error(f"加载工作流 {filename} 失败: {e}")
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        获取工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流对象或None
        """
        return self._workflows.get(workflow_id)
    
    def get_all_workflows(self) -> List[Workflow]:
        """
        获取所有工作流
        
        Returns:
            工作流列表
        """
        return list(self._workflows.values())
    
    def save_workflow(self, workflow: Workflow) -> bool:
        """
        保存工作流
        
        Args:
            workflow: 工作流对象
            
        Returns:
            是否成功保存
        """
        try:
            # 更新时间戳
            workflow.updated_at = datetime.now().isoformat()
            
            # 保存到内存
            self._workflows[workflow.id] = workflow
            
            # 保存到文件
            workflow_path = os.path.join(self.workflows_dir, f"{workflow.id}.json")
            with open(workflow_path, 'w', encoding='utf-8') as f:
                json.dump(workflow.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 添加到最近使用
            config_manager.add_recent_workflow(workflow.id)
            
            return True
        except Exception as e:
            logging.error(f"保存工作流 {workflow.name} 失败: {e}")
            return False
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """
        删除工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            是否成功删除
        """
        if workflow_id not in self._workflows:
            return False
        
        try:
            # 从内存中删除
            del self._workflows[workflow_id]
            
            # 从文件中删除
            workflow_path = os.path.join(self.workflows_dir, f"{workflow_id}.json")
            if os.path.exists(workflow_path):
                os.remove(workflow_path)
            
            # 从最近使用中删除
            recent = config_manager.get('recent_workflows', [])
            if workflow_id in recent:
                recent.remove(workflow_id)
                config_manager.set('recent_workflows', recent)
            
            return True
        except Exception as e:
            logging.error(f"删除工作流 {workflow_id} 失败: {e}")
            return False
    
    def create_workflow(self, name: str, description: str = "") -> Workflow:
        """
        创建新工作流
        
        Args:
            name: 工作流名称
            description: 工作流描述
            
        Returns:
            新的工作流对象
        """
        workflow = Workflow(name, description)
        self.save_workflow(workflow)
        return workflow


# 创建全局实例
workflow_manager = WorkflowManager()
