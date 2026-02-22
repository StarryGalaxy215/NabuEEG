import sys
import os
from typing import Any, cast
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QFileDialog, QMessageBox, QWidget, QGroupBox,
    QDoubleSpinBox, QFormLayout, QCheckBox
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

class EPRDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("事件相关电位分析 (ERP/EPR)")
        self.resize(1000, 700)
        self.data = None
        self.columns = []
        self.sampling_rate = 250 # Default, could be inferred or set
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # --- Left Panel: Controls ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_panel.setFixedWidth(320)
        
        # 1. Data Loading
        gb_file = QGroupBox("1. 数据加载")
        if GROUP_BOX_MAIN: gb_file.setStyleSheet(GROUP_BOX_MAIN)
        file_layout = QVBoxLayout()
        
        self.file_btn = QPushButton("选择EEG数据文件")
        if BTN_PRIMARY_8: self.file_btn.setStyleSheet(BTN_PRIMARY_8)
        self.file_btn.clicked.connect(self.load_file)
        
        self.file_label = QLabel("未选择文件")
        self.file_label.setWordWrap(True)
        
        file_layout.addWidget(self.file_btn)
        file_layout.addWidget(self.file_label)
        gb_file.setLayout(file_layout)
        left_layout.addWidget(gb_file)
        
        # 2. Parameters
        gb_params = QGroupBox("2. 分析参数")
        if GROUP_BOX_MAIN: gb_params.setStyleSheet(GROUP_BOX_MAIN)
        param_layout = QFormLayout()
        
        # Channel Selection
        self.channel_combo = QComboBox()
        param_layout.addRow("分析通道:", self.channel_combo)
        
        # Trigger Selection
        self.trigger_combo = QComboBox()
        param_layout.addRow("触发(Marker)通道:", self.trigger_combo)
        
        # Threshold
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(-1000, 1000)
        self.threshold_spin.setValue(0.5)
        self.threshold_spin.setSingleStep(0.1)
        param_layout.addRow("触发阈值:", self.threshold_spin)
        
        # Epoch Window
        self.tmin_spin = QDoubleSpinBox()
        self.tmin_spin.setRange(-5.0, 0.0)
        self.tmin_spin.setValue(-0.2)
        self.tmin_spin.setSingleStep(0.1)
        param_layout.addRow("开始时间 (s):", self.tmin_spin)
        
        self.tmax_spin = QDoubleSpinBox()
        self.tmax_spin.setRange(0.0, 10.0)
        self.tmax_spin.setValue(0.8)
        self.tmax_spin.setSingleStep(0.1)
        param_layout.addRow("结束时间 (s):", self.tmax_spin)
        
        # Sampling Rate
        self.fs_spin = QDoubleSpinBox()
        self.fs_spin.setRange(1, 10000)
        self.fs_spin.setValue(250)
        self.fs_spin.setDecimals(0)
        param_layout.addRow("采样率 (Hz):", self.fs_spin)
        
        gb_params.setLayout(param_layout)
        left_layout.addWidget(gb_params)
        
        # 3. Action
        self.analyze_btn = QPushButton("生成 ERP 波形")
        if BTN_SUCCESS_8: self.analyze_btn.setStyleSheet(BTN_SUCCESS_8)
        self.analyze_btn.clicked.connect(self.analyze)
        self.analyze_btn.setEnabled(False)
        left_layout.addWidget(self.analyze_btn)
        
        left_layout.addStretch()
        
        # Close Button
        self.close_btn = QPushButton("关闭")
        if BTN_DANGER_8: self.close_btn.setStyleSheet(BTN_DANGER_8)
        self.close_btn.clicked.connect(self.accept)
        left_layout.addWidget(self.close_btn)
        
        main_layout.addWidget(left_panel)
        
        # --- Right Panel: Plot ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        
        main_layout.addWidget(right_panel)

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
                
            # Filter numeric columns
            self.columns = [col for col in self.data.columns if pd.api.types.is_numeric_dtype(self.data[col])]
            
            if not self.columns:
                QMessageBox.warning(self, "错误", "文件中没有数值列")
                return
                
            self.file_label.setText(os.path.basename(file_path))
            
            # Update Combos
            self.channel_combo.clear()
            self.channel_combo.addItems(self.columns)
            
            self.trigger_combo.clear()
            self.trigger_combo.addItem("自动检测 (无)", None)
            self.trigger_combo.addItems(self.columns)
            
            # Try to guess trigger channel
            for col in self.columns:
                if 'marker' in col.lower() or 'trig' in col.lower():
                    self.trigger_combo.setCurrentText(col)
                    break
            
            self.analyze_btn.setEnabled(True)
            QMessageBox.information(self, "成功", f"成功加载文件，包含 {len(self.columns)} 个通道")
            
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载文件: {str(e)}")

    def analyze(self):
        if self.data is None:
            return
            
        channel = self.channel_combo.currentText()
        trigger_ch = self.trigger_combo.currentText()
        
        if not channel:
            return
            
        fs = self.fs_spin.value()
        tmin = self.tmin_spin.value()
        tmax = self.tmax_spin.value()
        threshold = self.threshold_spin.value()
        
        try:
            # Ensure signal is numeric
            signal = np.array(pd.to_numeric(self.data[channel], errors='coerce'))
            if np.isnan(signal).any():
                # Handle NaNs if necessary, for now let's just warn or fill
                # signal = np.nan_to_num(signal) 
                pass
            
            # Find triggers
            events = []
            if trigger_ch and trigger_ch != "自动检测 (无)":
                # Ensure trigger signal is numeric
                trig_signal = np.array(pd.to_numeric(self.data[trigger_ch], errors='coerce'))
                
                # Simple thresholding: find rising edges
                # Ensure trigger signal is binary-ish or peaks
                # Find indices where signal crosses threshold
                # Using a simple method: finding where signal goes from < threshold to >= threshold
                
                # Create a boolean array for values above threshold
                above_threshold = (trig_signal >= float(threshold))
                
                # Diff to find rising edges. Convert bool to int (0/1) before diff
                diff = np.diff(above_threshold.astype(int))
                
                # Find where diff is 1 (0 -> 1 transition)
                events = np.where(diff == 1)[0] + 1
            else:
                # If no trigger channel, maybe generate dummy events or ask user
                # For now, let's just generate periodic events for demonstration if no trigger selected
                # But this is not real ERP. 
                # Better: Check if we can find peaks in the signal itself (not ideal for ERP but fallback)
                reply = QMessageBox.question(
                    self, "无触发通道", 
                    "未选择触发通道。是否每隔 1 秒生成一个模拟触发事件用于演示？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    events = np.arange(int(fs), len(signal) - int(fs), int(fs))
                else:
                    return

            if len(events) == 0:
                QMessageBox.warning(self, "警告", "未检测到任何触发事件 (Events)")
                return
                
            # Epoching
            n_samples_pre = int(abs(tmin) * fs)
            n_samples_post = int(tmax * fs)
            epoch_len = n_samples_pre + n_samples_post
            
            epochs = []
            valid_events = 0
            
            for event_idx in events:
                start_idx = event_idx - n_samples_pre
                end_idx = event_idx + n_samples_post
                
                if start_idx >= 0 and end_idx < len(signal):
                    epoch = signal[start_idx:end_idx]
                    
                    # Baseline correction (subtract mean of pre-stimulus interval)
                    if n_samples_pre > 0:
                        baseline = np.nanmean(np.asarray(epoch[:n_samples_pre]))
                        epoch = epoch - baseline
                    
                    epochs.append(epoch)
                    valid_events += 1
            
            if not epochs:
                QMessageBox.warning(self, "警告", "所有事件的 epoch 都超出了数据范围")
                return
                
            epochs_arr = np.array(epochs)
            
            # Averaging
            erp_mean = np.mean(epochs_arr, axis=0)
            erp_std = np.std(epochs_arr, axis=0)
            erp_sem = erp_std / np.sqrt(len(epochs)) # Standard Error of Mean
            
            # Time axis
            time = np.linspace(tmin, tmax, len(erp_mean))
            
            # Plotting
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Plot individual epochs (optional, maybe too messy if many)
            # for epoch in epochs:
            #     ax.plot(time, epoch, color='gray', alpha=0.1)
                
            # Plot Mean ERP
            ax.plot(time, erp_mean, label=f'Average ERP (N={valid_events})', color='#2980b9', linewidth=2)
            
            # Plot Confidence Interval (Mean +/- SEM)
            ax.fill_between(time, erp_mean - erp_sem, erp_mean + erp_sem, color='#2980b9', alpha=0.3, label='Standard Error')
            
            ax.axvline(x=0, color='k', linestyle='--', alpha=0.5, label='Stimulus Onset')
            ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            
            ax.set_title(f'Event-Related Potential (ERP) - {channel}')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude (uV)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Invert Y axis is common in ERP research, but let's stick to normal for now or make it optional
            # ax.invert_yaxis() 
            
            self.canvas.draw()
            
            QMessageBox.information(self, "分析完成", f"成功提取 {valid_events} 个 Epochs 并生成 ERP。")
            
        except Exception as e:
            QMessageBox.critical(self, "分析失败", f"ERP分析过程中发生错误: {str(e)}")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = EPRDialog()
    dialog.show()
    sys.exit(app.exec_())
