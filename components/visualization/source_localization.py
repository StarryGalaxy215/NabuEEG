import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

try:
    import mne
except ImportError:
    mne = None

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QFileDialog, QMessageBox, QWidget, QGroupBox, QSpinBox
)
from PyQt5.QtCore import Qt

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

class SourceLocalizationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("3D 源定位可视化 (Source Localization Visualization)")
        self.resize(1000, 800)
        self.data = None
        self.sampling_rate = 250
        
        if mne is None:
            QMessageBox.warning(self, "依赖缺失", "未检测到 mne 库，3D源定位功能不可用。\n请安装: pip install mne")
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
        
        # Frequency Band
        control_layout.addWidget(QLabel("频带:"))
        self.band_combo = QComboBox()
        self.band_combo.addItems(['Delta (1-4Hz)', 'Theta (4-8Hz)', 'Alpha (8-13Hz)', 'Beta (13-30Hz)', 'Gamma (30-50Hz)', 'Total Power'])
        self.band_combo.setCurrentText('Alpha (8-13Hz)')
        control_layout.addWidget(self.band_combo)
        
        # Analyze Button
        self.analyze_btn = QPushButton("生成3D可视化")
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
                
            # Filter for numeric columns
            self.columns = [col for col in self.data.columns if pd.api.types.is_numeric_dtype(self.data[col])]
            
            # Try to match with standard 10-20 channels
            standard_channels = ['Fp1', 'Fp2', 'F7', 'F3', 'Fz', 'F4', 'F8', 'T3', 'C3', 'Cz', 'C4', 'T4', 'T5', 'P3', 'Pz', 'P4', 'T6', 'O1', 'O2']
            self.valid_channels = [col for col in self.columns if col in standard_channels]
            
            if not self.valid_channels:
                QMessageBox.warning(self, "警告", "未检测到标准的10-20系统通道名称。\n请确保列名为标准通道名 (如 Fp1, C3, O1 等) 以便进行3D定位。")
                # Fallback to all numeric columns, but positions might be missing
                self.valid_channels = self.columns
            else:
                QMessageBox.information(self, "成功", f"成功加载文件: {os.path.basename(file_path)}\n识别到 {len(self.valid_channels)} 个标准通道: {', '.join(self.valid_channels)}")
            
            self.analyze_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载文件: {str(e)}")

    def get_band_power(self, signal, fs, band):
        from scipy.signal import welch
        f, Pxx = welch(signal, fs, nperseg=min(256, len(signal)))
        
        if band == 'Total Power':
            return np.sum(Pxx)
        
        # Parse band range
        if 'Delta' in band: fmin, fmax = 1, 4
        elif 'Theta' in band: fmin, fmax = 4, 8
        elif 'Alpha' in band: fmin, fmax = 8, 13
        elif 'Beta' in band: fmin, fmax = 13, 30
        elif 'Gamma' in band: fmin, fmax = 30, 50
        else: return np.sum(Pxx)
        
        idx = np.logical_and(f >= fmin, f <= fmax)
        return np.sum(Pxx[idx])

    def analyze(self):
        if self.data is None or mne is None:
            return
            
        band = self.band_combo.currentText()
        
        try:
            # Calculate power for each channel
            channel_powers = {}
            for ch in self.valid_channels:
                signal = self.data[ch].values
                signal = np.asarray(signal, dtype=np.float64)
                signal = signal - np.mean(signal)
                power = self.get_band_power(signal, self.sampling_rate, band)
                channel_powers[ch] = power
            
            # Get 3D positions
            montage = mne.channels.make_standard_montage('standard_1020')
            ch_pos = montage.get_positions()['ch_pos']
            
            xs, ys, zs, colors, labels = [], [], [], [], []
            
            # Normalize powers for coloring
            powers = list(channel_powers.values())
            if not powers:
                return
            max_power = max(powers) if max(powers) > 0 else 1
            min_power = min(powers)
            
            for ch, power in channel_powers.items():
                if ch in ch_pos:
                    pos = ch_pos[ch]
                    xs.append(pos[0])
                    ys.append(pos[1])
                    zs.append(pos[2])
                    
                    # Normalized color (simple heatmap logic)
                    norm_power = (power - min_power) / (max_power - min_power) if max_power > min_power else 0.5
                    cmap = plt.get_cmap('jet')
                    colors.append(cmap(norm_power))
                    labels.append(ch)
            
            if not xs:
                QMessageBox.warning(self, "错误", "无法匹配任何通道的3D位置。")
                return

            # Plotting
            self.figure.clear()
            ax = self.figure.add_subplot(111, projection='3d')
            
            # Scatter plot
            # Use zs as keyword argument to avoid type checker confusion
            sc = ax.scatter(xs, ys, zs=zs, c=colors, s=200, depthshade=True) # type: ignore
            
            # Add labels
            for i, label in enumerate(labels):
                ax.text(xs[i], ys[i], zs[i], label, fontsize=8)
                
            # Draw a simple head sphere approximation (wireframe)
            u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
            r = 0.095 # Approx radius in MNE standard montage (meters)
            x = r*np.cos(u)*np.sin(v)
            y = r*np.sin(u)*np.sin(v)
            z = r*np.cos(v)
            # Offset slightly to match positions roughly (MNE positions are around origin but fit a head shape)
            # Just plot a faint sphere for reference
            ax.plot_wireframe(x, y, z, color="gray", alpha=0.1)

            ax.set_title(f'3D 源定位可视化 - {band}')
            ax.set_xlabel('X (Right)')
            ax.set_ylabel('Y (Anterior)')
            ax.set_zlabel('Z (Superior)')
            
            # Add a colorbar
            sm = plt.cm.ScalarMappable(cmap='jet', norm=Normalize(vmin=min_power, vmax=max_power))
            sm.set_array([])
            self.figure.colorbar(sm, ax=ax, label='Power')
            
            self.canvas.draw()
            
        except Exception as e:
            QMessageBox.critical(self, "分析失败", f"分析过程中发生错误: {str(e)}")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = SourceLocalizationDialog()
    dialog.show()
    sys.exit(app.exec_())
