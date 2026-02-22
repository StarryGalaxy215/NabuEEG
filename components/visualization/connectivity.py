import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import coherence

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QFileDialog, QMessageBox, QWidget, QGroupBox, QSpinBox, QDoubleSpinBox
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

class ConnectivityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("脑连接分析 (Connectivity Analysis)")
        self.resize(900, 800)
        self.data = None
        self.sampling_rate = 250
        
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
        
        # Threshold
        control_layout.addWidget(QLabel("相干性阈值:"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.0, 1.0)
        self.threshold_spin.setSingleStep(0.1)
        self.threshold_spin.setValue(0.5)
        control_layout.addWidget(self.threshold_spin)
        
        # Analyze Button
        self.analyze_btn = QPushButton("生成连接图")
        if BTN_SUCCESS_8:
            self.analyze_btn.setStyleSheet(BTN_SUCCESS_8)
        self.analyze_btn.clicked.connect(self.analyze)
        self.analyze_btn.setEnabled(False)
        control_layout.addWidget(self.analyze_btn)
        
        control_layout.addStretch()
        main_layout.addWidget(control_group)
        
        # Plot Area
        self.figure = Figure(figsize=(8, 8), dpi=100)
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
            
            if len(self.columns) < 2:
                QMessageBox.warning(self, "错误", "文件中至少需要2个数值通道才能进行连接分析")
                return
                
            self.analyze_btn.setEnabled(True)
            QMessageBox.information(self, "成功", f"成功加载文件: {os.path.basename(file_path)}\n包含 {len(self.columns)} 个通道")
            
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载文件: {str(e)}")

    def analyze(self):
        if self.data is None:
            return
            
        threshold = self.threshold_spin.value()
        n_channels = len(self.columns)
        
        if n_channels > 20:
             ret = QMessageBox.question(self, "通道过多", f"检测到 {n_channels} 个通道，计算可能较慢且显示拥挤。\n是否仅使用前20个通道?", 
                                        QMessageBox.Yes | QMessageBox.No)
             if ret == QMessageBox.Yes:
                 channels = self.columns[:20]
             else:
                 channels = self.columns
        else:
            channels = self.columns
            
        n_channels = len(channels)
        
        try:
            # Calculate Coherence Matrix
            coh_matrix = np.zeros((n_channels, n_channels))
            
            # This can be slow O(N^2), but acceptable for < 32 channels
            for i in range(n_channels):
                for j in range(i+1, n_channels):
                    sig1 = np.asarray(self.data[channels[i]].values, dtype=np.float64)
                    sig2 = np.asarray(self.data[channels[j]].values, dtype=np.float64)
                    
                    f, Cxy = coherence(sig1, sig2, fs=self.sampling_rate, nperseg=256)
                    # Average coherence over all frequencies (or specific band, here using mean)
                    mean_coh = np.mean(Cxy)
                    coh_matrix[i, j] = mean_coh
                    coh_matrix[j, i] = mean_coh
            
            # Plotting Circular Graph
            self.figure.clear()
            ax = self.figure.add_subplot(111, polar=True) # Use polar coordinates
            
            # Calculate angles for each channel
            angles = np.linspace(0, 2*np.pi, n_channels, endpoint=False)
            
            # Draw nodes
            ax.scatter(angles, np.ones(n_channels), s=100, c='blue', zorder=10)
            
            # Draw labels
            for angle, label in zip(angles, channels):
                ax.text(angle, 1.1, label, ha='center', va='center', fontsize=9)
            
            # Draw connections
            for i in range(n_channels):
                for j in range(i+1, n_channels):
                    coh = coh_matrix[i, j]
                    if coh > threshold:
                        # Draw line between i and j
                        # In polar plot, plotting a line between two points (theta1, r1) and (theta2, r2)
                        # draws a straight line if used correctly, or an arc?
                        # matplotlib polar plot connects points with straight lines in projection space (curved in cartesian)
                        # Wait, we want straight lines in cartesian sense (chords).
                        # Polar plot lines are arcs if we just plot(theta, r).
                        # Actually, plot([theta1, theta2], [1, 1]) draws a chord? No, it draws an arc segment.
                        
                        # Better to use Cartesian plot for chords, but Polar is easier for layout.
                        # Let's use Cartesian for drawing manually.
                        pass

            # Switching to Cartesian for easier chord drawing
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.set_aspect('equal')
            ax.axis('off')
            
            # Radius
            r = 1.0
            
            # Coordinates
            x = r * np.cos(angles)
            y = r * np.sin(angles)
            
            # Draw nodes
            ax.scatter(x, y, s=200, c='lightblue', edgecolors='blue', zorder=10)
            
            # Draw labels
            for i, label in enumerate(channels):
                # Offset label slightly outward
                lx = 1.15 * r * np.cos(angles[i])
                ly = 1.15 * r * np.sin(angles[i])
                ax.text(lx, ly, label, ha='center', va='center', fontsize=9, fontweight='bold')
                
            # Draw connections
            num_connections = 0
            for i in range(n_channels):
                for j in range(i+1, n_channels):
                    coh = coh_matrix[i, j]
                    if coh > threshold:
                        # Color based on strength (alpha)
                        alpha = (coh - threshold) / (1.0 - threshold)
                        alpha = max(0.1, min(1.0, alpha)) # Clamp
                        
                        ax.plot([x[i], x[j]], [y[i], y[j]], 'k-', alpha=alpha, linewidth=1.5)
                        num_connections += 1
                        
            ax.set_title(f'脑连接图 (阈值 > {threshold}, 连接数: {num_connections})')
            
            # Add a legend for strength
            # Create a custom legend? 
            # Maybe just text
            ax.text(0, -1.3, f"线条透明度表示相干性强度\n总通道数: {n_channels}", ha='center')
            
            self.canvas.draw()
            
        except Exception as e:
            QMessageBox.critical(self, "分析失败", f"分析过程中发生错误: {str(e)}")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = ConnectivityDialog()
    dialog.show()
    sys.exit(app.exec_())
