import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QMessageBox, QGroupBox,
    QSplitter, QFrame, QToolBar, QAction, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage

from src.data import Workflow, ExecutionRecord, workflow_engine, history_manager


class TaskExecutionWidget(QWidget):
    """
    任务执行部件，展示处理任务的执行过程和结果
    """
    task_started = pyqtSignal()
    task_finished = pyqtSignal(bool, str)  # 成功状态, 消息

    # 新增信号，用于线程安全更新UI
    progress_signal = pyqtSignal(str, float, str)  # status, progress, message
    log_signal = pyqtSignal(str)  # message
    result_signal = pyqtSignal(dict)  # step_log

    def __init__(self, workflow: Workflow, source_type: str, source_params: Dict[str, Any],
                output_directory: str, parent=None):
        super().__init__(parent)

        self.workflow = workflow
        self.source_type = source_type
        self.source_params = source_params
        self.output_directory = output_directory

        self.execution_record: Optional[ExecutionRecord] = None
        self.is_running = False

        # 初始化UI
        self.init_ui()

        # 连接信号到槽
        self.progress_signal.connect(self.on_progress_update)
        self.log_signal.connect(self.add_log)
        self.result_signal.connect(self.update_result_tree)

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 任务信息
        info_layout = QHBoxLayout()

        self.workflow_label = QLabel(f"工作流: {self.workflow.name}")
        info_layout.addWidget(self.workflow_label)

        self.source_label = QLabel(f"源: {self.source_type}")
        info_layout.addWidget(self.source_label)

        self.output_label = QLabel(f"输出: {self.output_directory}")
        info_layout.addWidget(self.output_label)

        # 添加到主布局
        layout.addLayout(info_layout)

        # 进度部分
        progress_group = QGroupBox("执行进度")
        progress_layout = QVBoxLayout(progress_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("准备执行...")
        progress_layout.addWidget(self.status_label)

        # 添加到主布局
        layout.addWidget(progress_group)

        # 日志输出
        log_group = QGroupBox("执行日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        # 添加到主布局
        layout.addWidget(log_group)

        # 结果部分
        result_group = QGroupBox("执行结果")
        result_layout = QVBoxLayout(result_group)

        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["步骤", "状态", "详情"])
        self.result_tree.setColumnWidth(0, 200)
        self.result_tree.setColumnWidth(1, 100)
        result_layout.addWidget(self.result_tree)

        # 添加到主布局
        layout.addWidget(result_group)

        # 控制按钮
        buttons_layout = QHBoxLayout()

        self.start_button = QPushButton("开始执行")
        self.start_button.clicked.connect(self.start_task)
        buttons_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("停止执行")
        self.stop_button.clicked.connect(self.stop_task)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)

        self.open_output_button = QPushButton("打开输出目录")
        self.open_output_button.clicked.connect(self.open_output_directory)
        buttons_layout.addWidget(self.open_output_button)

        # 添加到主布局
        layout.addLayout(buttons_layout)

        # 更新计时器
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_progress)
        self.update_timer.setInterval(1000)  # 1秒更新一次

    def start_task(self):
        """开始执行任务"""
        if self.is_running:
            return

        # 重置UI
        self.progress_bar.setValue(0)
        self.status_label.setText("正在启动...")
        self.log_text.clear()
        self.result_tree.clear()

        # 更新按钮状态
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # 添加首条日志
        self.log_signal.emit("开始执行任务...")
        self.log_signal.emit(f"工作流: {self.workflow.name}")
        self.log_signal.emit(f"源类型: {self.source_type}")
        self.log_signal.emit(f"输出目录: {self.output_directory}")

        # 启动任务
        self.execution_record = workflow_engine.execute_workflow(
            self.workflow,
            self.source_type,
            self.source_params,
            self.output_directory,
            self.on_progress_callback
        )

        self.is_running = True

        # 启动更新计时器
        self.update_timer.start()

        # 发送任务开始信号
        self.task_started.emit()

    def stop_task(self):
        """停止执行任务"""
        if not self.is_running or not self.execution_record:
            return

        # 确认停止
        reply = QMessageBox.question(
            self, "确认停止", "确定要停止当前任务吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # 尝试取消任务
        if workflow_engine.cancel_task(self.execution_record.id):
            self.log_signal.emit("任务已取消")
            self.status_label.setText("已取消")

            # 更新任务状态
            self.is_running = False

            # 停止更新计时器
            self.update_timer.stop()

            # 更新按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

            # 发送任务完成信号
            self.task_finished.emit(False, "任务已取消")
        else:
            self.log_signal.emit("无法取消任务")
            QMessageBox.warning(self, "错误", "无法取消任务，任务可能已完成或出错。")

    def on_progress_callback(self, status: str, progress: float, message: str):
        """
        进度更新回调，子线程调用，发信号给主线程

        Args:
            status: 当前状态
            progress: 进度值 (0.0 - 1.0)
            message: 状态消息
        """
        self.progress_signal.emit(status, progress, message)

    @pyqtSlot(str, float, str)
    def on_progress_update(self, status: str, progress: float, message: str):
        """
        进度更新槽函数，主线程更新UI

        Args:
            status: 当前状态
            progress: 进度值 (0.0 - 1.0)
            message: 状态消息
        """
        # 更新进度条
        progress_value = int(progress * 100)
        self.progress_bar.setValue(progress_value)

        # 更新状态标签
        self.status_label.setText(f"{status}: {message}")

        # 添加日志
        self.log_signal.emit(f"[{status}] {message}")

    @pyqtSlot(str)
    def add_log(self, message: str):
        """
        添加日志，主线程更新UI

        Args:
            message: 日志消息
        """
        self.log_text.append(message)

        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    @pyqtSlot(dict)
    def update_result_tree(self, step_log: dict):
        """
        更新结果树显示，主线程更新UI

        Args:
            step_log: 步骤日志字典
        """
        step_id = step_log.get("step_id")
        step_name = step_log.get("step_name")
        status = step_log.get("status")
        message = step_log.get("message", "")

        # 创建或获取步骤项
        found = False
        for i in range(self.result_tree.topLevelItemCount()):
            item = self.result_tree.topLevelItem(i)
            if item.text(0) == step_name:
                # 更新已有项
                item.setText(1, status)
                item.setText(2, message)
                step_item = item
                found = True
                break

        if not found:
            # 创建新项
            step_item = QTreeWidgetItem([step_name, status, message])
            self.result_tree.addTopLevelItem(step_item)

        # 添加详情子项
        details = step_log.get("details", {})
        if details:
            for key, value in details.items():
                detail_item = QTreeWidgetItem([key, "", str(value)])
                step_item.addChild(detail_item)

        # 展开所有项
        self.result_tree.expandAll()

    def update_progress(self):
        """更新进度和结果显示"""
        if not self.is_running or not self.execution_record:
            return

        # 检查执行记录状态
        record = history_manager.get_record(self.execution_record.id)
        if not record:
            return

        # 更新执行记录
        self.execution_record = record

        # 检查是否完成
        if record.status != "running":
            # 任务完成
            self.is_running = False

            # 停止更新计时器
            self.update_timer.stop()

            # 更新按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

            # 更新进度和状态
            if record.status == "completed":
                self.progress_bar.setValue(100)
                self.status_label.setText(f"已完成 (成功: {record.success_images}, 失败: {record.failed_images})")
                self.log_signal.emit(f"任务完成. 总图像: {record.total_images}, 成功: {record.success_images}, 失败: {record.failed_images}")

                # 发送任务完成信号
                self.task_finished.emit(True, f"成功处理 {record.success_images} 个图像, 失败 {record.failed_images} 个")
            else:
                self.status_label.setText(f"出错: {record.error_message}")
                self.log_signal.emit(f"任务失败: {record.error_message}")

                # 发送任务完成信号
                self.task_finished.emit(False, record.error_message or "任务执行失败")

    def open_output_directory(self):
        """打开输出目录"""
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                os.startfile(self.output_directory)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", self.output_directory])
            else:  # Linux
                subprocess.Popen(["xdg-open", self.output_directory])
        except Exception as e:
            QMessageBox.warning(
                self, "错误", f"无法打开输出目录: {str(e)}"
            )