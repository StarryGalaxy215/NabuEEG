import os
from typing import cast
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch
from PyQt5.QtWidgets import (QMessageBox, QFileDialog, QDialog, QVBoxLayout, 
                            QHBoxLayout, QListWidget, QPushButton, QLabel, 
                            QTableWidget, QTableWidgetItem, QHeaderView, 
                            QDoubleSpinBox, QGroupBox, QSpinBox)
from PyQt5.QtCore import Qt

from common.styles import (
    LABEL_BOLD_INFO,
    BTN_SUCCESS_8,
    BTN_WARNING_8,
    BTN_PRIMARY_8,
    BTN_DANGER_8,
)

class ChannelFilterDialog(QDialog):
    def __init__(self, channel_names, parent=None):
        super().__init__(parent)
        self.channel_names = channel_names
        self.filter_settings = {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("通道滤波器设置")
        self.setGeometry(300, 200, 800, 500)
        
        layout = QVBoxLayout()
        
        info_label = QLabel("请为每个通道设置滤波器参数：\n"
                          "• 带通滤波：低频和高频截止频率\n"
                          "• 陷波滤波：中心频率和品质因数Q")
        info_label.setStyleSheet(LABEL_BOLD_INFO)
        layout.addWidget(info_label)
        
        self.create_filter_table(layout)
        
        button_layout = QHBoxLayout()
        
        apply_all_btn = QPushButton("应用到所有通道")
        apply_all_btn.clicked.connect(self.apply_to_all_channels)
        apply_all_btn.setStyleSheet(BTN_SUCCESS_8)
        
        reset_btn = QPushButton("重置为默认值")
        reset_btn.clicked.connect(self.reset_to_defaults)
        reset_btn.setStyleSheet(BTN_WARNING_8)
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(BTN_PRIMARY_8)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(BTN_DANGER_8)
        
        button_layout.addWidget(apply_all_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.reset_to_defaults()
    
    def create_filter_table(self, layout):
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels([
            "通道名称", "带通低频(Hz)", "带通高频(Hz)", 
            "陷波频率(Hz)", "品质因数Q"
        ])
        
        self.table_widget.setRowCount(len(self.channel_names))
        
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        for row, channel in enumerate(self.channel_names):
            channel_item = QTableWidgetItem(channel)
            channel_item.setFlags(channel_item.flags() & ~Qt.ItemIsEditable)
            self.table_widget.setItem(row, 0, channel_item)
            
            low_spin = QDoubleSpinBox()
            low_spin.setRange(0.1, 10.0)
            low_spin.setValue(1.0)
            low_spin.setSingleStep(0.01)
            low_spin.setSuffix(" Hz")
            self.table_widget.setCellWidget(row, 1, low_spin)
            
            high_spin = QDoubleSpinBox()
            high_spin.setRange(10.0, 100.0)
            high_spin.setValue(45.0)
            high_spin.setSingleStep(0.01)
            high_spin.setSuffix(" Hz")
            self.table_widget.setCellWidget(row, 2, high_spin)
            
            notch_spin = QDoubleSpinBox()
            notch_spin.setRange(40.0, 60.0)
            notch_spin.setValue(50.0)
            notch_spin.setSingleStep(1.0)
            notch_spin.setSuffix(" Hz")
            self.table_widget.setCellWidget(row, 3, notch_spin)
            
            q_spin = QSpinBox()
            q_spin.setRange(10, 100)
            q_spin.setValue(30)
            q_spin.setSingleStep(1)
            self.table_widget.setCellWidget(row, 4, q_spin)
        
        layout.addWidget(self.table_widget)
    
    def apply_to_all_channels(self):
        if self.table_widget.rowCount() == 0:
            return
        
        low_spin = cast(QDoubleSpinBox, self.table_widget.cellWidget(0, 1))
        high_spin = cast(QDoubleSpinBox, self.table_widget.cellWidget(0, 2))
        notch_spin = cast(QDoubleSpinBox, self.table_widget.cellWidget(0, 3))
        q_spin = cast(QSpinBox, self.table_widget.cellWidget(0, 4))
        
        if not all([low_spin, high_spin, notch_spin, q_spin]):
            return
        
        low_val = low_spin.value()
        high_val = high_spin.value()
        notch_val = notch_spin.value()
        q_val = q_spin.value()
        
        for row in range(1, self.table_widget.rowCount()):
            low_spin_row = cast(QDoubleSpinBox, self.table_widget.cellWidget(row, 1))
            high_spin_row = cast(QDoubleSpinBox, self.table_widget.cellWidget(row, 2))
            notch_spin_row = cast(QDoubleSpinBox, self.table_widget.cellWidget(row, 3))
            q_spin_row = cast(QSpinBox, self.table_widget.cellWidget(row, 4))
            
            if all([low_spin_row, high_spin_row, notch_spin_row, q_spin_row]):
                low_spin_row.setValue(low_val)
                high_spin_row.setValue(high_val)
                notch_spin_row.setValue(notch_val)
                q_spin_row.setValue(q_val)
        
        QMessageBox.information(self, "成功", "设置已应用到所有通道！")
    
    def reset_to_defaults(self):
        for row in range(self.table_widget.rowCount()):
            low_spin = cast(QDoubleSpinBox, self.table_widget.cellWidget(row, 1))
            high_spin = cast(QDoubleSpinBox, self.table_widget.cellWidget(row, 2))
            notch_spin = cast(QDoubleSpinBox, self.table_widget.cellWidget(row, 3))
            q_spin = cast(QSpinBox, self.table_widget.cellWidget(row, 4))
            
            if all([low_spin, high_spin, notch_spin, q_spin]):
                low_spin.setValue(1.0)
                high_spin.setValue(50.0)
                notch_spin.setValue(50.0)
                q_spin.setValue(30)
    
    def get_filter_settings(self):
        settings = {}
        for row in range(self.table_widget.rowCount()):
            channel_item = self.table_widget.item(row, 0)
            if not channel_item:
                continue
                
            channel_name = channel_item.text()
            low_spin = cast(QDoubleSpinBox, self.table_widget.cellWidget(row, 1))
            high_spin = cast(QDoubleSpinBox, self.table_widget.cellWidget(row, 2))
            notch_spin = cast(QDoubleSpinBox, self.table_widget.cellWidget(row, 3))
            q_spin = cast(QSpinBox, self.table_widget.cellWidget(row, 4))
            
            if all([low_spin, high_spin, notch_spin, q_spin]):
                settings[channel_name] = {
                    'low_cutoff': low_spin.value(),
                    'high_cutoff': high_spin.value(),
                    'notch_freq': notch_spin.value(),
                    'q_factor': q_spin.value()
                }
        
        return settings

class EEGDataProcessor:
    def __init__(self, sampling_rate=250):
        self.sampling_rate = sampling_rate
        self.nyquist_freq = sampling_rate / 2
    
    def select_csv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "选择EEG数据CSV文件", "", "CSV文件 (*.csv);;所有文件 (*.*)"
        )
        return file_path if file_path else None
    
    def load_and_preprocess_data(self, file_path):
        try:
            # 使用Pandas读取CSV文件
            df = pd.read_csv(file_path)
            
            if df.shape[1] == 1:
                result = df.iloc[:, 0].astype(str).str.split(expand=True)
                n_samples = result.shape[0]
                for col in result.columns:
                    result[col] = pd.to_numeric(result[col], errors='coerce')
                time_column = np.arange(n_samples) / self.sampling_rate
                result.iloc[:, 0] = time_column
                column_names = ['time'] + [f'N{i}P' for i in range(1, result.shape[1])]
                result.columns = column_names
            else:
                result = df.copy()
                for col in result.columns:
                    if col != 'time':
                        result[col] = pd.to_numeric(result[col], errors='coerce')
                if 'time' not in result.columns:
                    n_samples = result.shape[0]
                    time_column = np.arange(n_samples) / self.sampling_rate
                    result.insert(0, 'time', time_column)
                column_names = result.columns.tolist()
            
            # 处理缺失值
            nan_count = result.isnull().sum().sum()
            if nan_count > 0:
                result = result.ffill().bfill()
            
            return result, column_names
        except Exception as e:
            QMessageBox.critical(None, "错误", f"数据加载错误: {str(e)}")
            return None, None
    
    def apply_custom_filters(self, data, filter_settings):
        """
        使用Numpy数组进行信号滤波处理
        """
        try:
            # 确保输入是Numpy数组
            if isinstance(data, pd.Series):
                data = data.values
            elif not isinstance(data, np.ndarray):
                data = np.array(data)
            
            # 数据类型检查和转换
            if data.dtype.kind not in 'biufc':
                data = data.astype(float)
            
            # 处理NaN值（使用 np.asarray 確保傳入標準 ndarray，解決與 nan_to_num 的型別相容性）
            if np.isnan(data).any():
                data = np.nan_to_num(np.asarray(data, dtype=float))
            
            # 数据长度检查
            if len(data) < 10:
                return data
            
            # 获取滤波器参数
            low_cutoff = filter_settings['low_cutoff']
            high_cutoff = filter_settings['high_cutoff']
            
            # 應用帶通濾波器（確保 nyquist_freq 有效且 butter 回傳值可迭代）
            if (self.nyquist_freq and self.nyquist_freq > 0 and 
                    low_cutoff < high_cutoff):
                coeffs = butter(4, 
                    [low_cutoff/self.nyquist_freq, high_cutoff/self.nyquist_freq], 
                    btype='band')
                if coeffs is not None and len(coeffs) == 2:
                    b_band, a_band = coeffs
                    filtered_data = filtfilt(b_band, a_band, data)
                else:
                    filtered_data = data.copy()
            else:
                filtered_data = data.copy()  # 使用copy避免修改原数据
            
            # 应用陷波滤波器
            notch_freq = filter_settings['notch_freq']
            q_factor = filter_settings['q_factor']
            
            if (self.nyquist_freq and 0 < notch_freq < self.nyquist_freq):
                coeffs_notch = iirnotch(notch_freq/self.nyquist_freq, q_factor)
                if coeffs_notch is not None and len(coeffs_notch) == 2:
                    b_notch, a_notch = coeffs_notch
                    filtered_data = filtfilt(b_notch, a_notch, filtered_data)
            
            return filtered_data
            
        except Exception as e:
            print(f"滤波错误: {e}")
            return data
    
    def process_data_with_custom_filters(self, data, selected_channels, filter_settings):
        """
        使用Numpy数组进行批量信号处理，提高效率
        """
        # 提取时间列
        time_data = data['time'].values
        
        # 创建结果数组
        n_samples = len(time_data)
        n_channels = len(selected_channels)
        
        # 预分配结果数组
        result_array = np.zeros((n_samples, n_channels + 1))
        result_array[:, 0] = time_data
        
        # 批量处理每个通道
        for i, channel in enumerate(selected_channels, 1):
            # 获取原始数据并转换为numpy数组
            original_data = data[channel].values
            
            # 获取该通道的滤波器设置
            channel_settings = filter_settings.get(channel, {
                'low_cutoff': 1.0,
                'high_cutoff': 50.0,
                'notch_freq': 50.0,
                'q_factor': 30
            })
            
            # 应用滤波器
            filtered_data = self.apply_custom_filters(original_data, channel_settings)
            result_array[:, i] = filtered_data
        
        # 将结果转换回DataFrame（仅用于输出）
        result_df = pd.DataFrame(result_array, columns=['time'] + selected_channels)
        return result_df
    
    def process_data_batch_optimized(self, data, selected_channels, filter_settings):
        """
        进一步优化的批量处理方法（可选）
        使用向量化操作处理多个通道
        """
        time_data = data['time'].values
        n_samples = len(time_data)
        
        # 预分配结果数组
        result_data = {'time': time_data}
        
        # 并行处理每个通道
        for channel in selected_channels:
            channel_data = data[channel].values
            channel_settings = filter_settings.get(channel, {
                'low_cutoff': 1.0, 'high_cutoff': 50.0, 
                'notch_freq': 50.0, 'q_factor': 30
            })
            
            # 应用滤波器
            filtered = self.apply_custom_filters(channel_data, channel_settings)
            result_data[channel] = filtered
        
        return pd.DataFrame(result_data)
    
    def save_results(self, processed_data, original_path, suffix="_custom_filtered"):
        try:
            # 使用Pandas保存结果
            file_dir = os.path.dirname(original_path)
            file_name = os.path.basename(original_path)
            file_base, file_ext = os.path.splitext(file_name)
            output_file = os.path.join(file_dir, f"{file_base}{suffix}{file_ext}")
            processed_data.to_csv(output_file, index=False)
            return output_file
        except Exception as e:
            print(f"保存结果错误: {e}")
            return None
    
    def extract_sample_data_for_display(self, data, channels, max_samples=1000):
        """
        提取用于显示的样本数据（使用Numpy数组操作）
        """
        display_data = {}
        
        for channel in channels:
            channel_data = data[channel].values
            n_samples = min(len(channel_data), max_samples)
            
            # 使用Numpy数组切片，提高效率
            display_data[channel] = channel_data[:n_samples]
        
        return display_data
    
    def run_preprocessing(self):
        return self.run_preprocessing_with_display()[0]
    
    def run_preprocessing_with_display(self):
        # 使用Pandas读取文件
        file_path = self.select_csv_file()
        if not file_path:
            return 1, None, None, None
        
        data, all_channels = self.load_and_preprocess_data(file_path)
        if data is None or all_channels is None or len(all_channels) < 2:
            return 1, None, None, None
        
        # 通道选择对话框
        channel_dialog = QDialog()
        channel_dialog.setWindowTitle("选择要处理的通道")
        channel_dialog.setGeometry(300, 300, 400, 300)
        layout = QVBoxLayout()
        
        label = QLabel(f"可用通道: {', '.join(all_channels[1:])}")
        layout.addWidget(label)
        
        channel_list = QListWidget()
        channel_list.addItems(all_channels[1:])
        channel_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(channel_list)
        
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(channel_list.selectAll)
        deselect_all_btn = QPushButton("全不选")
        deselect_all_btn.clicked.connect(channel_list.clearSelection)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        layout.addLayout(btn_layout)
        
        selected_channels = []
        def accept_selection():
            nonlocal selected_channels
            selected_items = channel_list.selectedItems()
            selected_channels = [item.text() for item in selected_items]
            if selected_channels:
                channel_dialog.accept()
            else:
                QMessageBox.warning(channel_dialog, "警告", "请至少选择一个通道")
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(accept_selection)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(channel_dialog.reject)
        btn_layout2 = QHBoxLayout()
        btn_layout2.addWidget(ok_btn)
        btn_layout2.addWidget(cancel_btn)
        layout.addLayout(btn_layout2)
        
        channel_dialog.setLayout(layout)
        
        if channel_dialog.exec_() != QDialog.Accepted:
            return 1, None, None, None
        
        if not selected_channels:
            QMessageBox.warning(None, "警告", "未选择任何通道")
            return 1, None, None, None
        
        # 滤波器设置对话框
        filter_dialog = ChannelFilterDialog(selected_channels)
        if filter_dialog.exec_() != QDialog.Accepted:
            return 1, None, None, None
        
        filter_settings = filter_dialog.get_filter_settings()
        
        # 使用优化的Numpy处理
        processed_data = self.process_data_with_custom_filters(data, selected_channels, filter_settings)
        result_file = self.save_results(processed_data, file_path)
        
        # 提取显示数据（使用Numpy数组操作）
        display_data = None
        if len(selected_channels) > 0:
            display_data = self.extract_sample_data_for_display(
                data, selected_channels[:1], max_samples=1000
            )
            # 添加滤波后的数据用于对比
            filtered_display = self.extract_sample_data_for_display(
                processed_data, selected_channels[:1], max_samples=1000
            )
            
            first_channel = selected_channels[0]
            display_data = {
                'original': display_data[first_channel],
                'filtered': filtered_display[first_channel],
                'channel': first_channel
            }
        
        if result_file:
            settings_report = self.generate_filter_report(filter_settings, selected_channels)
            
            QMessageBox.information(None, "处理完成", 
                f"数据处理完成！\n"
                f"输出文件: {os.path.basename(result_file)}\n"
                f"处理通道数: {len(selected_channels)}\n\n"
                f"滤波器设置:\n{settings_report}")
            
            file_info = f"{os.path.basename(file_path)} → {os.path.basename(result_file)}"
            return 0, file_info, len(selected_channels), display_data
        return 1, None, None, None
    
    def generate_filter_report(self, filter_settings, channels):
        report = ""
        for channel in channels:
            settings = filter_settings.get(channel, {})
            report += (f"{channel}: 带通[{settings.get('low_cutoff', 1.0)}-"
                      f"{settings.get('high_cutoff', 50.0)}]Hz, "
                      f"陷波{settings.get('notch_freq', 50.0)}Hz "
                      f"(Q={settings.get('q_factor', 30)})\n")
        return report