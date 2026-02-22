import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QFileDialog, QMessageBox, QWidget, QGroupBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Import styles if available, otherwise define fallbacks
try:
    from common.styles import (
        BTN_PRIMARY_8, BTN_SUCCESS_8, BTN_DANGER_8, 
        GROUP_BOX_MAIN, LABEL_BOLD_INFO
    )
except ImportError:
    BTN_PRIMARY_8 = ""
    BTN_SUCCESS_8 = ""
    BTN_DANGER_8 = ""
    GROUP_BOX_MAIN = ""
    LABEL_BOLD_INFO = ""

class HilbertEnvelopeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("希尔伯特包络分析")
        self.resize(800, 600)
        self.data = None
        self.columns = []
        self.sampling_rate = 250 # Default, could be inferred or set
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Control Panel
        control_group = QGroupBox("控制面板")
        if GROUP_BOX_MAIN:
            control_group.setStyleSheet(GROUP_BOX_MAIN)
        control_layout = QHBoxLayout(control_group)
        
        # File Selection
        self.file_btn = QPushButton("选择文件")
        if BTN_PRIMARY_8:
            self.file_btn.setStyleSheet(BTN_PRIMARY_8)
        self.file_btn.clicked.connect(self.load_file)
        control_layout.addWidget(self.file_btn)
        
        # Channel Selection
        self.channel_label = QLabel("选择通道:")
        if LABEL_BOLD_INFO:
            self.channel_label.setStyleSheet(LABEL_BOLD_INFO)
        control_layout.addWidget(self.channel_label)
        
        self.channel_combo = QComboBox()
        self.channel_combo.setMinimumWidth(150)
        control_layout.addWidget(self.channel_combo)
        
        # Analyze Button
        self.analyze_btn = QPushButton("生成包络")
        if BTN_SUCCESS_8:
            self.analyze_btn.setStyleSheet(BTN_SUCCESS_8)
        self.analyze_btn.clicked.connect(self.analyze)
        self.analyze_btn.setEnabled(False)
        control_layout.addWidget(self.analyze_btn)
        
        control_layout.addStretch()
        main_layout.addWidget(control_group)
        
        # Plot Area
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)
        
        # Close Button
        close_btn = QPushButton("关闭")
        if BTN_DANGER_8:
            close_btn.setStyleSheet(BTN_DANGER_8)
        close_btn.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        main_layout.addLayout(btn_layout)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择EEG数据文件", "", "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            if file_path.endswith('.csv'):
                self.data = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                self.data = pd.read_excel(file_path)
            else:
                # Try CSV as default
                self.data = pd.read_csv(file_path)
                
            # Filter for numeric columns only
            self.columns = [col for col in self.data.columns if pd.api.types.is_numeric_dtype(self.data[col])]
            
            if not self.columns:
                QMessageBox.warning(self, "错误", "文件中没有数值列")
                return
                
            self.channel_combo.clear()
            self.channel_combo.addItems(self.columns)
            self.analyze_btn.setEnabled(True)
            QMessageBox.information(self, "成功", f"成功加载文件: {os.path.basename(file_path)}\n包含 {len(self.columns)} 个数值通道")
            
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载文件: {str(e)}")

    def analyze(self):
        if self.data is None:
            return
            
        channel = self.channel_combo.currentText()
        if not channel:
            return
            
        try:
            signal = self.data[channel].values
            # Explicitly convert to float64 numpy array to avoid type issues
            signal = np.asarray(signal, dtype=np.float64)
            
            # Remove DC offset
            signal = signal - np.mean(signal)
            
            # Hilbert Transform
            analytic_signal = hilbert(signal)
            amplitude_envelope = np.abs(np.asarray(analytic_signal))
            
            # Plotting
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            time = np.arange(len(signal)) / self.sampling_rate
            
            ax.plot(time, signal, label='原始信号', alpha=0.7, linewidth=0.8)
            ax.plot(time, amplitude_envelope, label='希尔伯特包络', color='red', linewidth=1.5)
            
            ax.set_title(f'希尔伯特包络分析 - {channel}')
            ax.set_xlabel('时间 (s) [假设采样率 250Hz]')
            ax.set_ylabel('幅值')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            self.canvas.draw()
            
        except Exception as e:
            QMessageBox.critical(self, "分析失败", f"分析过程中发生错误: {str(e)}")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = HilbertEnvelopeDialog()
    dialog.show()
    sys.exit(app.exec_())
