import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QMessageBox, QFileDialog, QWidget,
                             QGroupBox, QSpinBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt

# 尝试导入MNE库
try:
    import mne
    MNE_AVAILABLE = True
except ImportError:
    MNE_AVAILABLE = False

class TopoplotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("脑电地形图可视化 (Topographic Map)")
        self.resize(1000, 750)
        self.parent_window = parent
        self.raw = None
        self.sfreq = 250  # 默认采样率
        
        # 定义频带
        self.bands = {
            'Delta (1-4 Hz)': (1, 4),
            'Theta (4-8 Hz)': (4, 8),
            'Alpha (8-13 Hz)': (8, 13),
            'Beta (13-30 Hz)': (13, 30),
            'Gamma (30-45 Hz)': (30, 45)
        }
        
        # 默认通道映射 (OpenBCI 8通道默认)
        self.channel_mapping = {
            0: 'Fp1', 1: 'Fp2',
            2: 'C3', 3: 'C4',
            4: 'P7', 5: 'P8',
            6: 'O1', 7: 'O2'
        }
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 顶部控制栏
        control_group = QGroupBox("控制面板")
        control_layout = QHBoxLayout(control_group)
        
        # 1. 数据加载
        load_btn = QPushButton("📂 加载CSV数据")
        load_btn.clicked.connect(self.load_data)
        load_btn.setStyleSheet("padding: 5px 10px; font-weight: bold;")
        control_layout.addWidget(load_btn)
        
        # 2. 频带选择
        control_layout.addWidget(QLabel("频带选择:"))
        self.band_combo = QComboBox()
        self.band_combo.addItems(self.bands.keys())
        self.band_combo.setCurrentText('Alpha (8-13 Hz)')
        control_layout.addWidget(self.band_combo)
        
        # 3. 绘图按钮
        self.plot_btn = QPushButton("🎨 生成地形图")
        self.plot_btn.clicked.connect(self.plot_topomap)
        self.plot_btn.setStyleSheet("background-color: #3498db; color: white; padding: 5px 15px; font-weight: bold;")
        self.plot_btn.setEnabled(False) # 初始禁用
        control_layout.addWidget(self.plot_btn)
        
        control_layout.addStretch()
        main_layout.addWidget(control_group)
        
        # 中间显示区域
        self.canvas_panel = QWidget()
        canvas_layout = QVBoxLayout(self.canvas_panel)
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        canvas_layout.addWidget(self.canvas)
        main_layout.addWidget(self.canvas_panel)
        
        # 底部状态栏
        self.status_label = QLabel("请加载数据以开始分析)")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        main_layout.addWidget(self.status_label)
        
        if not MNE_AVAILABLE:
            QMessageBox.warning(self, "缺少依赖", "检测到未安装 'mne' 库。\n脑电地形图功能需要该库才能运行。\n\n请运行: pip install mne")
            load_btn.setEnabled(False)
            self.plot_btn.setEnabled(False)
            self.status_label.setText("错误: 未安装 mne 库")

    def load_data(self):
        if not MNE_AVAILABLE:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择EEG数据CSV文件", "", "CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            # 读取CSV
            df = pd.read_csv(file_path)
            
            # 数据清洗与通道识别
            # 尝试查找标准通道名
            standard_channels = ['Fp1', 'Fp2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2', 'T5', 'T6', 'F3', 'F4', 'P3', 'P4', 'F7', 'F8', 'T3', 'T4']
            found_channels = [col for col in df.columns if col in standard_channels]
            
            data_cols = []
            ch_names = []
            
            if len(found_channels) >= 2:
                # 如果找到至少2个标准通道名，则使用这些列
                data_cols = found_channels
                ch_names = found_channels
                self.status_label.setText(f"自动识别通道: {', '.join(ch_names)}")
            else:
                # 否则假设前8列是数据 (排除 'time' 列)
                potential_cols = [c for c in df.columns if str(c).lower() != 'time' and 'timestamp' not in str(c).lower()]
                # 取前8个作为默认8通道
                limit = min(8, len(potential_cols))
                data_cols = potential_cols[:limit]
                # 使用默认映射命名
                ch_names = [self.channel_mapping.get(i, f"EEG{i+1}") for i in range(limit)]
                self.status_label.setText(f"使用默认映射通道: {', '.join(ch_names)}")
            
            if not data_cols:
                raise ValueError("无法识别有效的数据列")

            # 提取数据并转置 (n_channels, n_samples)
            data = df[data_cols].values.T
            
            # 单位转换: MNE期望单位是Volts (V)。OpenBCI通常是uV。
            # 如果数值很大 (>1)，假设是uV，转换为V
            if np.abs(data).max() > 1:
                 data = data * 1e-6
            
            # 创建MNE Raw对象
            info = mne.create_info(ch_names=ch_names, sfreq=self.sfreq, ch_types='eeg')
            self.raw = mne.io.RawArray(data, info)
            
            # 设置Montage (电极位置)
            # standard_1020 是最通用的
            try:
                montage = mne.channels.make_standard_montage('standard_1020')
                self.raw.set_montage(montage, on_missing='ignore') # 忽略找不到位置的通道
            except Exception as e:
                print(f"设置Montage警告: {e}")
                self.status_label.setText(self.status_label.text() + " (Montage设置部分失败)")
            
            self.plot_btn.setEnabled(True)
            self.status_label.setText(f"已加载: {os.path.basename(file_path)} | 通道: {len(ch_names)} | 采样点: {data.shape[1]}")
            
            # 自动绘图
            self.plot_topomap()
            
        except Exception as e:
            QMessageBox.critical(self, "加载错误", f"数据加载失败: {str(e)}")
            self.raw = None
            self.plot_btn.setEnabled(False)

    def plot_topomap(self):
        if not MNE_AVAILABLE or self.raw is None:
            return
            
        try:
            self.figure.clear()
            
            # 获取选定的频带
            band_name = self.band_combo.currentText()
            fmin, fmax = self.bands[band_name]
            
            # 计算PSD (Power Spectral Density)
            # 针对不同版本的MNE做兼容
            try:
                # 新版MNE (v1.0+)
                spectrum = self.raw.compute_psd(method='welch', fmin=fmin, fmax=fmax, verbose=False)
                psds, freqs = spectrum.get_data(return_freqs=True)
                # psds shape: (n_channels, n_freqs)
                # 对频带求平均
                psd_mean = np.mean(psds, axis=1)
                
            except AttributeError:
                # 旧版MNE
                from mne.time_frequency import psd_welch  # type: ignore
                psds, freqs = psd_welch(self.raw, fmin=fmin, fmax=fmax, n_fft=256, verbose=False)
                psd_mean = np.mean(psds, axis=1)
            except Exception as e:
                # 尝试通用方法
                from scipy.signal import welch
                data = self.raw.get_data()  # type: ignore
                # 确保data是数组
                if isinstance(data, np.ndarray):
                    nperseg = min(256, data.shape[-1])
                    freqs, psds = welch(data, fs=self.sfreq, nperseg=nperseg)
                    # 筛选频率
                    idx = np.logical_and(freqs >= fmin, freqs <= fmax)
                    if np.sum(idx) == 0:
                        raise ValueError(f"在 {fmin}-{fmax}Hz 范围内没有足够的数据点")
                    psd_mean = np.mean(psds[:, idx], axis=1)
                else:
                    raise ValueError("无法获取有效的EEG数据")

            # 绘制Topomap
            ax = self.figure.add_subplot(111)
            
            # 使用MNE的plot_topomap
            # 注意: MNE不同版本参数略有不同，通常是 data, pos
            # pos 可以是 info 对象
            im, _ = mne.viz.plot_topomap(
                psd_mean, 
                self.raw.info, 
                axes=ax, 
                show=False, 
                names=self.raw.ch_names,
                cmap='RdBu_r',
                sensors=True
            )
            
            # 添加Colorbar
            cbar = self.figure.colorbar(im, ax=ax, orientation='vertical', shrink=0.8)
            cbar.set_label('Power Spectral Density (V²/Hz)')
            
            ax.set_title(f"Topographic Map - {band_name}", fontsize=14, fontweight='bold')
            self.canvas.draw()
            
            self.status_label.setText(f"已生成 {band_name} 频带的地形图")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "绘图错误", f"生成地形图失败:\n{str(e)}")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dlg = TopoplotDialog()
    dlg.show()
    sys.exit(app.exec_())
