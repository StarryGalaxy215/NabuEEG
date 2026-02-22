import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from sklearn.decomposition import FastICA
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QMessageBox, QSpinBox, QCheckBox, QListWidget, 
    QListWidgetItem, QGroupBox, QSplitter, QWidget, QProgressDialog,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from common.styles import (
    BTN_PRIMARY_8, BTN_SUCCESS_8, BTN_DANGER_8, BTN_WARNING_8,
    GROUP_BOX_MAIN, LABEL_BOLD_INFO, Colors
)
from typing import cast, Literal

class ICAWorker(QThread):
    finished = pyqtSignal(object, object, object) # components, mixing_matrix, mean
    error = pyqtSignal(str)

    def __init__(self, data, n_components, algorithm='deflation'):
        super().__init__()
        self.data = data
        self.n_components = n_components
        self.algorithm = algorithm

    def run(self):
        try:
            # FastICA implementation
            ica = FastICA(n_components=self.n_components, algorithm=cast(Literal['parallel','deflation'], self.algorithm), random_state=42, max_iter=1000)
            components = ica.fit_transform(self.data)  # S = W * X
            mixing_matrix = ica.mixing_  # A
            mean = ica.mean_
            self.finished.emit(components, mixing_matrix, mean)
        except Exception as e:
            self.error.emit(str(e))

class ICAProcessor:
    def __init__(self):
        self.raw_data = None
        self.columns = None
        self.sampling_rate = 250
        self.ica_components = None
        self.mixing_matrix = None
        self.pca_mean = None
        self.n_samples = 0
        self.n_channels = 0
        self.file_path = None

    def load_data(self, file_path):
        try:
            self.file_path = file_path
            df = pd.read_csv(file_path)
            
            # Simple preprocessing to handle different CSV formats (similar to processor.py)
            if 'time' in df.columns:
                data_df = df.drop(columns=['time'])
            else:
                # Assuming first column might be time or index if not labeled, or just raw data
                # For safety, let's try to detect if the first column is monotonic (time)
                if df.shape[1] > 1 and df.iloc[:, 0].is_monotonic_increasing:
                     data_df = df.iloc[:, 1:]
                else:
                    data_df = df

            # Filter only numeric columns
            data_df = data_df.select_dtypes(include=[np.number])
            
            # Handle NaNs
            if data_df.isnull().sum().sum() > 0:
                data_df = data_df.ffill().bfill()

            self.columns = data_df.columns.tolist()
            self.raw_data = data_df.values
            self.n_samples, self.n_channels = self.raw_data.shape
            
            return True, f"Loaded {self.n_channels} channels, {self.n_samples} samples"
        except Exception as e:
            return False, str(e)

    def reconstruct_signal(self, excluded_components):
        """
        Reconstruct signal excluding specific components.
        X_clean = S_clean * A.T + mean
        """
        if self.ica_components is None or self.mixing_matrix is None:
            return None

        # Create a copy of components to modify
        components_clean = self.ica_components.copy()
        
        # Zero out excluded components
        for idx in excluded_components:
            if 0 <= idx < components_clean.shape[1]:
                components_clean[:, idx] = 0
        
        # Reconstruct
        reconstructed = np.dot(components_clean, self.mixing_matrix.T) + self.pca_mean
        return reconstructed

    def save_data(self, data, output_path):
        try:
            df = pd.DataFrame(data, columns=self.columns)
            # Add time column back if we want, for now just 0 to N/Fs
            time_col = np.arange(len(data)) / self.sampling_rate
            df.insert(0, 'time', time_col)
            df.to_csv(output_path, index=False)
            return True, "File saved successfully"
        except Exception as e:
            return False, str(e)

class ComponentPlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        vbox = QVBoxLayout(self)
        self.figure = Figure(figsize=(8, 2), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        vbox.addWidget(self.canvas)
        vbox.setContentsMargins(0, 0, 0, 0)
        self.ax = self.figure.add_subplot(111)
        self.figure.tight_layout()

    def plot_component(self, data, title, fs=250):
        self.ax.clear()
        time = np.arange(len(data)) / fs
        self.ax.plot(time, data, color='#2c3e50', linewidth=1)
        self.ax.set_title(title, fontsize=10)
        self.ax.set_ylabel('Amp', fontsize=8)
        self.ax.grid(True, linestyle='--', alpha=0.5)
        self.ax.margins(x=0)
        
        # Remove x ticks labels to save space if needed, or keep for context
        # self.ax.set_xticklabels([]) 
        
        self.canvas.draw()

class ICADialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.processor = ICAProcessor()
        self.excluded_components = set()
        self.component_widgets = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("独立成分分析 (ICA) - 去除伪迹")
        self.resize(1000, 800)
        
        main_layout = QHBoxLayout()

        # --- Left Panel: Controls ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_panel.setFixedWidth(300)

        # 1. File Selection
        gb_file = QGroupBox("1. 数据加载")
        gb_file.setStyleSheet(GROUP_BOX_MAIN)
        file_layout = QVBoxLayout()
        self.btn_load = QPushButton("选择EEG文件 (.csv)")
        self.btn_load.clicked.connect(self.load_file)
        self.btn_load.setStyleSheet(BTN_PRIMARY_8)
        self.lbl_file_info = QLabel("未加载文件")
        self.lbl_file_info.setWordWrap(True)
        file_layout.addWidget(self.btn_load)
        file_layout.addWidget(self.lbl_file_info)
        gb_file.setLayout(file_layout)
        left_layout.addWidget(gb_file)

        # 2. ICA Parameters
        gb_params = QGroupBox("2. ICA参数")
        gb_params.setStyleSheet(GROUP_BOX_MAIN)
        param_layout = QVBoxLayout()
        
        param_layout.addWidget(QLabel("分解成分数量:"))
        self.spin_components = QSpinBox()
        self.spin_components.setRange(2, 64)
        self.spin_components.setValue(8) # Default
        param_layout.addWidget(self.spin_components)
        
        self.btn_run_ica = QPushButton("运行 ICA 分解")
        self.btn_run_ica.clicked.connect(self.run_ica_decomposition)
        self.btn_run_ica.setStyleSheet(BTN_SUCCESS_8)
        self.btn_run_ica.setEnabled(False)
        param_layout.addWidget(self.btn_run_ica)
        
        # Component List for selection
        param_layout.addWidget(QLabel("选择要去除的成分 (伪迹):"))
        self.list_components = QListWidget()
        self.list_components.itemChanged.connect(self.on_component_selection_change)
        param_layout.addWidget(self.list_components)
        
        gb_params.setLayout(param_layout)
        left_layout.addWidget(gb_params)

        # 3. Output
        gb_output = QGroupBox("3. 结果输出")
        gb_output.setStyleSheet(GROUP_BOX_MAIN)
        out_layout = QVBoxLayout()
        
        self.btn_preview = QPushButton("预览重建信号")
        self.btn_preview.clicked.connect(self.preview_reconstruction)
        self.btn_preview.setStyleSheet(BTN_WARNING_8)
        self.btn_preview.setEnabled(False)
        out_layout.addWidget(self.btn_preview)
        
        self.btn_save = QPushButton("保存处理后数据")
        self.btn_save.clicked.connect(self.save_result)
        self.btn_save.setStyleSheet(BTN_SUCCESS_8)
        self.btn_save.setEnabled(False)
        out_layout.addWidget(self.btn_save)
        
        gb_output.setLayout(out_layout)
        left_layout.addWidget(gb_output)
        
        left_layout.addStretch()

        # --- Right Panel: Visualization ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.lbl_viz_title = QLabel("独立成分可视化")
        self.lbl_viz_title.setStyleSheet(LABEL_BOLD_INFO)
        right_layout.addWidget(self.lbl_viz_title)

        # Scroll area for components
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        
        right_layout.addWidget(self.scroll_area)

        # Splitter to adjust width
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择EEG数据CSV文件", "", "CSV文件 (*.csv);;所有文件 (*.*)"
        )
        if file_path:
            success, msg = self.processor.load_data(file_path)
            if success:
                self.lbl_file_info.setText(f"文件: {os.path.basename(file_path)}\n{msg}")
                self.btn_run_ica.setEnabled(True)
                # Set max components to number of channels
                self.spin_components.setMaximum(self.processor.n_channels)
                self.spin_components.setValue(min(self.processor.n_channels, 20)) # Cap default at 20
            else:
                QMessageBox.critical(self, "错误", f"无法加载文件: {msg}")

    def run_ica_decomposition(self):
        n_comp = self.spin_components.value()
        if n_comp > self.processor.n_channels:
            QMessageBox.warning(self, "警告", "主成分数量不能超过通道数量")
            return

        # Show progress
        self.progress = QProgressDialog("正在进行ICA分解 (FastICA)...", "取消", 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()

        # Threaded execution
        self.worker = ICAWorker(self.processor.raw_data, n_comp)
        self.worker.finished.connect(self.on_ica_finished)
        self.worker.error.connect(self.on_ica_error)
        self.worker.start()

    def on_ica_finished(self, components, mixing, mean):
        self.progress.close()
        self.processor.ica_components = components
        self.processor.mixing_matrix = mixing
        self.processor.pca_mean = mean
        
        self.update_component_list()
        self.visualize_components()
        
        self.btn_preview.setEnabled(True)
        self.btn_save.setEnabled(True)
        QMessageBox.information(self, "完成", "ICA分解完成！\n请在左侧勾选认为是伪迹（如眼动、肌电）的成分。")

    def on_ica_error(self, error_msg):
        self.progress.close()
        QMessageBox.critical(self, "ICA 错误", f"分解过程中发生错误:\n{error_msg}")

    def update_component_list(self):
        self.list_components.clear()
        if self.processor.ica_components is None:
            return
        n_comps = self.processor.ica_components.shape[1]
        for i in range(n_comps):
            item = QListWidgetItem(f"成分IC {i+1}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_components.addItem(item)

    def on_component_selection_change(self, item):
        idx = self.list_components.row(item)
        if item.checkState() == Qt.Checked:
            self.excluded_components.add(idx)
        else:
            self.excluded_components.discard(idx)

    def visualize_components(self):
        # Clear previous plots
        for i in reversed(range(self.scroll_layout.count())): 
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        if self.processor.ica_components is None:
            return
        components = self.processor.ica_components
        n_comps = components.shape[1]
        
        # Limit display if too many samples for performance
        display_samples = min(len(components), 2000)
        
        for i in range(n_comps):
            comp_data = components[:display_samples, i]
            
            # Create plot widget
            plot_widget = ComponentPlotWidget()
            plot_widget.plot_component(comp_data, f"Independent Component {i+1}")
            self.scroll_layout.addWidget(plot_widget)

    def preview_reconstruction(self):
        if not self.excluded_components:
            QMessageBox.information(self, "提示", "未选择任何要去除的成分，重建信号将与原始信号相同。")
        
        # New dialog for comparison
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("信号对比预览 (原始 vs 重建)")
        preview_dialog.resize(1000, 600)
        layout = QVBoxLayout(preview_dialog)
        
        # Reconstruct
        reconstructed = self.processor.reconstruct_signal(self.excluded_components)
        if reconstructed is None:
            return
        if self.processor.raw_data is None or self.processor.n_samples == 0:
            return
        
        # Plotting
        figure = Figure(figsize=(10, 6))
        canvas = FigureCanvas(figure)
        layout.addWidget(canvas)
        
        ax = figure.add_subplot(111)
        
        # Plot first channel as example
        display_samples = min(self.processor.n_samples, 1000)
        time = np.arange(display_samples) / self.processor.sampling_rate
        
        orig_data = self.processor.raw_data[:display_samples, 0]
        recon_data = reconstructed[:display_samples, 0]
        
        ax.plot(time, orig_data, label='原始信号 (通道1)', alpha=0.7)
        ax.plot(time, recon_data, label='ICA重建后 (通道1)', alpha=0.7, linestyle='--')
        ax.legend()
        ax.set_title(f"信号对比 (已去除成分: {list(self.excluded_components)})")
        ax.set_xlabel("Time (s)")
        
        preview_dialog.exec_()

    def save_result(self):
        output_file, _ = QFileDialog.getSaveFileName(
            self, "保存处理后数据", 
            self.processor.file_path.replace(".csv", "_ica_cleaned.csv") if self.processor.file_path else "eeg_ica_cleaned.csv",
            "CSV文件 (*.csv)"
        )
        
        if output_file:
            reconstructed = self.processor.reconstruct_signal(self.excluded_components)
            if reconstructed is None:
                QMessageBox.warning(self, "警告", "无法保存：重建数据为空")
                return
            success, msg = self.processor.save_data(reconstructed, output_file)
            if success:
                QMessageBox.information(self, "保存成功", f"文件已保存至:\n{output_file}")
            else:
                QMessageBox.critical(self, "保存失败", msg)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = ICADialog()
    window.show()
    sys.exit(app.exec_())
