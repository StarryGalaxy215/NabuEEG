import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QComboBox, QApplication
)
from PyQt5.QtCore import Qt

# 尝试导入样式，若失败则使用空值
try:
    from common.styles import BTN_SUCCESS_8, BTN_DANGER_8, LABEL_BOLD_INFO
except ImportError:
    BTN_SUCCESS_8 = BTN_DANGER_8 = LABEL_BOLD_INFO = ""

# 标准 10-20 系统通道名称
STANDARD_1020_CHANNELS = [
    'Fp1', 'Fp2', 'F7', 'F3', 'Fz', 'F4', 'F8', 'FC5', 'FC1', 'FC2', 'FC6', 
    'T3', 'C3', 'Cz', 'C4', 'T4', 'CP5', 'CP1', 'CP2', 'CP6', 'T5', 'P3', 
    'Pz', 'P4', 'T6', 'O1', 'O2', 'AF7', 'AF3', 'AFz', 'AF4', 'AF8', 'F5', 
    'F1', 'F2', 'F6', 'FT7', 'FT8', 'C5', 'C1', 'C2', 'C6', 'TP7', 'TP8', 
    'P5', 'P1', 'P2', 'P6', 'PO7', 'PO3', 'POz', 'PO4', 'PO8', 'Iz'
]

class ChannelRenameDialog(QDialog):
    """通道重命名对话框"""
    def __init__(self, channels, parent=None):
        super().__init__(parent)
        self.setWindowTitle("更改通道名称")
        self.resize(500, 600)
        self.original_channels = channels
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 提示标签
        info_label = QLabel("请在下表中修改通道名称：")
        if LABEL_BOLD_INFO: info_label.setStyleSheet(LABEL_BOLD_INFO)
        layout.addWidget(info_label)
        
        # 表格配置
        self.table = QTableWidget(len(self.original_channels), 2)
        self.table.setHorizontalHeaderLabels(["原始名称", "新名称"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 填充表格
        for i, name in enumerate(self.original_channels):
            # 原始名称（只读）
            item_orig = QTableWidgetItem(str(name))
            item_orig.setFlags(item_orig.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, item_orig)
            
            # 新名称（下拉框）
            combo = QComboBox()
            combo.setEditable(True)
            combo.addItems(STANDARD_1020_CHANNELS)
            combo.setCurrentText(str(name))
            self.table.setCellWidget(i, 1, combo)
            
        layout.addWidget(self.table)
        
        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("保存更改")
        if BTN_SUCCESS_8: self.save_btn.setStyleSheet(BTN_SUCCESS_8)
        self.save_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("取消")
        if BTN_DANGER_8: self.cancel_btn.setStyleSheet(BTN_DANGER_8)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def get_new_channels(self):
        """获取修改后的通道列表"""
        new_channels = []
        for i in range(self.table.rowCount()):
            widget = self.table.cellWidget(i, 1)
            new_channels.append(widget.currentText() if isinstance(widget, QComboBox) else "")
        return new_channels

def show_channel_rename_dialog(parent=None):
    """显示通道重命名对话框的主流程"""
    # 1. 选择文件
    file_path, _ = QFileDialog.getOpenFileName(
        parent, "选择要修改的EEG数据文件", "", "Data Files (*.csv *.xlsx *.xls)"
    )
    if not file_path: return

    try:
        # 2. 读取文件
        df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
        columns = df.columns.tolist()
        
        # 3. 显示对话框
        dialog = ChannelRenameDialog(columns, parent)
        if dialog.exec_() != QDialog.Accepted: return
            
        new_channels = dialog.get_new_channels()
        if new_channels == columns:
            QMessageBox.information(parent, "提示", "未做任何修改")
            return
            
        # 4. 保存文件
        save_path, _ = QFileDialog.getSaveFileName(
            parent, "保存修改后的文件", file_path, "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        
        if save_path:
            df.columns = new_channels
            if save_path.endswith('.csv'):
                df.to_csv(save_path, index=False)
            else:
                df.to_excel(save_path, index=False)
            QMessageBox.information(parent, "成功", f"文件已保存至:\n{save_path}")
                
    except Exception as e:
        QMessageBox.critical(parent, "错误", f"处理文件时发生错误:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    show_channel_rename_dialog()
    sys.exit(app.exec_())
