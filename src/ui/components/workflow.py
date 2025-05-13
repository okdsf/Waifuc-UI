"""
工作流设计组件：实现创建、编辑、查看工作流，添加/删除/排序步骤。
"""
import gradio as gr
import json
import logging
import pandas as pd
from typing import Optional, Dict, List, Union
from src.services.workflow_service import WorkflowService, WorkflowError
from src.tools.actions.action_registry import registry as action_registry

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def render():
    """
    渲染工作流设计界面，包含创建、加载、步骤管理功能。
    """

    def _format_steps_for_dataframe(steps_list_of_dicts: List[Dict]) -> List[List[Union[int, str]]]:
        """
        将步骤字典列表格式化为 gr.Dataframe 所需的列表的列表，
        并在第一列添加从1开始的行号。
        """
        formatted_steps = []
        for i, step_data in enumerate(steps_list_of_dicts):
            formatted_steps.append([
                i + 1,  # 行号 (1-based)
                step_data.get("action_name", "N/A"), # 操作名称
                json.dumps(step_data.get("params", {}), ensure_ascii=False) # 参数
            ])
        return formatted_steps

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
            # 参数输入区域（动态生成）
            with gr.Column() as params_container:
                pass  # 占位，动态渲染将在这里进行

            add_step_btn = gr.Button("添加步骤")
            steps_table = gr.Dataframe(
                value=[],
                headers=["行号", "操作", "参数"],  
                datatype=["number", "str", "str"], 
                interactive=True
            )
            selected_step_display = gr.Textbox(label="当前选中步骤", value="未选择任何步骤", interactive=False) # <--- 新增
            with gr.Row():
                delete_step_btn = gr.Button("删除选中步骤")
                move_up_btn = gr.Button("上移")
                move_down_btn = gr.Button("下移")
                selected_step_index = gr.State(None)

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

        # 动态生成参数输入字段
        @gr.render(inputs=action_dropdown)
        def render_params_inputs(action_name):
            if not action_name or action_name == "无操作可用":
                return
            params = action_registry.get_action_params(action_name)
            logger.info(f"Generating inputs for action: {action_name}, params: {params}")
            with gr.Column():
                components = []
                for param_name, (default_value, param_type) in params.items():
                    # 生成提示信息
                    info = None
                    if param_type == Optional[int]:
                        info = "请输入整数或留空（使用 None）"
                        component = gr.Number(
                            label=param_name,
                            value=default_value,
                            precision=0,
                            info=info
                        )
                    elif param_type == Optional[float]:
                        info = "请输入浮点数或留空（使用 None）"
                        component = gr.Number(
                            label=param_name,
                            value=default_value,
                            info=info
                        )
                    elif param_type in (Optional[Dict], Optional[List]):
                        info = "请输入 JSON 格式（例如 {\"key\": \"value\"}）或留空（使用 None）"
                        component = gr.Textbox(
                            label=param_name,
                            value=json.dumps(default_value, ensure_ascii=False) if default_value is not None else None,
                            lines=5,
                            placeholder="请输入 JSON 格式",
                            info=info
                        )
                    elif param_type == Optional[str]:
                        info = "请输入文本或留空（使用 None）"
                        component = gr.Textbox(
                            label=param_name,
                            value=default_value,
                            info=info
                        )
                    elif isinstance(default_value, bool):
                        info = "选择是否启用"
                        component = gr.Checkbox(
                            label=param_name,
                            value=default_value,
                            info=info
                        )
                    elif isinstance(default_value, int):
                        info = "请输入整数"
                        component = gr.Number(
                            label=param_name,
                            value=default_value,
                            precision=0,
                            info=info
                        )
                    elif isinstance(default_value, float):
                        info = "请输入浮点数"
                        component = gr.Number(
                            label=param_name,
                            value=default_value,
                            info=info
                        )
                    elif isinstance(default_value, (dict, list)):
                        info = "请输入 JSON 格式（例如 {\"key\": \"value\"} 或 [1, 2, 3]）"
                        component = gr.Textbox(
                            label=param_name,
                            value=json.dumps(default_value, ensure_ascii=False),
                            lines=5,
                            placeholder="请输入 JSON 格式",
                            info=info
                        )
                    else:
                        info = "请输入文本" if default_value is not None else "请输入文本（必填）"
                        component = gr.Textbox(
                            label=param_name,
                            value=str(default_value) if default_value is not None else "",
                            placeholder="必填" if default_value is None else "",
                            info=info
                        )
                    logger.info(f"Rendered component for {param_name}: type={param_type}, default={default_value}")
                    components.append(component)
                # 事件绑定
                add_step_btn.click(
                    fn=add_step,
                    inputs=[workflow_id, action_dropdown] + components,
                    outputs=[workflow_output, steps_table, workflow_output]
                )
            return components

        # 创建工作流
        def create_workflow(name, desc):
            try:
                if not name.strip():
                    raise WorkflowError("工作流名称不能为空")
                workflow_data = WorkflowService.create_workflow(name, desc)
                logger.info(f"Created workflow: {workflow_data['id']}")
                return workflow_data["id"], json.dumps(workflow_data, indent=2, ensure_ascii=False), [], ""
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
                WorkflowService.save_workflow(workflow_data)
                logger.info(f"Saved workflow: {workflow_id}")
                return json.dumps(workflow_data, indent=2, ensure_ascii=False)
            except WorkflowError as e:
                logger.error(f"Save workflow error: {str(e)}")
                return str(e)

        save_btn.click(
            fn=save_workflow,
            inputs=[workflow_id, workflow_name, workflow_desc],
            outputs=workflow_output
        )

        def handle_table_select(evt: gr.SelectData, current_steps_df_data: pd.DataFrame):
            print(f"DEBUG: handle_table_select - Event: evt.index={evt.index}, evt.value={evt.value}, evt.selected={evt.selected}")
            if current_steps_df_data is None:
                print("DEBUG: handle_table_select - current_steps_df_data is None!")
                return None, "表格数据错误"
            print(f"DEBUG: handle_table_select - DataFrame: empty={current_steps_df_data.empty}, len={len(current_steps_df_data)}")

            if evt.index is None:
                print("DEBUG: handle_table_select - evt.index is None. Returning None for index.")
                return None, "未选择任何步骤"

            selected_row_index = evt.index[0]
            print(f"DEBUG: handle_table_select - selected_row_index from evt.index[0] = {selected_row_index}")

            if 0 <= selected_row_index < len(current_steps_df_data):
                try:
                    actual_row_number = current_steps_df_data.iloc[selected_row_index, 0]
                    action_name = current_steps_df_data.iloc[selected_row_index, 1]
                    print(f"DEBUG: handle_table_select - Success. Returning index: {selected_row_index}")
                    return selected_row_index, f"已选择第 {actual_row_number} 行: {action_name}"
                except IndexError as e:
                    print(f"DEBUG: handle_table_select - IndexError: {e}. Returning None for index.")
                    return None, "读取步骤数据时发生错误"

            print(f"DEBUG: handle_table_select - Index {selected_row_index} invalid for table len {len(current_steps_df_data)}. Returning None for index.")
            return None, "选择无效或表格为空"
        
        steps_table.select(
                fn=handle_table_select,
                inputs=[steps_table],
                outputs=[selected_step_index, selected_step_display],
                show_progress="hidden"
            )


        # 添加步骤，处理动态参数
        def add_step(workflow_id, action_name, *param_values):
            try:
                if not workflow_id:
                    raise WorkflowError("请先创建或加载工作流")
                if action_name == "无操作可用":
                    raise WorkflowError("请选择有效的操作")
                params = action_registry.get_action_params(action_name)
                param_names = list(params.keys())
                param_dict = {}
                param_value_index = 0
                for param_name in param_names:
                    default_value, param_type = params[param_name]
                    # 处理 Optional 类型，允许空输入为 None
                    if param_value_index >= len(param_values):
                        if param_type in (Optional[int], Optional[float], Optional[Dict], Optional[List], Optional[str]):
                            param_dict[param_name] = None
                            logger.info(f"Assigned None to {param_name} (empty input, type={param_type})")
                            continue
                        raise ValueError(f"参数 {param_name} 缺少值")
                    value = param_values[param_value_index]
                    # 空输入处理
                    if value is None or value == "":
                        if param_type in (Optional[int], Optional[float], Optional[Dict], Optional[List], Optional[str]):
                            param_dict[param_name] = None
                            logger.info(f"Assigned None to {param_name} (empty input, type={param_type})")
                        else:
                            raise ValueError(f"参数 {param_name} 为必填项")
                    else:
                        # 类型解析
                        if param_type == Optional[int] or isinstance(default_value, int):
                            try:
                                param_dict[param_name] = int(value)
                            except (ValueError, TypeError):
                                raise ValueError(f"参数 {param_name} 应为整数")
                        elif param_type == Optional[float] or isinstance(default_value, float):
                            try:
                                param_dict[param_name] = float(value)
                            except (ValueError, TypeError):
                                raise ValueError(f"参数 {param_name} 应为浮点数")
                        elif param_type in (Optional[Dict], Optional[List]) or isinstance(default_value, (dict, list)):
                            try:
                                param_dict[param_name] = json.loads(value)
                            except json.JSONDecodeError:
                                raise ValueError(f"参数 {param_name} 的 JSON 格式无效")
                        else:
                            param_dict[param_name] = value
                        logger.info(f"Parsed {param_name}: input={value}, type={param_type}, value={param_dict[param_name]}")
                    param_value_index += 1
                logger.info(f"Adding step: {action_name}, params: {param_dict}")
                workflow_data = WorkflowService.add_step(workflow_id, action_name, param_dict)
                steps_for_df = _format_steps_for_dataframe(workflow_data.get("steps", [])) # <--- MODIFIED LINE (使用辅助函数)
                logger.info(f"Added step: {action_name} to workflow: {workflow_id}")
                return json.dumps(workflow_data, indent=2, ensure_ascii=False),  steps_for_df, "已添加步骤"
            except (WorkflowError, ValueError) as e:
                logger.error(f"Add step error: {str(e)}")
                return str(e), gr.update(), str(e)

    

        def delete_step(workflow_id_val, current_0_based_selected_index):
            # (workflow_output_update, steps_table_update, new_selected_index_update, selected_display_update)
            if workflow_id_val is None:
                return "请先创建或加载工作流", gr.update(), None, "未选择任何步骤"
            if current_0_based_selected_index is None:
                return "请先选择一个步骤进行删除", gr.update(), None, "未选择任何步骤"

            try:
                workflow_data = WorkflowService.get_workflow(workflow_id_val)
                if not workflow_data or "steps" not in workflow_data:
                    return "工作流数据错误", gr.update(), None, "未选择任何步骤"

                steps_list = workflow_data.get("steps", [])
                if not (0 <= current_0_based_selected_index < len(steps_list)):
                    return "选择的步骤索引无效，无法删除", gr.update(), None, "未选择任何步骤"

                deleted_step_info = steps_list.pop(current_0_based_selected_index) # 从原始数据中删除
                logger.info(f"Deleted step: {deleted_step_info.get('action_name')} from workflow: {workflow_id_val}")

                WorkflowService.save_workflow(workflow_data)
                new_steps_for_df = _format_steps_for_dataframe(steps_list) # 重新生成显示数据

                # 删除后清除选中状态
                new_selected_index_after_delete = None
                new_display_text_after_delete = "未选择任何步骤 (前步骤已删除)"

                return json.dumps(workflow_data, indent=2, ensure_ascii=False), new_steps_for_df, new_selected_index_after_delete, new_display_text_after_delete
            except WorkflowError as e:
                logger.error(f"Delete step WorkflowError: {str(e)}")
                return str(e), gr.update(), current_0_based_selected_index, gr.update() # 保留旧的选中，让用户知道哪里出错了
            except Exception as e:
                logger.exception(f"Delete step unexpected error: {str(e)}")
                return f"删除步骤时发生意外错误: {str(e)}", gr.update(), current_0_based_selected_index, gr.update()

        delete_step_btn.click(
            fn=delete_step,
            inputs=[workflow_id, selected_step_index], # 使用 .select 更新的 selected_step_index
            outputs=[workflow_output, steps_table, selected_step_index, selected_step_display] # 确保更新所有相关组件
        )

        def move_step(workflow_id_val, current_0_based_selected_index, direction):
            """
            移动步骤，并返回更新后的工作流详情、步骤表格数据、新的0-based选中索引和选中显示文本。
            """
            # 初始返回状态，以防出错或无法操作
            # (workflow_output_update, steps_table_update, new_selected_index_update, selected_display_update)
            error_return = (gr.update(), gr.update(), current_0_based_selected_index, gr.update())

            if workflow_id_val is None:
                logger.warning("Move step: No workflow loaded.")
                return "请先创建或加载工作流", gr.update(), current_0_based_selected_index, "未选择任何步骤" # 特定错误信息给 workflow_output

            if current_0_based_selected_index is None:
                logger.warning("Move step: No step selected.")
                # 返回一个提示给 workflow_output 或者直接不更新，保持 selected_step_display 的内容
                return "请先选择一个步骤进行移动", gr.update(), None, "未选择任何步骤"

            try:
                workflow_data = WorkflowService.get_workflow(workflow_id_val)
                if not workflow_data or "steps" not in workflow_data:
                    logger.error(f"Move step: Workflow data error for ID {workflow_id_val}.")
                    return "工作流数据错误", gr.update(), None, "未选择任何步骤"

                steps_list = workflow_data.get("steps", []) # 这是你的原始字典列表
                num_steps = len(steps_list)

                # 检查索引有效性
                if not (0 <= current_0_based_selected_index < num_steps):
                    logger.warning(f"Move step: Invalid selected index {current_0_based_selected_index} for {num_steps} steps.")
                    return "选择的步骤索引无效", gr.update(), None, "未选择任何步骤" # 或者 gr.update() for selected_step_index

                new_0_based_selected_index = current_0_based_selected_index # 预设为不变
                moved = False

                if direction == "up":
                    if current_0_based_selected_index > 0:
                        # 交换原始数据列表中的元素
                        steps_list[current_0_based_selected_index], steps_list[current_0_based_selected_index - 1] = \
                            steps_list[current_0_based_selected_index - 1], steps_list[current_0_based_selected_index]
                        new_0_based_selected_index = current_0_based_selected_index - 1
                        moved = True
                        logger.info(f"Moved step up. Old index: {current_0_based_selected_index}, New index: {new_0_based_selected_index}")
                elif direction == "down":
                    if current_0_based_selected_index < num_steps - 1:
                        # 交换原始数据列表中的元素
                        steps_list[current_0_based_selected_index], steps_list[current_0_based_selected_index + 1] = \
                            steps_list[current_0_based_selected_index + 1], steps_list[current_0_based_selected_index]
                        new_0_based_selected_index = current_0_based_selected_index + 1
                        moved = True
                        logger.info(f"Moved step down. Old index: {current_0_based_selected_index}, New index: {new_0_based_selected_index}")

                if moved:
                    # workflow_data["steps"] 已经被上面的交换操作通过引用修改了
                    WorkflowService.save_workflow(workflow_data) # 保存更新后的原始数据

                    # 从更新后的原始数据重新生成用于DataFrame显示的数据
                    new_steps_for_df = _format_steps_for_dataframe(steps_list)

                    # 更新选中行的显示信息
                    action_name_after_move = "N/A"
                    displayed_row_num_after_move = ""
                    if 0 <= new_0_based_selected_index < len(new_steps_for_df):
                        # new_steps_for_df 是 [[行号, 操作, 参数], ...]
                        action_name_after_move = new_steps_for_df[new_0_based_selected_index][1] # 操作名称在索引1
                        displayed_row_num_after_move = new_steps_for_df[new_0_based_selected_index][0] # 显示的行号在索引0

                    new_display_text = f"已选择第 {displayed_row_num_after_move} 行: {action_name_after_move}" if moved else "未选择任何步骤"

                    logger.info(f"Move successful. New selected display: '{new_display_text}'")
                    return json.dumps(workflow_data, indent=2, ensure_ascii=False), new_steps_for_df, new_0_based_selected_index, new_display_text
                else:
                    logger.info("Move step: No move performed (already at boundary or invalid direction).")
                    # 未移动，返回当前状态或特定提示，保持选中索引不变
                    # 当前的 workflow_output 内容可能不需要更新，除非你想显示 "无法移动" 的消息
                    # 如果不更新 workflow_output，可以使用 gr.update()
                    return gr.update(), gr.update(), current_0_based_selected_index, gr.update() # "无法移动（已在顶部/底部）"

            except WorkflowError as e:
                logger.error(f"Move step WorkflowError: {str(e)}")
                return str(e), gr.update(), current_0_based_selected_index, gr.update() # 错误信息给 workflow_output
            except Exception as e:
                logger.exception(f"Move step unexpected error: {str(e)}") # 使用 .exception() 记录完整堆栈
                return f"移动步骤时发生意外错误: {str(e)}", gr.update(), current_0_based_selected_index, gr.update()

        move_up_btn.click(
            fn=move_step,
            inputs=[workflow_id, selected_step_index, gr.State("up")], 
            outputs=[workflow_output, steps_table, selected_step_index, selected_step_display] 
        )
        move_down_btn.click(
            fn=move_step,
            inputs=[workflow_id, selected_step_index, gr.State("down")],
            outputs=[workflow_output, steps_table, selected_step_index, selected_step_display]
        )
       
        def on_workflow_select(workflow_id):
            try:
                if not workflow_id:
                    return None, "请选择工作流", [], "", ""
                workflow_data = WorkflowService.get_workflow(workflow_id)
                if not workflow_data:
                    return None, "工作流不存在", [], "", ""
                steps_for_df = _format_steps_for_dataframe(workflow_data.get("steps", [])) # <--- MODIFIED LINE (使用辅助函数)
                logger.info(f"Loaded workflow: {workflow_id}")
                return (
                    workflow_id,
                    json.dumps(workflow_data, indent=2, ensure_ascii=False),
                    steps_for_df,
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