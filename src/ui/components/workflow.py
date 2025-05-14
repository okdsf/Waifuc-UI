"""
工作流设计组件：实现创建、编辑、查看工作流，添加/删除/排序步骤。
"""
import gradio as gr
import json
import logging
import pandas as pd
from typing import Optional, Dict, List, Union,get_origin, get_args
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
        edit_mode_active = gr.State(False)
        editing_step_index = gr.State(None) # 存储0-based索引
        temporary_editing_params = gr.State({}) # 存储待编辑步骤的参数（格式要适合UI组件）
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

            with gr.Row() as action_buttons_row: # 新的Row
             add_step_btn = gr.Button("添加步骤") # 保持原始按钮的意图，但放入Row
             cancel_edit_btn = gr.Button("取消编辑", visible=False) # 新增，初始隐藏
            
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
                edit_step_btn = gr.Button("编辑选中步骤")



        def handle_edit_mode_entry(workflow_id_val, selected_0_based_idx, registry_ref): # registry_ref 就是 action_registry
            logger.debug(f"Entering edit mode: workflow_id={workflow_id_val}, selected_idx={selected_0_based_idx}")

            # --- 初始校验 ---
            if workflow_id_val is None or selected_0_based_idx is None:
                gr.Warning("请先加载工作流并选择一个步骤进行编辑！")
                return (
                    gr.update(value=False), gr.update(value=None), gr.update(value={}),  # edit_mode_active, editing_step_index, temporary_editing_params
                    gr.update(), gr.update(),                                          # category_dropdown, action_dropdown (无变化)
                    gr.update(value="添加步骤", visible=True), gr.update(visible=False), # add_step_btn, cancel_edit_btn
                    gr.update(visible=True), gr.update(visible=True),                  # edit_step_btn, delete_step_btn (恢复原始可见性)
                    gr.update(visible=True), gr.update(visible=True),                  # move_up_btn, move_down_btn
                    gr.update(value="选择无效或未加载工作流"),                              # selected_step_display
                    gr.update(interactive=True)                                        # steps_table (保持可交互)
                )

            try:
                workflow_data = WorkflowService.get_workflow(workflow_id_val)
                if not workflow_data or "steps" not in workflow_data or \
                not (0 <= selected_0_based_idx < len(workflow_data["steps"])):
                    gr.Warning("选择的步骤无效或工作流数据错误。")
                    return (
                        gr.update(value=False), gr.update(value=None), gr.update(value={}),
                        gr.update(), gr.update(),
                        gr.update(value="添加步骤", visible=True), gr.update(visible=False),
                        gr.update(visible=True), gr.update(visible=True),
                        gr.update(visible=True), gr.update(visible=True),
                        gr.update(value="选择的步骤无效"),
                        gr.update(interactive=True)
                    )

                step_to_edit = workflow_data["steps"][selected_0_based_idx]
                action_name_to_edit = step_to_edit.get("action_name") # 在您的 _format_steps_for_dataframe 中是 "action_name"
                if not action_name_to_edit or action_name_to_edit == "N/A": # 更强的校验
                    gr.Error(f"要编辑的步骤没有有效的操作名称。")
                    return (
                        gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                        gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                        gr.update(), gr.update(value="步骤操作名称无效"), gr.update(interactive=True)
                    )
                params_to_edit_raw = step_to_edit.get("params", {})


                # 1. 获取操作的正确类别
                correct_category = registry_ref.get_category_for_action(action_name_to_edit)
                if correct_category is None:
                    error_msg = f"错误：无法为操作 '{action_name_to_edit}' 找到所属的类别。请检查Action Registry的配置。"
                    gr.Error(error_msg)
                    return ( # 明确返回13个更新
                        gr.update(), gr.update(), gr.update(),  # edit_mode states
                        gr.update(), gr.update(),              # dropdowns
                        gr.update(), gr.update(), gr.update(),  # buttons
                        gr.update(), gr.update(), gr.update(),  # more buttons
                        gr.update(value=error_msg),            # selected_step_display
                        gr.update(interactive=True)            # steps_table
                    )

                # 2. 获取该正确类别下的所有操作
                actions_in_correct_category = registry_ref.get_actions_in_category(correct_category)
                if action_name_to_edit not in actions_in_correct_category: # 安全校验
                    error_msg = f"错误：操作 '{action_name_to_edit}' 不在它本应属于的类别 '{correct_category}' 中。Action Registry可能存在问题。"
                    gr.Error(error_msg)
                    return ( # 明确返回13个更新
                        gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                        gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                        gr.update(), gr.update(value=error_msg), gr.update(interactive=True)
                    )

                # 3. 准备对下拉框的更新
                category_dropdown_update = gr.update(value=correct_category)
                action_dropdown_update = gr.update(choices=actions_in_correct_category, value=action_name_to_edit)

                # 4. 准备参数用于UI显示
                prepared_params_for_state = {}
                action_param_definitions = registry_ref.get_action_params(action_name_to_edit)
                if action_param_definitions is None: # 之前 workflowPP.py 有 if not action_param_definitions
                    error_msg = f"错误：未能获取操作 '{action_name_to_edit}' 的参数定义（可能返回了None）。"
                    gr.Error(error_msg)
                    return ( # 明确返回13个更新
                        gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                        gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                        gr.update(), gr.update(value=error_msg), gr.update(interactive=True)
                    )
                
                # (循环填充 prepared_params_for_state - 这部分逻辑来自您 workflowPP.py 已有的部分)
                for param_name, (default_val_reg, param_type_hint) in action_param_definitions.items():
                    raw_value = params_to_edit_raw.get(param_name)
                    if param_type_hint in (Optional[Dict], Optional[List]) or \
                    (isinstance(default_val_reg, (dict, list)) and not isinstance(default_val_reg, bool)):
                        if raw_value is not None:
                            prepared_params_for_state[param_name] = json.dumps(raw_value, ensure_ascii=False)
                        else:
                            # 对于 Textbox，传递 None 或空字符串 "" 都可以，Gradio 通常能处理
                            # 但为了与 render_params_inputs 中对 Textbox value 的处理一致 (不应为None)，这里也用 "" 或 None
                            prepared_params_for_state[param_name] = None # 或者 "" 如果 render_params_inputs 的 Textbox 不能接受 None
                    elif isinstance(default_val_reg, bool): # 对应 Checkbox
                        prepared_params_for_state[param_name] = bool(raw_value) if raw_value is not None else False
                    else: # 对应 Number 或 Textbox (非JSON str)
                        prepared_params_for_state[param_name] = raw_value
                logger.info(f"Prepared temporary_editing_params for state: {prepared_params_for_state}")

                # (获取 display_text_on_edit - 这部分逻辑来自您 workflowPP.py 已有的部分)
                actual_row_number_in_df = selected_0_based_idx + 1 # Dataframe中的行号是1-based
                display_text_on_edit = f"正在编辑第 {actual_row_number_in_df} 行: {action_name_to_edit}"

                # 5. 返回所有更新 (成功进入编辑模式)
                return (
                    gr.update(value=True),                      # edit_mode_active
                    gr.update(value=selected_0_based_idx),      # editing_step_index
                    gr.update(value=prepared_params_for_state), # temporary_editing_params
                    category_dropdown_update,                   # category_dropdown
                    action_dropdown_update,                     # action_dropdown
                    gr.update(value="更新步骤", visible=True),   # add_step_btn
                    gr.update(visible=True),                    # cancel_edit_btn
                    gr.update(visible=False),                   # edit_step_btn (隐藏自己)
                    gr.update(visible=False),                   # delete_step_btn (禁用其他表格操作)
                    gr.update(visible=False),                   # move_up_btn
                    gr.update(visible=False),                   # move_down_btn
                    display_text_on_edit,                       # selected_step_display
                    gr.update(interactive=False)                # steps_table (设为不可交互)
                )

            except Exception as e: # 捕获所有其他未预料的错误
                logger.error(f"进入编辑模式时发生严重错误: {e}", exc_info=True)
                error_msg_for_ui = f"进入编辑模式失败: {str(e)}"
                gr.Error(error_msg_for_ui) # Gradio内置的错误提示条
                return ( # 明确返回13个更新
                    gr.update(value=False), gr.update(value=None), gr.update(value={}), # 重置编辑状态
                    gr.update(), gr.update(),                                          # dropdowns (无变化)
                    gr.update(value="添加步骤", visible=True), gr.update(visible=False), # add_step_btn, cancel_edit_btn
                    gr.update(visible=True), gr.update(visible=True),                  # 其他按钮恢复原始可见性
                    gr.update(visible=True), gr.update(visible=True),
                    gr.update(value=error_msg_for_ui),                                 # selected_step_display
                    gr.update(interactive=True)                                        # steps_table (保持可交互)
                )

        def handle_cancel_edit(): 
            """
            处理取消编辑操作，将UI重置回非编辑状态。
            """
            logger.info("用户取消编辑操作。UI将重置。")
            
            # 重置UI状态到非编辑模式
            # 按钮的标签和可见性将被更新
            # 相关的State变量将被清空或重置
            # selected_step_display 和 selected_step_index 也会被重置
            return (
                gr.update(value=False),                         # edit_mode_active: 设为 False，退出编辑模式
                gr.update(value=None),                          # editing_step_index: 清空正在编辑的步骤索引
                gr.update(value={}),                            # temporary_editing_params: 清空临时编辑参数
                gr.update(value="添加步骤", visible=True),    # add_step_btn: 恢复标签为"添加步骤"并设为可见
                gr.update(visible=False),                       # cancel_edit_btn: 隐藏"取消编辑"按钮
                gr.update(visible=True),                        # edit_step_btn: 恢复"编辑选中步骤"按钮的可见性
                gr.update(visible=True),                        # delete_step_btn: 恢复"删除选中步骤"按钮的可见性
                gr.update(visible=True),                        # move_up_btn: 恢复"上移"按钮的可见性
                gr.update(visible=True),                        # move_down_btn: 恢复"下移"按钮的可见性
                "未选择任何步骤 (编辑已取消)",                   # selected_step_display: 更新选中步骤的显示文本
                gr.update(value=None),                           # selected_step_index: 清空实际的步骤选择索引，以取消表格中的高亮（如果适用）
                gr.update(interactive=True)   
            )



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


        def handle_actual_update_step(
            workflow_id_val: str,
            editing_step_index_val: int,
            action_name: str,
            *param_values_tuple
        ):
            logger.info(f"Updating step at index {editing_step_index_val} for workflow '{workflow_id_val}' with action '{action_name}'.")
            logger.debug(f"Received param values for update: {param_values_tuple}")

            def _create_ui_update_tuple(
                wf_output_update, steps_table_update, selected_display_update,
                edit_mode_update, editing_idx_update, temp_params_update,
                add_btn_update, cancel_btn_update, edit_btn_update,
                delete_btn_update, move_up_update, move_down_update
            ):
                return (
                    wf_output_update, steps_table_update, selected_display_update,
                    edit_mode_update, editing_idx_update, temp_params_update,
                    add_btn_update, cancel_btn_update, edit_btn_update,
                    delete_btn_update, move_up_update, move_down_update
                )

            error_message_display = ""

            try:
                workflow_data = WorkflowService.get_workflow(workflow_id_val)
                if not workflow_data:
                    logger.error(f"Workflow ID '{workflow_id_val}' not found during update.")
                    error_message_display = f"错误: 工作流 ID '{workflow_id_val}' 未找到。"
                    raise WorkflowError(error_message_display) # 使用您定义的 WorkflowError

                steps = workflow_data.get("steps", [])
                if not (0 <= editing_step_index_val < len(steps)):
                    logger.error(f"Invalid step index {editing_step_index_val} for workflow '{workflow_id_val}' with {len(steps)} steps.")
                    error_message_display = f"错误: 无效的步骤索引 {editing_step_index_val}。"
                    raise WorkflowError(error_message_display)

                action_param_definitions = action_registry.get_action_params(action_name)
                if action_param_definitions is None: # 假设 get_action_params 在找不到时返回 None
                    logger.error(f"Could not get parameter definitions for action '{action_name}' during update.")
                    error_message_display = f"错误: 未知操作 '{action_name}'。"
                    raise WorkflowError(error_message_display)

                processed_params = {}
                param_names_from_definition = list(action_param_definitions.keys())

                if len(param_values_tuple) != len(param_names_from_definition):
                    logger.error(f"Parameter count mismatch for action '{action_name}'. Expected {len(param_names_from_definition)}, got {len(param_values_tuple)}.")
                    error_message_display = f"错误: 操作 '{action_name}' 的参数数量不匹配。"
                    raise WorkflowError(error_message_display)

                for i, param_name in enumerate(param_names_from_definition):
                    raw_value_from_component = param_values_tuple[i]
                    _default_val, param_type_hint_actual = action_param_definitions[param_name]

                    actual_target_type = param_type_hint_actual
                    is_optional = get_origin(param_type_hint_actual) is Union and type(None) in get_args(param_type_hint_actual)
                    if is_optional:
                        actual_target_type = next((t for t in get_args(param_type_hint_actual) if t is not type(None)), actual_target_type)
                    
                    current_processed_value = None
                    if raw_value_from_component is None:
                        if not is_optional:
                            raise ValueError(f"参数 '{param_name}' 是必需的，但其值为 None。")
                        # 保持 current_processed_value = None
                    elif actual_target_type == bool:
                        if isinstance(raw_value_from_component, str): # 以防万一
                            current_processed_value = raw_value_from_component.lower() == 'true'
                        else:
                            current_processed_value = bool(raw_value_from_component)
                    elif actual_target_type == int:
                        current_processed_value = int(raw_value_from_component)
                    elif actual_target_type == float:
                        current_processed_value = float(raw_value_from_component)
                    elif actual_target_type in (dict, list, Dict, List): # 适用于 typing.Dict, List 和内建 dict, list
                        if not isinstance(raw_value_from_component, str):
                            # 如果UI设计确保了这里总是字符串，这条可以去掉，否则是重要检查
                            raise ValueError(f"参数 '{param_name}' (用于字典/列表) 期望得到JSON字符串，但收到了 {type(raw_value_from_component)} 类型。")
                        if not raw_value_from_component.strip(): # 空字符串
                            if is_optional:
                                current_processed_value = None
                            else:
                                raise ValueError(f"必需的字典/列表参数 '{param_name}' 收到了空字符串。")
                        else:
                            current_processed_value = json.loads(raw_value_from_component)
                    else: # 默认为字符串
                        current_processed_value = str(raw_value_from_component)
                    
                    processed_params[param_name] = current_processed_value

                # 更新工作流数据中的步骤
                step_to_update = workflow_data["steps"][editing_step_index_val]
                step_to_update['action_name'] = action_name # 确保 action_name 也被更新
                step_to_update['params'] = processed_params
                # 如果步骤有其他可编辑字段（例如步骤名称），也在这里更新

                WorkflowService.save_workflow(workflow_data) # 保存整个工作流
                logger.info(f"Step at index {editing_step_index_val} updated and workflow saved.")

                # 成功更新
                return _create_ui_update_tuple(
                    wf_output_update=gr.update(value=json.dumps(workflow_data, indent=2, ensure_ascii=False)),
                    steps_table_update=gr.update(value=_format_steps_for_dataframe(workflow_data["steps"]),interactive=True),
                    selected_display_update=gr.update(value="步骤已成功更新。"), # 或清空，或显示新步骤信息
                    edit_mode_update=gr.update(value=False),      # 退出编辑模式
                    editing_idx_update=gr.update(value=None),      # 重置编辑索引 (Gradio State通常用None重置)
                    temp_params_update=gr.update(value={}),      # 清空临时参数
                    add_btn_update=gr.update(label="添加步骤", visible=True),
                    cancel_btn_update=gr.update(visible=False),
                    edit_btn_update=gr.update(visible=True, interactive=False), # 可见，但通常在选中步骤后才可交互
                    delete_btn_update=gr.update(visible=True, interactive=False),
                    move_up_update=gr.update(visible=True, interactive=False),
                    move_down_update=gr.update(visible=True, interactive=False)
                )

            except (WorkflowError, ValueError, TypeError, json.JSONDecodeError) as e:
                logger.error(f"Error during step update: {e}", exc_info=True)
                # 如果 error_message_display 之前已被特定错误填充，则使用它
                final_error_message = error_message_display if error_message_display else f"更新步骤失败: {e}"
                
                # 出错时，保持在编辑模式可能更好，以便用户修正
                return _create_ui_update_tuple(
                    wf_output_update=gr.update(), # 不改变 workflow_output 或显示通用错误
                    steps_table_update=gr.update(), # 不改变 steps_table
                    selected_display_update=gr.update(value=final_error_message),
                    edit_mode_update=gr.update(value=True), # 保持在编辑模式
                    editing_idx_update=gr.update(value=editing_step_index_val), # 保持当前编辑索引
                    temp_params_update=gr.update(), # 不改变临时参数，以便用户看到他们输入的内容
                    add_btn_update=gr.update(label="更新步骤", visible=True), # 按钮文字保持“更新步骤”
                    cancel_btn_update=gr.update(visible=True),
                    edit_btn_update=gr.update(visible=False), # 编辑按钮在编辑模式下应隐藏
                    delete_btn_update=gr.update(visible=False), # 其他操作按钮也隐藏
                    move_up_update=gr.update(visible=False),
                    move_down_update=gr.update(visible=False)
                )
            except Exception as e: # 捕获其他意外错误
                logger.error(f"Unexpected error during step update: {e}", exc_info=True)
                final_error_message = f"发生意外错误，更新步骤失败: {e}"
                return _create_ui_update_tuple(
                    wf_output_update=gr.update(),
                    steps_table_update=gr.update(),
                    selected_display_update=gr.update(value=final_error_message),
                    edit_mode_update=gr.update(value=True),
                    editing_idx_update=gr.update(value=editing_step_index_val),
                    temp_params_update=gr.update(),
                    add_btn_update=gr.update(label="更新步骤", visible=True),
                    cancel_btn_update=gr.update(visible=True),
                    edit_btn_update=gr.update(visible=False),
                    delete_btn_update=gr.update(visible=False),
                    move_up_update=gr.update(visible=False),
                    move_down_update=gr.update(visible=False)
                )


                

        @gr.render(inputs=[action_dropdown, edit_mode_active, temporary_editing_params])
        def render_params_inputs(action_name, is_edit_mode, params_to_use_for_editing):
            # 1. 获取参数定义
            params_definition = {}  # 默认为空字典，适用于无有效操作或操作无参数的情况
            if action_name and action_name != "无操作可用":
                action_params_result = action_registry.get_action_params(action_name)
                if action_params_result is not None:
                    params_definition = action_params_result
                else:
                    logger.error(f"Render_params_inputs: Action '{action_name}' selected, but get_action_params returned None. Treating as no parameters, but this indicates an issue with action registration or naming.")
                    # 保持 params_definition 为 {}, UI上不显示参数输入，但允许按钮重新绑定

            # logger.info(f"Render_params_inputs: Action='{action_name}', EditMode={is_edit_mode}, ParamsForEditing='{params_to_use_for_editing if is_edit_mode else 'N/A'}'")

            # 2. 创建参数UI组件 (必须进入 with gr.Column 以便 @gr.render 返回组件)
            with gr.Column():
                components = []
                # 只有当 params_definition 字典非空时（即操作有参数），才遍历生成输入组件
                if params_definition:
                    for param_name, (default_value_from_registry, param_type) in params_definition.items():
                        # 确定组件当前应显示的值
                        current_value_for_component = default_value_from_registry
                        if is_edit_mode and params_to_use_for_editing and param_name in params_to_use_for_editing:
                            current_value_for_component = params_to_use_for_editing[param_name]

                        component = None
                        info = None # 初始化提示信息

                        # --- 开始组件生成逻辑 (基于您 workflowPP.py 中的结构) ---
                        if param_type == Optional[int]:
                            info = "请输入整数或留空（使用 None）"
                            component = gr.Number(
                                label=param_name,
                                value=current_value_for_component, # Optional[int]可以直接使用None或int
                                precision=0,
                                info=info
                            )
                        elif param_type == Optional[float]:
                            info = "请输入浮点数或留空（使用 None）"
                            component = gr.Number(
                                label=param_name,
                                value=current_value_for_component, # Optional[float]可以直接使用None或float
                                info=info
                            )
                        elif param_type in (Optional[Dict], Optional[List]) or \
                            (not str(param_type).startswith("typing.Optional") and isinstance(default_value_from_registry, (dict, list))):
                            # 这个条件覆盖: Optional[Dict], Optional[List], 和非Optional但默认值是dict/list的情况
                            info = "请输入 JSON 格式或留空（如果可选）"
                            if isinstance(default_value_from_registry, (dict, list)) and not str(param_type).startswith("typing.Optional"):
                                info = "请输入 JSON 格式 (例如 {\"key\": \"value\"} 或 [1, 2, 3])" # 非可选的提示
                            else: # Optional[Dict/List]
                                info = "请输入 JSON 格式（例如 {\"key\": \"value\"}）或留空（使用 None）"

                            val_for_textbox = current_value_for_component
                            # 如果当前值是Python的dict或list (通常来自默认值，或非编辑模式下)，则转为JSON字符串
                            # 如果已经是JSON字符串 (来自编辑模式的 temporary_editing_params)，或为None，则直接使用
                            if isinstance(val_for_textbox, (dict, list)):
                                val_for_textbox = json.dumps(val_for_textbox, ensure_ascii=False)

                            component = gr.Textbox(
                                label=param_name,
                                value=val_for_textbox,
                                lines=3, # 根据您的喜好调整行数
                                placeholder="请输入 JSON 格式",
                                info=info
                            )
                        elif param_type == Optional[str]:
                            info = "请输入文本或留空（使用 None）"
                            component = gr.Textbox(
                                label=param_name,
                                value=current_value_for_component if current_value_for_component is not None else "", # Textbox value不应是None
                                info=info
                            )
                        elif isinstance(default_value_from_registry, bool): # 适用于 bool 和 Optional[bool] (如果 Optional[bool] 的默认值是布尔型)
                            info = "选择是否启用"
                            processed_bool_value = False # 默认值，以防 current_value_for_component 为 None 或无法转换
                            if current_value_for_component is not None:
                                if isinstance(current_value_for_component, str): # 处理从状态恢复的 'true'/'false' 字符串
                                    processed_bool_value = current_value_for_component.lower() == 'true'
                                else:
                                    processed_bool_value = bool(current_value_for_component)
                            component = gr.Checkbox(
                                label=param_name,
                                value=processed_bool_value,
                                info=info
                            )
                        # 处理非Optional的原始类型 (这些通常由 isinstance(default_value_from_registry, ...) 捕获)
                        elif isinstance(default_value_from_registry, int) and param_type not in [Optional[int]]: # 确保不是Optional[int]已被处理
                            info = "请输入整数"
                            component = gr.Number(
                                label=param_name,
                                value=current_value_for_component,
                                precision=0,
                                info=info
                            )
                        elif isinstance(default_value_from_registry, float) and param_type not in [Optional[float]]: # 确保不是Optional[float]已被处理
                            info = "请输入浮点数"
                            component = gr.Number(
                                label=param_name,
                                value=current_value_for_component,
                                info=info
                            )
                        else: # 默认回退到字符串输入 (适用于 str 和其他未明确处理的类型)
                            info = "请输入文本"
                            # Textbox的value不应是None，确保转换
                            component_value = str(current_value_for_component) if current_value_for_component is not None else ""
                            component = gr.Textbox(
                                label=param_name,
                                value=component_value,
                                info=info
                            )
                        # --- 结束组件生成逻辑 ---

                        if component is not None:
                            components.append(component)
                        else: # 理论上不应发生，但作为保障
                            logger.error(f"Component for '{param_name}' of type '{param_type}' was unexpectedly not created.")
                            # 可以添加一个占位的 gr.Markdown 提示错误
                            components.append(gr.Markdown(f"参数 '{param_name}' UI生成失败。", visible=True))

                if is_edit_mode:
                    # logger.debug(f"Binding 'Update Step' for action: {action_name}, components: {[c.label for c in components]}")
                    add_step_btn.click(
                        fn=handle_actual_update_step,
                        inputs=[
                            workflow_id,
                            editing_step_index,
                            action_dropdown # 当前选中的操作名称
                        ] + components, # components 列表可能是空的
                        outputs=[ # 对应 handle_actual_update_step 的返回
                            workflow_output, steps_table, selected_step_display,
                            edit_mode_active, editing_step_index, temporary_editing_params,
                            add_step_btn, cancel_edit_btn, edit_step_btn,
                            delete_step_btn, move_up_btn, move_down_btn
                        ]
                    )
                else: # 非编辑模式 (即添加新步骤的模式)
                    # logger.debug(f"Binding 'Add Step' for action: {action_name}, components: {[c.label for c in components]}")
                    add_step_btn.click(
                        fn=add_step,
                        inputs=[
                            workflow_id,
                            action_dropdown # 当前选中的操作名称
                        ] + components, # components 列表可能是空的 (对于无参数操作)
                        outputs=[workflow_output, steps_table, workflow_output] # add_step 的原始 outputs
                    )

            # 4. 返回生成的UI组件列表 (如果无参数则为空列表)
            return components

        def create_workflow(name, desc):
            try:
                if not name.strip():
                    raise WorkflowError("工作流名称不能为空")
                workflow_data = WorkflowService.create_workflow(name, desc)
                logger.info(f"Created workflow: {workflow_data['id']}")
                updated_choices = [(w["name"], w["id"]) for w in WorkflowService.get_all_workflows()] or [("无工作流", "")]
                return (
                    workflow_data["id"],
                    json.dumps(workflow_data, indent=2, ensure_ascii=False),
                    [],  # steps_table
                    "",  # workflow_name
                    gr.update(choices=updated_choices) 
                )
            except WorkflowError as e:
                logger.error(f"Create workflow error: {str(e)}")
                return None, str(e), [], gr.update()

        create_btn.click(
            fn=create_workflow,
            inputs=[workflow_name, workflow_desc],
            outputs=[workflow_id, workflow_output, steps_table, workflow_name, load_dropdown]
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
                updated_choices = [(w["name"], w["id"]) for w in WorkflowService.get_all_workflows()] or [("无工作流", "")]
                return (
                    json.dumps(workflow_data, indent=2, ensure_ascii=False),
                    gr.update(choices=updated_choices) # <--- 新增更新 load_dropdown
                )
            except WorkflowError as e:
                logger.error(f"Save workflow error: {str(e)}")
                return str(e)

        save_btn.click(
            fn=save_workflow,
            inputs=[workflow_id, workflow_name, workflow_desc],
            outputs=[workflow_output, load_dropdown]
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

        edit_step_btn.click(
            fn=handle_edit_mode_entry,
            inputs=[workflow_id, selected_step_index, gr.State(action_registry)], # 确保 action_registry 被正确传递
            outputs=[
                edit_mode_active, editing_step_index, temporary_editing_params,
                category_dropdown, action_dropdown,
                add_step_btn, cancel_edit_btn, edit_step_btn,
                delete_step_btn, move_up_btn, move_down_btn,
                selected_step_display,
                steps_table
            ]
        )
        cancel_edit_btn.click(
            fn=handle_cancel_edit, 
            inputs=[], 
            outputs=[ # 对应 handle_cancel_edit 的返回
                edit_mode_active, editing_step_index, temporary_editing_params,
                add_step_btn, cancel_edit_btn, edit_step_btn,
                delete_step_btn, move_up_btn, move_down_btn,
                selected_step_display, selected_step_index,
                steps_table
            ]
        )
