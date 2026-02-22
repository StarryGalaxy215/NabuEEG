import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
try:
    import pywt  # type: ignore
except ImportError:
    pywt = None

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QFileDialog, QMessageBox, QWidget, QGroupBox, QSpinBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Import styles if available
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

class WaveletPacketDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("小波包分析")
        self.resize(900, 700)
        self.data = None
        self.columns = []
        self.sampling_rate = 250
        
        if pywt is None:
            QMessageBox.warning(self, "依赖缺失", "未检测到 PyWavelets 库，小波包分析功能不可用。\n请安装: pip install PyWavelets")
            self.setEnabled(False)
            return

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
        control_layout.addWidget(QLabel("通道:"))
        self.channel_combo = QComboBox()
        self.channel_combo.setMinimumWidth(100)
        control_layout.addWidget(self.channel_combo)
        
        # Wavelet Selection
        control_layout.addWidget(QLabel("小波基:"))
        self.wavelet_combo = QComboBox()
        self.wavelet_combo.addItems(['db4', 'db8', 'sym4', 'sym8', 'coif4', 'haar'])
        control_layout.addWidget(self.wavelet_combo)
        
        # Level Selection
        control_layout.addWidget(QLabel("层数:"))
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 8)
        self.level_spin.setValue(4)
        control_layout.addWidget(self.level_spin)
        
        # Analyze Button
        self.analyze_btn = QPushButton("分析")
        if BTN_SUCCESS_8:
            self.analyze_btn.setStyleSheet(BTN_SUCCESS_8)
        self.analyze_btn.clicked.connect(self.analyze)
        self.analyze_btn.setEnabled(False)
        control_layout.addWidget(self.analyze_btn)
        
        control_layout.addStretch()
        main_layout.addWidget(control_group)
        
        # Plot Area
        self.figure = Figure(figsize=(10, 8), dpi=100)
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
                self.data = pd.read_csv(file_path)
                
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
        if self.data is None or pywt is None:
            return
            
        channel = self.channel_combo.currentText()
        wavelet = self.wavelet_combo.currentText()
        level = self.level_spin.value()
        
        if not channel:
            return
            
        try:
            signal = self.data[channel].values
            # Explicitly convert to float64 numpy array to avoid type issues
            signal = np.asarray(signal, dtype=np.float64)
            
            # Remove DC offset
            signal = signal - np.mean(signal)
            
            # Wavelet Packet Decomposition
            wp = pywt.WaveletPacket(data=signal, wavelet=wavelet, mode='symmetric', maxlevel=level)
            
            # Calculate energy of each node at the specified level
            nodes = [node for node in wp.get_level(level, 'natural')]
            energy = [np.sum(n.data**2) for n in nodes]
            labels = [n.path for n in nodes]
            
            # Plotting
            self.figure.clear()
            
            # Plot 1: Original Signal
            ax1 = self.figure.add_subplot(211)
            time = np.arange(len(signal)) / self.sampling_rate
            ax1.plot(time, signal, label='原始信号', alpha=0.8, linewidth=0.8)
            ax1.set_title(f'原始信号 - {channel}')
            ax1.set_xlabel('时间 (s)')
            ax1.set_ylabel('幅值')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Energy Spectrum (Bar Chart)
            ax2 = self.figure.add_subplot(212)
            x_pos = np.arange(len(labels))
            ax2.bar(x_pos, energy, align='center', alpha=0.7, color='orange')
            ax2.set_xticks(x_pos)
            # If too many labels, simplify or rotate
            if len(labels) > 16:
                ax2.set_xticklabels([]) # Hide labels if too many
                ax2.set_xlabel(f'小波包节点 (层数 {level}, 共 {len(labels)} 个节点)')
            else:
                ax2.set_xticklabels(labels)
                ax2.set_xlabel('小波包节点')
            
            ax2.set_ylabel('能量')
            ax2.set_title(f'小波包能量谱 (Level {level}, {wavelet})')
            ax2.grid(True, alpha=0.3, axis='y')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            QMessageBox.critical(self, "分析失败", f"分析过程中发生错误: {str(e)}")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = WaveletPacketDialog()
    dialog.show()
    sys.exit(app.exec_())
