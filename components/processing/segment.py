import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpinBox, QDoubleSpinBox, QGroupBox, QRadioButton, QFileDialog, 
    QMessageBox, QWidget
)
from PyQt5.QtCore import Qt

from common.styles import (
    BTN_PRIMARY_8, BTN_SUCCESS_8, BTN_DANGER_8, BTN_WARNING_8,
    GROUP_BOX_MAIN, LABEL_BOLD_INFO, Colors
)
from typing import Any, cast

class SegmentDialog(QDialog):
    def __init__(self, data_processor=None, parent=None):
        super().__init__(parent)
        self.processor = data_processor
        self.data = None
        self.columns = None
        self.signal_data = np.empty((0, 0))
        self.time_col = np.empty((0,), dtype=float)
        self.fs = 250  # Default sampling rate
        self.init_ui()
        
        # If processor has data, load it
        if self.processor and hasattr(self.processor, 'df') and getattr(self.processor, 'df') is not None:
            self.load_from_processor()

    def init_ui(self):
        self.setWindowTitle("信号段处理 - NabuEEG")
        self.resize(900, 600)
        
        layout = QHBoxLayout()
        
        # --- Left Panel: Settings ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(300)
        
        # 1. Mode Selection
        gb_mode = QGroupBox("1. 截取模式")
        gb_mode.setStyleSheet(GROUP_BOX_MAIN)
        mode_layout = QVBoxLayout()
        
        self.rb_free = QRadioButton("自由截取 (Free)")
        self.rb_n45 = QRadioButton("N45 模式 (45ms)")
        self.rb_n100 = QRadioButton("N100 模式 (100ms)")
        
        self.rb_free.setChecked(True)
        
        self.rb_free.toggled.connect(self.on_mode_changed)
        self.rb_n45.toggled.connect(self.on_mode_changed)
        self.rb_n100.toggled.connect(self.on_mode_changed)
        
        mode_layout.addWidget(self.rb_free)
        mode_layout.addWidget(self.rb_n45)
        mode_layout.addWidget(self.rb_n100)
        gb_mode.setLayout(mode_layout)
        left_layout.addWidget(gb_mode)
        
        # 2. Time Settings
        gb_time = QGroupBox("2. 时间参数")
        gb_time.setStyleSheet(GROUP_BOX_MAIN)
        time_layout = QVBoxLayout()
        
        time_layout.addWidget(QLabel("起始时间 (s):"))
        self.spin_start = QDoubleSpinBox()
        self.spin_start.setRange(0, 3600)
        self.spin_start.setSingleStep(0.01)
        self.spin_start.setValue(0.0)
        self.spin_start.valueChanged.connect(self.update_plot_preview)
        time_layout.addWidget(self.spin_start)
        
        time_layout.addWidget(QLabel("结束时间 (s):"))
        self.spin_end = QDoubleSpinBox()
        self.spin_end.setRange(0, 3600)
        self.spin_end.setSingleStep(0.01)
        self.spin_end.setValue(1.0)
        self.spin_end.valueChanged.connect(self.update_plot_preview)
        time_layout.addWidget(self.spin_end)
        
        gb_time.setLayout(time_layout)
        left_layout.addWidget(gb_time)
        
        # 3. Actions
        gb_action = QGroupBox("3. 操作")
        gb_action.setStyleSheet(GROUP_BOX_MAIN)
        action_layout = QVBoxLayout()
        
        self.btn_load = QPushButton("加载文件")
        self.btn_load.clicked.connect(self.load_file)
        self.btn_load.setStyleSheet(BTN_PRIMARY_8)
        action_layout.addWidget(self.btn_load)
        
        self.btn_save = QPushButton("保存截取片段")
        self.btn_save.clicked.connect(self.save_segment)
        self.btn_save.setStyleSheet(BTN_SUCCESS_8)
        self.btn_save.setEnabled(False)
        action_layout.addWidget(self.btn_save)
        
        gb_action.setLayout(action_layout)
        left_layout.addWidget(gb_action)
        
        left_layout.addStretch()
        layout.addWidget(left_panel)
        
        # --- Right Panel: Plot ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        
        layout.addWidget(right_panel)
        
        self.setLayout(layout)
        
    def load_from_processor(self):
        try:
            if self.processor is None or not hasattr(self.processor, 'df') or getattr(self.processor, 'df') is None:
                return
            processor_df = cast(Any, getattr(self.processor, 'df'))
            self.data = processor_df.copy()
            # Try to handle 'time' column
            if 'time' in self.data.columns:
                self.time_col = np.asarray(self.data['time'].values, dtype=float)
                sig_df = self.data.drop(columns=['time']).apply(pd.to_numeric, errors='coerce')
                sig_df = sig_df.ffill().bfill()
                sig_df = sig_df.select_dtypes(include=[np.number])
                self.signal_data = sig_df.to_numpy(dtype=float)
                self.columns = sig_df.columns
            else:
                self.time_col = np.arange(len(self.data), dtype=float) / float(self.fs)
                sig_df = self.data.apply(pd.to_numeric, errors='coerce')
                sig_df = sig_df.ffill().bfill()
                sig_df = sig_df.select_dtypes(include=[np.number])
                self.signal_data = sig_df.to_numpy(dtype=float)
                self.columns = sig_df.columns
                
            self.spin_end.setValue(self.time_col[-1])
            self.spin_end.setMaximum(self.time_col[-1])
            self.spin_start.setMaximum(self.time_col[-1])
            
            self.update_plot()
            self.btn_save.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法从主程序加载数据: {e}")

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择EEG文件", "", "CSV Files (*.csv)")
        if file_path:
            try:
                self.data = pd.read_csv(file_path)
                # Simple logic same as above
                if 'time' in self.data.columns:
                    self.time_col = np.asarray(self.data['time'].values, dtype=float)
                    sig_df = self.data.drop(columns=['time']).apply(pd.to_numeric, errors='coerce')
                    sig_df = sig_df.ffill().bfill()
                    sig_df = sig_df.select_dtypes(include=[np.number])
                    self.signal_data = sig_df.to_numpy(dtype=float)
                    self.columns = sig_df.columns
                else:
                    self.time_col = np.arange(len(self.data), dtype=float) / float(self.fs)
                    sig_df = self.data.apply(pd.to_numeric, errors='coerce')
                    sig_df = sig_df.ffill().bfill()
                    sig_df = sig_df.select_dtypes(include=[np.number])
                    self.signal_data = sig_df.to_numpy(dtype=float)
                    self.columns = sig_df.columns

                self.spin_end.setValue(self.time_col[-1])
                self.spin_end.setMaximum(self.time_col[-1])
                self.spin_start.setMaximum(self.time_col[-1])
                
                self.update_plot()
                self.btn_save.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取文件失败: {e}")

    def on_mode_changed(self):
        if self.rb_free.isChecked():
            self.spin_start.setEnabled(True)
            self.spin_end.setEnabled(True)
            
        elif self.rb_n45.isChecked():
            # N45: Typically around 45ms. Let's set a window around it, e.g., 0-100ms
            self.spin_start.setEnabled(False)
            self.spin_end.setEnabled(False)
            self.spin_start.setValue(0.0)
            self.spin_end.setValue(0.1)  # 100ms window to cover N45
            
        elif self.rb_n100.isChecked():
            # N100: Typically around 100ms. Window e.g. 50ms-150ms? Or 0-200ms?
            # Let's use 0-300ms to be safe for N100
            self.spin_start.setEnabled(False)
            self.spin_end.setEnabled(False)
            self.spin_start.setValue(0.0)
            self.spin_end.setValue(0.3) 
            
        self.update_plot_preview()

    def update_plot(self):
        if self.data is None: 
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Plot only first channel to avoid clutter, or average?
        # Let's plot first valid channel
        if self.signal_data.ndim == 2 and self.signal_data.shape[1] > 0 and self.time_col.size > 0 and self.columns is not None and len(self.columns) > 0:
            ax.plot(self.time_col, self.signal_data[:, 0], label=f"Channel {self.columns[0]}")
            ax.set_title("EEG Signal (Channel 1 Preview)")
            ax.set_xlabel("Time (s)")
            ax.legend()
        
        self.canvas.draw()
        self.update_plot_preview()

    def update_plot_preview(self):
        if self.data is None:
            return
            
        # Highlight selected region
        start = self.spin_start.value()
        end = self.spin_end.value()
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if self.signal_data.ndim == 2 and self.signal_data.shape[1] > 0 and self.time_col.size > 0 and self.columns is not None and len(self.columns) > 0:
            ax.plot(self.time_col, self.signal_data[:, 0], color='#2c3e50', alpha=0.5, label="Original")
            
            # Find indices for segment
            mask = (self.time_col >= float(start)) & (self.time_col <= float(end))
            if np.any(mask):
                ax.plot(self.time_col[mask], self.signal_data[mask, 0], color='#e74c3c', label="Selected")
                
            ax.axvline(start, color='green', linestyle='--', alpha=0.7)
            ax.axvline(end, color='green', linestyle='--', alpha=0.7)
            
            ax.set_title(f"EEG Signal (Selected: {start:.3f}s - {end:.3f}s)")
            ax.set_xlabel("Time (s)")
            ax.legend()
            
        self.canvas.draw()

    def save_segment(self):
        if self.data is None:
            return
            
        start = self.spin_start.value()
        end = self.spin_end.value()
        
        mask = (self.time_col >= float(start)) & (self.time_col <= float(end))
        segment_time = self.time_col[mask]
        segment_data = self.signal_data[mask]
        
        if len(segment_time) == 0:
            QMessageBox.warning(self, "警告", "选定范围内没有数据！")
            return
            
        # Create DataFrame
        if self.columns is None or len(self.columns) == 0:
            return
        df_segment = pd.DataFrame(np.asarray(segment_data, dtype=float), columns=self.columns)
        df_segment.insert(0, 'time', segment_time)
        
        file_path, _ = QFileDialog.getSaveFileName(self, "保存片段", "segment.csv", "CSV Files (*.csv)")
        if file_path:
            try:
                df_segment.to_csv(file_path, index=False)
                QMessageBox.information(self, "成功", f"片段已保存至: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
