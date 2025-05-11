"""
任务服务：包装 src/data/workflow_engine.py，提供任务执行功能，
通过信号桥接进度更新，返回任务 ID，供 Gradio 前端使用。
"""
from src.data import workflow_manager
from src.data.workflow_engine import workflow_engine
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict

class TaskError(Exception):
    pass

class TaskService(QObject):
    progress_updated = pyqtSignal(str, float, str)  # 进度更新信号：状态、进度、消息
    task_finished = pyqtSignal(bool, str)  # 任务完成信号：成功状态、消息

    @staticmethod
    def start_task(workflow_id: str, source_data: Dict, output_dir: str) -> str:
        """启动任务，返回任务 ID"""
        try:
            workflow = workflow_manager.get_workflow(workflow_id)
            if not workflow:
                raise TaskError("工作流不存在")
            source_type = source_data.get("type")
            source_params = source_data.get("params", {})
            if not source_type:
                raise TaskError("数据源类型不能为空")
            record = workflow_engine.execute_workflow(
                workflow, source_type, source_params, output_dir,
                lambda s, p, m: TaskService.progress_updated.emit(s, p, m)
            )
            return record.id
        except Exception as e:
            raise TaskError(f"启动任务失败: {str(e)}")