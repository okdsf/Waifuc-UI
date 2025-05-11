"""
工作流服务：包装 src/data/workflow_manager.py 和 src/data/workflow.py，
提供创建、获取、添加步骤等功能，返回字典数据，供 Gradio 前端使用。
"""
from src.data import workflow_manager
from src.data.workflow import Workflow, WorkflowStep
from typing import Dict, List, Optional

class WorkflowError(Exception):
    pass

class WorkflowService:
    @staticmethod
    def create_workflow(name: str, description: str = "") -> Dict:
        """创建工作流，返回字典格式的工作流数据"""
        workflow = workflow_manager.create_workflow(name, description)
        if not workflow:
            raise WorkflowError("创建工作流失败")
        return workflow.to_dict()

    @staticmethod
    def get_workflow(workflow_id: str) -> Optional[Dict]:
        """获取指定工作流，返回字典数据或 None"""
        workflow = workflow_manager.get_workflow(workflow_id)
        return workflow.to_dict() if workflow else None

    @staticmethod
    def get_all_workflows() -> List[Dict]:
        """获取所有工作流，返回字典列表"""
        workflows = workflow_manager.get_all_workflows()
        return [w.to_dict() for w in workflows]

    @staticmethod
    def add_step(workflow_id: str, action_name: str, params: Dict) -> Dict:
        """向工作流添加步骤，保存并返回更新后的工作流数据"""
        workflow = workflow_manager.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowError("工作流不存在")
        step = WorkflowStep(action_name, params)
        workflow.add_step(step)
        workflow_manager.save_workflow(workflow)
        return workflow.to_dict()

    @staticmethod
    def save_workflow(workflow_data: Dict) -> None:
        """保存工作流数据"""
        workflow = workflow_manager.get_workflow(workflow_data["id"])
        if not workflow:
            raise WorkflowError("工作流不存在")
        workflow.name = workflow_data["name"]
        workflow.description = workflow_data["description"]
        workflow.steps = [WorkflowStep(step["action_name"], step["params"]) for step in workflow_data.get("steps", [])]
        workflow_manager.save_workflow(workflow)

    @staticmethod
    def import_workflow(workflow_data: Dict) -> Dict:
        """导入工作流数据，返回新创建的工作流数据"""
        workflow = Workflow(
            name=workflow_data.get("name", ""),
            description=workflow_data.get("description", ""),
            steps=[WorkflowStep(step["action_name"], step["params"]) for step in workflow_data.get("steps", [])]
        )
        workflow.id = workflow_data.get("id", workflow_manager.generate_workflow_id())
        workflow_manager.save_workflow(workflow)
        return workflow.to_dict()