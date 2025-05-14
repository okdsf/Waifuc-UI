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
    
    @staticmethod
    def save_workflow(workflow_data: Dict) -> None: # 这个方法已存在，可以用于整体保存
        """保存工作流数据"""
        workflow = workflow_manager.get_workflow(workflow_data["id"])
        if not workflow:
            raise WorkflowError("工作流不存在")
        workflow.name = workflow_data["name"]
        workflow.description = workflow_data["description"]
        # 从字典列表重新构建步骤对象列表
        workflow.steps = [WorkflowStep.from_dict(step_dict) for step_dict in workflow_data.get("steps", [])]
        workflow_manager.save_workflow(workflow)

    # === 新增 update_step 方法 开始 ===
    @staticmethod
    def update_step(workflow_id: str, step_index: int, new_action_name: str, new_params: Dict) -> Dict:
        """
        更新工作流中指定索引的步骤。

        Args:
            workflow_id: 工作流的ID。
            step_index: 要更新的步骤的0-based索引。
            new_action_name: 步骤的新动作名称。
            new_params: 步骤的新参数字典。

        Returns:
            更新后的完整工作流数据的字典。

        Raises:
            WorkflowError: 如果工作流或步骤索引无效。
        """
        workflow = workflow_manager.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowError(f"工作流 '{workflow_id}' 未找到，无法更新步骤。")

        if not (0 <= step_index < len(workflow.steps)):
            raise WorkflowError(f"步骤索引 {step_index} 无效。工作流 '{workflow_id}' 共有 {len(workflow.steps)} 个步骤。")

  
        # WorkflowStep 对象在 workflow.steps 中应该是 WorkflowStep 的实例
        step_to_update: WorkflowStep = workflow.steps[step_index]
        step_to_update.action_name = new_action_name
        step_to_update.params = new_params
        # WorkflowStep 内部没有 updated_at，但 Workflow 对象有，它会在 save_workflow 时更新

        # 保存整个更新后的 Workflow 对象
        workflow_manager.save_workflow(workflow) # workflow_manager.save_workflow 内部会处理 updated_at
        
        return workflow.to_dict()
