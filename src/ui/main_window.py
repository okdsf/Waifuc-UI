import os
import sys
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QStatusBar, QAction, QToolBar,
    QFileDialog, QMessageBox, QDockWidget, QListWidget, QTreeWidget, 
    QTreeWidgetItem, QSplitter, QFrame, QMenu
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QFont

from .workflow_designer import WorkflowDesignerWidget
from .source_selector import SourceSelectorWidget
from .history_view import HistoryViewWidget

class MainWindow(QMainWindow):
    """
    应用程序主窗口
    """
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("图像处理工具")
        self.setMinimumSize(1200, 800)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建选项卡部件
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # 初始化选项卡
        self.init_tabs()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 创建工具栏
        self.init_toolbar()
        
        # 创建数据源选择器侧边栏
        self.init_source_dock()
        
        # 创建历史记录侧边栏
        self.init_history_dock()
        
        # 创建菜单
        self.init_menu()
        
        # 加载设置
        self.load_settings()
    
    def init_tabs(self):
        """初始化选项卡"""
        # 创建工作流设计器选项卡
        self.workflow_designer = WorkflowDesignerWidget()
        self.tabs.addTab(self.workflow_designer, "工作流设计器")
        
        # 任务执行选项卡将在执行时动态添加
    
    def init_toolbar(self):
        """初始化工具栏"""
        self.toolbar = QToolBar("主工具栏")
        self.toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        
        # 新建工作流
        self.action_new_workflow = QAction("新建工作流", self)
        self.action_new_workflow.triggered.connect(self.on_new_workflow)
        self.toolbar.addAction(self.action_new_workflow)
        
        # 打开工作流
        self.action_open_workflow = QAction("打开工作流", self)
        self.action_open_workflow.triggered.connect(self.on_open_workflow)
        self.toolbar.addAction(self.action_open_workflow)
        
        # 保存工作流
        self.action_save_workflow = QAction("保存工作流", self)
        self.action_save_workflow.triggered.connect(self.on_save_workflow)
        self.toolbar.addAction(self.action_save_workflow)
        
        self.toolbar.addSeparator()
        
        # 运行工作流
        self.action_run_workflow = QAction("运行工作流", self)
        self.action_run_workflow.triggered.connect(self.on_run_workflow)
        self.toolbar.addAction(self.action_run_workflow)
        
        # 停止工作流
        self.action_stop_workflow = QAction("停止工作流", self)
        self.action_stop_workflow.triggered.connect(self.on_stop_workflow)
        self.action_stop_workflow.setEnabled(False)
        self.toolbar.addAction(self.action_stop_workflow)
        
        # 添加“查看组件说明”按钮
        self.action_view_components = QAction("查看组件说明", self)
        self.action_view_components.triggered.connect(self.show_component_list)
        self.toolbar.addAction(self.action_view_components)
    
    def init_menu(self):
        """初始化菜单"""
        # 文件菜单
        file_menu = self.menuBar().addMenu("文件")
        
        file_menu.addAction(self.action_new_workflow)
        file_menu.addAction(self.action_open_workflow)
        file_menu.addAction(self.action_save_workflow)
        file_menu.addSeparator()
        
        # 导入/导出工作流
        self.action_export_workflow = QAction("导出工作流...", self)
        self.action_export_workflow.triggered.connect(self.on_export_workflow)
        file_menu.addAction(self.action_export_workflow)
        
        self.action_import_workflow = QAction("导入工作流...", self)
        self.action_import_workflow.triggered.connect(self.on_import_workflow)
        file_menu.addAction(self.action_import_workflow)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = self.menuBar().addMenu("工具")
        
        # 运行工作流
        tools_menu.addAction(self.action_run_workflow)
        tools_menu.addAction(self.action_stop_workflow)
        tools_menu.addSeparator()
        
        # 设置
        settings_action = QAction("设置...", self)
        settings_action.triggered.connect(self.on_open_settings)
        tools_menu.addAction(settings_action)
        
        # 视图菜单
        view_menu = self.menuBar().addMenu("视图")
        
        # 源选择器
        self.action_toggle_source_dock = self.source_dock.toggleViewAction()
        self.action_toggle_source_dock.setText("数据源选择器")
        view_menu.addAction(self.action_toggle_source_dock)
        
        # 历史记录
        self.action_toggle_history_dock = self.history_dock.toggleViewAction()
        self.action_toggle_history_dock.setText("历史记录")
        view_menu.addAction(self.action_toggle_history_dock)
        
        # 帮助菜单
        help_menu = self.menuBar().addMenu("帮助")
        
        # 关于
        about_action = QAction("关于...", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
        
        # 帮助
        help_action = QAction("帮助文档", self)
        help_action.triggered.connect(self.on_help)
        help_menu.addAction(help_action)
    
    def init_source_dock(self):
        """初始化数据源选择器侧边栏"""
        self.source_dock = QDockWidget("数据源选择器", self)
        self.source_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.source_selector = SourceSelectorWidget()
        self.source_dock.setWidget(self.source_selector)
        
        self.addDockWidget(Qt.LeftDockWidgetArea, self.source_dock)
        
        # 连接信号
        self.source_selector.source_selected.connect(self.on_source_selected)
    
    def init_history_dock(self):
        """初始化历史记录侧边栏"""
        self.history_dock = QDockWidget("历史记录", self)
        self.history_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.history_view = HistoryViewWidget()
        self.history_dock.setWidget(self.history_view)
        
        self.addDockWidget(Qt.RightDockWidgetArea, self.history_dock)
        
        # 连接信号
        self.history_view.record_selected.connect(self.on_history_record_selected)
    
    def load_settings(self):
        """加载应用程序设置"""
        settings = QSettings("ImageProcessor", "MainWindow")
        
        # 加载窗口状态
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        
        if settings.contains("windowState"):
            self.restoreState(settings.value("windowState"))
    
    def save_settings(self):
        """保存应用程序设置"""
        settings = QSettings("ImageProcessor", "MainWindow")
        
        # 保存窗口状态
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存设置
        self.save_settings()
        
        # 确认是否退出
        reply = QMessageBox.question(
            self, "确认退出", "确定要退出吗？未保存的工作流将丢失。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    
    # 槽函数
    def on_new_workflow(self):
        """新建工作流"""
        self.workflow_designer.create_new_workflow()
    
    def on_open_workflow(self):
        """打开工作流"""
        self.workflow_designer.open_workflow_dialog()
    
    def on_save_workflow(self):
        """保存工作流"""
        self.workflow_designer.save_workflow()
    
    def on_export_workflow(self):
        """导出工作流"""
        self.workflow_designer.export_workflow_dialog()
    
    def on_import_workflow(self):
        """导入工作流"""
        self.workflow_designer.import_workflow_dialog()
    
    def on_run_workflow(self):
        """运行工作流"""
        # 获取当前工作流
        workflow = self.workflow_designer.get_current_workflow()
        if workflow is None:
            QMessageBox.warning(self, "错误", "没有可运行的工作流，请先创建或打开工作流。")
            return
        
        # 获取数据源
        source_type, source_params = self.source_selector.get_selected_source()
        if source_type is None:
            QMessageBox.warning(self, "错误", "请先选择数据源。")
            return
        
        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录", os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not output_dir:
            return
        
        # 创建并显示任务执行选项卡
        from .task_execution import TaskExecutionWidget
        task_widget = TaskExecutionWidget(workflow, source_type, source_params, output_dir)
        
        # 添加到选项卡并切换
        tab_index = self.tabs.addTab(task_widget, f"任务: {workflow.name}")
        self.tabs.setCurrentIndex(tab_index)
        
        # 连接完成信号
        task_widget.task_finished.connect(self.on_task_finished)
        task_widget.task_started.connect(self.on_task_started)
        
        # 启动任务
        task_widget.start_task()
    
    def on_stop_workflow(self):
        """停止工作流"""
        current_tab = self.tabs.currentWidget()
        
        from .task_execution import TaskExecutionWidget
        if isinstance(current_tab, TaskExecutionWidget):
            current_tab.stop_task()
    
    def on_task_started(self):
        """任务开始时的处理"""
        self.action_stop_workflow.setEnabled(True)
    
    def on_task_finished(self, success: bool, message: str):
        """任务完成时的处理"""
        self.action_stop_workflow.setEnabled(False)
        
        if success:
            self.status_bar.showMessage(f"任务完成: {message}")
        else:
            self.status_bar.showMessage(f"任务失败: {message}")
        
        # 刷新历史记录视图
        self.history_view.refresh_records()
    
    def on_open_settings(self):
        """打开设置对话框"""
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec_():
            # 应用设置
            pass
    
    def on_source_selected(self, source_type: str, source_params: Dict[str, Any]):
        """数据源选择事件处理"""
        self.status_bar.showMessage(f"已选择数据源: {source_type}")
    
    def on_history_record_selected(self, record_id: str):
        """历史记录选择事件处理"""
        # 显示执行记录详情
        from src.data import history_manager
        record = history_manager.get_record(record_id)
        
        if record:
            self.status_bar.showMessage(f"历史记录: {record.workflow_name} ({record.start_time})")
            
            # 可以选择性地在此加载记录对应的工作流
            if record.workflow_id:
                self.workflow_designer.load_workflow(record.workflow_id)
    
    def on_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于图像处理工具",
            "图像处理工具 v1.0\n\n"
            "一个功能强大的图像处理和管理工具，基于waifuc库开发。\n\n"
            "© 2025 版权所有"
        )
    
    def on_help(self):
        """显示帮助文档"""
        # TODO: 实现帮助文档显示功能
        QMessageBox.information(
            self, "帮助文档",
            "帮助文档尚未实现，敬请期待。"
        )
    
    def show_component_list(self):
        """显示组件说明列表"""
        from .component_explorer import ComponentListDialog
        dialog = ComponentListDialog(self)
        dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())