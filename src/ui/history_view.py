"""
历史记录视图模块 - 显示图像处理任务的历史记录
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget,
    QTreeWidgetItem, QMessageBox, QGroupBox, QMenu, QAction, QDialog,
    QFormLayout, QTextEdit, QDialogButtonBox, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

from src.data import ExecutionRecord, history_manager


class ExecutionDetailDialog(QDialog):
    """
    执行记录详情对话框
    """
    def __init__(self, record: ExecutionRecord, parent=None):
        super().__init__(parent)
        
        self.record = record
        
        self.setWindowTitle(f"执行记录详情 - {record.id}")
        self.setMinimumSize(600, 400)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 基本信息
        info_group = QGroupBox("基本信息")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("工作流:", QLabel(record.workflow_name or "未知"))
        info_layout.addRow("工作流ID:", QLabel(record.workflow_id or "未知"))
        info_layout.addRow("源类型:", QLabel(record.source_type or "未知"))
        
        # 格式化时间显示
        start_time = record.start_time
        if start_time:
            try:
                dt = datetime.fromisoformat(start_time)
                start_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        end_time = record.end_time
        if end_time:
            try:
                dt = datetime.fromisoformat(end_time)
                end_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        info_layout.addRow("开始时间:", QLabel(start_time or "未知"))
        info_layout.addRow("结束时间:", QLabel(end_time or "进行中"))
        info_layout.addRow("状态:", QLabel(record.status or "未知"))
        
        if record.error_message:
            info_layout.addRow("错误信息:", QLabel(record.error_message))
        
        info_layout.addRow("总图像数:", QLabel(str(record.total_images)))
        info_layout.addRow("处理图像数:", QLabel(str(record.processed_images)))
        info_layout.addRow("成功图像数:", QLabel(str(record.success_images)))
        info_layout.addRow("失败图像数:", QLabel(str(record.failed_images)))
        
        info_layout.addRow("输出目录:", QLabel(record.output_directory or "未知"))
        
        layout.addWidget(info_group)
        
        # 源参数
        if record.source_params:
            source_group = QGroupBox("源参数")
            source_layout = QFormLayout(source_group)
            
            for key, value in record.source_params.items():
                source_layout.addRow(f"{key}:", QLabel(str(value)))
            
            layout.addWidget(source_group)
        
        # 步骤日志
        if record.step_logs:
            steps_group = QGroupBox("步骤日志")
            steps_layout = QVBoxLayout(steps_group)
            
            steps_tree = QTreeWidget()
            steps_tree.setHeaderLabels(["步骤", "状态", "时间", "消息"])
            steps_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
            
            for log in record.step_logs:
                step_name = log.get("step_name", "未知")
                status = log.get("status", "未知")
                timestamp = log.get("timestamp", "")
                message = log.get("message", "")
                
                # 格式化时间显示
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        timestamp = dt.strftime("%H:%M:%S")
                    except:
                        pass
                
                item = QTreeWidgetItem([step_name, status, timestamp, message])
                
                # 根据状态设置颜色
                if status == "completed":
                    item.setForeground(1, QColor(0, 128, 0))  # 绿色
                elif status == "failed":
                    item.setForeground(1, QColor(255, 0, 0))  # 红色
                
                steps_tree.addTopLevelItem(item)
                
                # 添加详情子项
                details = log.get("details", {})
                if details:
                    for key, value in details.items():
                        detail_item = QTreeWidgetItem(["", key, "", str(value)])
                        item.addChild(detail_item)
            
            steps_layout.addWidget(steps_tree)
            layout.addWidget(steps_group)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


class HistoryViewWidget(QWidget):
    """
    历史记录视图部件，显示历史执行记录
    """
    record_selected = pyqtSignal(str)  # 记录ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化UI
        self.init_ui()
        
        # 加载历史记录
        self.refresh_records()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建工具栏
        toolbar_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_records)
        toolbar_layout.addWidget(self.refresh_button)
        
        self.clear_button = QPushButton("清理记录")
        self.clear_button.clicked.connect(self.clear_records)
        toolbar_layout.addWidget(self.clear_button)
        
        toolbar_layout.addStretch()
        
        # 添加到主布局
        layout.addLayout(toolbar_layout)
        
        # 历史记录树
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["时间", "工作流", "状态", "图像数"])
        self.history_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.history_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # 设置列宽
        self.history_tree.setColumnWidth(0, 150)
        self.history_tree.setColumnWidth(1, 150)
        self.history_tree.setColumnWidth(2, 80)
        
        # 添加到主布局
        layout.addWidget(self.history_tree)
    
    def refresh_records(self):
        """刷新历史记录"""
        self.history_tree.clear()
        
        # 获取所有记录
        records = history_manager.get_all_records()
        
        # 添加到树
        for record in records:
            self.add_record_to_tree(record)
    
    def add_record_to_tree(self, record: ExecutionRecord):
        """
        将记录添加到树
        
        Args:
            record: 执行记录
        """
        # 格式化时间显示
        time_str = record.start_time
        if time_str:
            try:
                dt = datetime.fromisoformat(time_str)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        # 创建项
        item = QTreeWidgetItem([
            time_str or "未知",
            record.workflow_name or "未知",
            record.status or "未知",
            str(record.total_images)
        ])
        
        # 设置数据
        item.setData(0, Qt.UserRole, record.id)
        
        # 根据状态设置颜色
        if record.status == "completed":
            item.setForeground(2, QColor(0, 128, 0))  # 绿色
        elif record.status == "failed":
            item.setForeground(2, QColor(255, 0, 0))  # 红色
        elif record.status == "running":
            item.setForeground(2, QColor(0, 0, 255))  # 蓝色
        
        # 添加到树
        self.history_tree.addTopLevelItem(item)
    
    def show_context_menu(self, position):
        """
        显示上下文菜单
        
        Args:
            position: 鼠标位置
        """
        item = self.history_tree.itemAt(position)
        if not item:
            return
        
        # 获取记录ID
        record_id = item.data(0, Qt.UserRole)
        if not record_id:
            return
        
        # 创建菜单
        menu = QMenu(self)
        
        # 查看详情
        view_action = QAction("查看详情", self)
        view_action.triggered.connect(lambda: self.view_record_details(record_id))
        menu.addAction(view_action)
        
        # 打开输出目录
        record = history_manager.get_record(record_id)
        if record and record.output_directory:
            open_action = QAction("打开输出目录", self)
            open_action.triggered.connect(lambda: self.open_output_directory(record.output_directory))
            menu.addAction(open_action)
        
        menu.addSeparator()
        
        # 删除记录
        delete_action = QAction("删除记录", self)
        delete_action.triggered.connect(lambda: self.delete_record(record_id))
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec_(self.history_tree.mapToGlobal(position))
    
    def on_item_double_clicked(self, item, column):
        """
        项双击事件
        
        Args:
            item: 双击的项
            column: 双击的列
        """
        # 获取记录ID
        record_id = item.data(0, Qt.UserRole)
        if not record_id:
            return
        
        # 发送记录选择信号
        self.record_selected.emit(record_id)
        
        # 查看详情
        self.view_record_details(record_id)
    
    def view_record_details(self, record_id: str):
        """
        查看记录详情
        
        Args:
            record_id: 记录ID
        """
        record = history_manager.get_record(record_id)
        if not record:
            QMessageBox.warning(self, "错误", f"未找到记录 {record_id}")
            return
        
        # 显示详情对话框
        dialog = ExecutionDetailDialog(record, self)
        dialog.exec_()
    
    def open_output_directory(self, directory: str):
        """
        打开输出目录
        
        Args:
            directory: 目录路径
        """
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                os.startfile(directory)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", directory])
            else:  # Linux
                subprocess.Popen(["xdg-open", directory])
        except Exception as e:
            QMessageBox.warning(
                self, "错误", f"无法打开目录: {str(e)}"
            )
    
    def delete_record(self, record_id: str):
        """
        删除记录
        
        Args:
            record_id: 记录ID
        """
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除此记录吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 删除记录
        if history_manager.delete_record(record_id):
            # 刷新显示
            self.refresh_records()
        else:
            QMessageBox.warning(self, "错误", f"删除记录失败")
    
    def clear_records(self):
        """清理历史记录"""
        # 创建菜单
        menu = QMenu(self)
        
        # 清理所有记录
        all_action = QAction("清理所有记录", self)
        all_action.triggered.connect(lambda: self.do_clear_records(None))
        menu.addAction(all_action)
        
        menu.addSeparator()
        
        # 清理一周前的记录
        week_action = QAction("清理一周前的记录", self)
        week_action.triggered.connect(lambda: self.do_clear_records(7))
        menu.addAction(week_action)
        
        # 清理一个月前的记录
        month_action = QAction("清理一个月前的记录", self)
        month_action.triggered.connect(lambda: self.do_clear_records(30))
        menu.addAction(month_action)
        
        # 显示菜单
        menu.exec_(self.clear_button.mapToGlobal(
            self.clear_button.rect().bottomLeft()
        ))
    
    def do_clear_records(self, days: Optional[int] = None):
        """
        执行清理记录
        
        Args:
            days: 保留最近几天的记录，如果为None则清理所有记录
        """
        # 确认清理
        msg = "确定要清理"
        if days is None:
            msg += "所有记录"
        else:
            msg += f"{days}天前的记录"
        msg += "吗？"
        
        reply = QMessageBox.question(
            self, "确认清理", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 执行清理
        count = history_manager.clear_records(days)
        
        # 刷新显示
        self.refresh_records()
        
        QMessageBox.information(self, "清理完成", f"已清理 {count} 条记录")
