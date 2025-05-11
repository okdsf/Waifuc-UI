"""
工作流设计组件：实现创建、编辑、查看工作流，添加/删除/排序步骤，导入/导出工作流。
对应 PyQt5 的 workflow_designer.py。
"""
import gradio as gr
import json
import logging
from src.services.workflow_service import WorkflowService, WorkflowError
from src.tools.actions.action_registry import registry as action_registry

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render():
    """
    渲染工作流设计界面，包含创建、加载、步骤管理和导入/导出功能。
    """
    with gr.Column():
        # 工作流信息
        workflow_id = gr.State(None)
        workflow_name = gr.Textbox(label="工作流名称", placeholder="输入工作流名称")
        workflow_desc = gr.Textbox(label="描述", placeholder="输入工作流描述")
        with gr.Row():
            create_btn = gr.Button("创建工作流")
            save_btn = gr.Button("保存工作流")
            load_dropdown = gr.Dropdown(
                choices=[(w["name"], w["id"]) for w in WorkflowService.get_all_workflows()] or [("无工作流", "")],
                label="加载工作流"
            )
        workflow_output = gr.Textbox(label="工作流详情", interactive=False, lines=10)

        # 步骤管理
        with gr.Group():
            gr.Markdown("### 步骤管理")
            with gr.Row():
                categories = action_registry.get_categories() or ["默认类别"]
                category_state = gr.State(categories[0])
                category_dropdown = gr.Dropdown(
                    choices=categories,
                    label="操作类别",
                    value=categories[0]
                )
                action_dropdown = gr.Dropdown(
                    choices=action_registry.get_actions_in_category(categories[0]) or ["无操作可用"],
                    label="选择操作"
                )
                params_json = gr.Textbox(label="参数 (JSON 格式)", placeholder='{"key": "value"}')
                add_step_btn = gr.Button("添加步骤")
            steps_table = gr.Dataframe(
                value=[],
                headers=["操作", "参数"],
                datatype=["str", "str"],
                interactive=True
            )
            with gr.Row():
                select_step_btn = gr.Button("选择步骤")
                delete_step_btn = gr.Button("删除选中步骤")
                move_up_btn = gr.Button("上移")
                move_down_btn = gr.Button("下移")
                selected_step_index = gr.State(None)

        # 导入/导出
        with gr.Group():
            gr.Markdown("### 导入/导出")
            import_file = gr.File(label="导入工作流 JSON")
            export_btn = gr.Button("导出工作流")

        # 动态更新动作下拉框
        def update_action_dropdown(category):
            logger.info(f"Updating actions for category: {category}")
            actions = action_registry.get_actions_in_category(category) or ["无操作可用"]
            return gr.update(choices=actions, value=actions[0] if actions else "无操作可用"), category

        category_dropdown.change(
            fn=update_action_dropdown,
            inputs=category_dropdown,
            outputs=[action_dropdown, category_state]
        )

        # 创建工作流
        def create_workflow(name, desc):
            try:
                if not name.strip():
                    raise WorkflowError("工作流名称不能为空")
                workflow_data = WorkflowService.create_workflow(name, desc)
                logger.info(f"Created workflow: {workflow_data['id']}")
                return workflow_data["id"], json.dumps(workflow_data, indent=2), [], ""
            except WorkflowError as e:
                logger.error(f"Create workflow error: {str(e)}")
                return None, str(e), [], gr.update()

        create_btn.click(
            fn=create_workflow,
            inputs=[workflow_name, workflow_desc],
            outputs=[workflow_id, workflow_output, steps_table, workflow_name]
        )

        # 保存工作流
        def save_workflow(workflow_id, name, desc):
            try:
                if not workflow_id:
                    raise WorkflowError("请先创建或加载工作流")
                workflow_data = WorkflowService.get_workflow(workflow_id)
                if not workflow_data:
                    raise WorkflowError("工作流不存在")
                workflow_data["name"] = name
                workflow_data["description"] = desc
                WorkflowService.save_workflow(workflow_data)  # 调用服务层保存
                logger.info(f"Saved workflow: {workflow_id}")
                return json.dumps(workflow_data, indent=2)
            except WorkflowError as e:
                logger.error(f"Save workflow error: {str(e)}")
                return str(e)

        save_btn.click(
            fn=save_workflow,
            inputs=[workflow_id, workflow_name, workflow_desc],
            outputs=workflow_output
        )

        # 修复：选择步骤
        def select_step(steps_table_value):
            try:
                if steps_table_value.empty:  # 使用 .empty 检查 DataFrame
                    logger.info("No steps available to select")
                    return None, "请先添加步骤"
                logger.info("Selected first step")
                return 0, "已选择第一个步骤"
            except Exception as e:
                logger.error(f"Select step error: {str(e)}")
                return None, str(e)

        select_step_btn.click(
            fn=select_step,
            inputs=steps_table,
            outputs=[selected_step_index, workflow_output]
        )

        # 添加步骤
        def add_step(workflow_id, action_name, params_json):
            try:
                if not workflow_id:
                    raise WorkflowError("请先创建或加载工作流")
                params = json.loads(params_json) if params_json else {}
                workflow_data = WorkflowService.add_step(workflow_id, action_name, params)
                steps = [[step["action_name"], json.dumps(step["params"])] for step in workflow_data.get("steps", [])]
                logger.info(f"Added step: {action_name} to workflow: {workflow_id}")
                return json.dumps(workflow_data, indent=2), steps
            except (WorkflowError, json.JSONDecodeError) as e:
                logger.error(f"Add step error: {str(e)}")
                return str(e), gr.update()

        add_step_btn.click(
            fn=add_step,
            inputs=[workflow_id, action_dropdown, params_json],
            outputs=[workflow_output, steps_table]
        )

        # 删除步骤
        def delete_step(workflow_id, selected_index):
            try:
                if not workflow_id:
                    raise WorkflowError("请先创建或加载工作流")
                if selected_index is None:
                    raise WorkflowError("请先选择步骤")
                workflow_data = WorkflowService.get_workflow(workflow_id)
                if not workflow_data.get("steps") or selected_index >= len(workflow_data.get("steps", [])):
                    raise WorkflowError("无效的步骤索引")
                deleted_step = workflow_data["steps"].pop(selected_index)
                WorkflowService.save_workflow(workflow_data)
                steps = [[step["action_name"], json.dumps(step["params"])] for step in workflow_data.get("steps", [])]
                logger.info(f"Deleted step: {deleted_step['action_name']} from workflow: {workflow_id}")
                return json.dumps(workflow_data, indent=2), steps, None
            except WorkflowError as e:
                logger.error(f"Delete step error: {str(e)}")
                return str(e), gr.update(), gr.update()

        delete_step_btn.click(
            fn=delete_step,
            inputs=[workflow_id, selected_step_index],
            outputs=[workflow_output, steps_table, selected_step_index]
        )

        # 移动步骤（上移/下移）
        def move_step(workflow_id, selected_index, direction):
            try:
                if not workflow_id:
                    raise WorkflowError("请先创建或加载工作流")
                if selected_index is None:
                    raise WorkflowError("请先选择步骤")
                workflow_data = WorkflowService.get_workflow(workflow_id)
                steps = workflow_data.get("steps", [])
                index = selected_index
                if direction == "up" and index > 0:
                    steps[index], steps[index - 1] = steps[index - 1], steps[index]
                    logger.info(f"Moved step up: index {index} in workflow: {workflow_id}")
                elif direction == "down" and index < len(steps) - 1:
                    steps[index], steps[index + 1] = steps[index + 1], steps[index]
                    logger.info(f"Moved step down: index {index} in workflow: {workflow_id}")
                else:
                    raise WorkflowError("无法移动步骤")
                WorkflowService.save_workflow(workflow_data)
                steps = [[step["action_name"], json.dumps(step["params"])] for step in steps]
                return json.dumps(workflow_data, indent=2), steps
            except WorkflowError as e:
                logger.error(f"Move step error: {str(e)}")
                return str(e), gr.update()

        move_up_btn.click(
            fn=move_step,
            inputs=[workflow_id, selected_step_index, gr.State("up")],
            outputs=[workflow_output, steps_table]
        )
        move_down_btn.click(
            fn=move_step,
            inputs=[workflow_id, selected_step_index, gr.State("down")],
            outputs=[workflow_output, steps_table]
        )

        # 加载工作流
        def on_workflow_select(workflow_id):
            try:
                if not workflow_id:
                    return None, "请选择工作流", [], "", ""
                workflow_data = WorkflowService.get_workflow(workflow_id)
                if not workflow_data:
                    return None, "工作流不存在", [], "", ""
                steps = [[step["action_name"], json.dumps(step["params"])] for step in workflow_data.get("steps", [])]
                logger.info(f"Loaded workflow: {workflow_id}")
                return (
                    workflow_id,
                    json.dumps(workflow_data, indent=2),
                    steps,
                    workflow_data.get("name", ""),
                    workflow_data.get("description", "")
                )
            except Exception as e:
                logger.error(f"Load workflow error: {str(e)}")
                return None, str(e), [], "", ""

        load_dropdown.change(
            fn=on_workflow_select,
            inputs=load_dropdown,
            outputs=[workflow_id, workflow_output, steps_table, workflow_name, workflow_desc]
        )

        # 导入工作流
        def import_workflow(file):
            try:
                if not file:
                    raise WorkflowError("请上传有效的 JSON 文件")
                with open(file.name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                workflow_data = WorkflowService.import_workflow(data)
                steps = [[step["action_name"], json.dumps(step["params"])] for step in workflow_data.get("steps", [])]
                logger.info(f"Imported workflow: {workflow_data['id']}")
                return (
                    workflow_data["id"],
                    json.dumps(workflow_data, indent=2),
                    steps,
                    workflow_data.get("name", ""),
                    workflow_data.get("description", "")
                )
            except Exception as e:
                logger.error(f"Import workflow error: {str(e)}")
                return None, str(e), [], "", ""

        import_file.change(
            fn=import_workflow,
            inputs=import_file,
            outputs=[workflow_id, workflow_output, steps_table, workflow_name, workflow_desc]
        )

        # 导出工作流
        def export_workflow(workflow_id):
            try:
                if not workflow_id:
                    raise WorkflowError("请先创建或加载工作流")
                workflow_data = WorkflowService.get_workflow(workflow_id)
                if not workflow_data:
                    raise WorkflowError("工作流不存在")
                logger.info(f"Exported workflow: {workflow_id}")
                return gr.File(value=json.dumps(workflow_data, indent=2), label="工作流 JSON")
            except WorkflowError as e:
                logger.error(f"Export workflow error: {str(e)}")
                return str(e)

        export_btn.click(
            fn=export_workflow,
            inputs=workflow_id,
            outputs=gr.File()
        )