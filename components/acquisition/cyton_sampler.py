import os
import sys
import time
from typing import cast, Tuple
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QLineEdit, QFileDialog, QMessageBox, QGroupBox,
    QTextEdit, QSpinBox, QProgressBar, QCheckBox, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import pyqtgraph as pg
from scipy.signal import butter, lfilter, iirnotch

from common.styles import (
    BG_DIALOG,
    GROUP_BOX_SMALL,
    GROUP_BOX_CONFIG,
    COMBO_BOX_BASE,
    SPIN_BOX_BASE,
    LINE_EDIT_BASE,
    BTN_BLUE_SMALL,
    BTN_ORANGE_SMALL,
    BTN_GREEN_SMALL,
    BTN_RED_SMALL,
    BTN_GRAY_SMALL,
    BTN_START,
    BTN_PAUSE,
    BTN_STOP,
    FONT_SMALL_9PT,
    FONT_SMALL_9PT_PADDING,
    LABEL_BOLD_INFO,
    LABEL_FONT_BOLD,
    CONSOLE_STYLE,
    PROGRESS_BAR,
    HEADER_CYTON,
)

BRAINFLOW_AVAILABLE = False
SERIAL_AVAILABLE = False

try:
    import brainflow
    from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, LogLevels
    BRAINFLOW_AVAILABLE = True
    BoardShim.set_log_level(LogLevels.LEVEL_INFO)
except ImportError:
    print("警告: BrainFlow库未安装，将使用模拟模式")

try:
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    print("警告: 串口检测功能不可用，请安装pyserial库")

BOARD_CONFIG = {
    0: {"name": "Cyton", "rate": 250, "rows": 24, "channels": 8},
    1: {"name": "Cyton+Daisy", "rate": 125, "rows": 32, "channels": 16},
    2: {"name": "Ganglion", "rate": 200, "rows": 20, "channels": 4},
    -1: {"name": "Synthetic", "rate": 250, "rows": 24, "channels": 8}
}


class _FallbackBoardParams:
    """BrainFlow 未安裝時的參數佔位類，具備與 BrainFlowInputParams 相容的屬性。"""
    serial_port: str = ""
    mac_address: str = ""
    ip_address: str = ""
    ip_port: int = 8000


class FilterProcessor:
    @staticmethod
    def butter_bandpass(lowcut, highcut, fs, order=4):
        nyq = 0.5 * fs
        b, a = cast(
            Tuple[np.ndarray, np.ndarray],
            butter(order, [lowcut/nyq, highcut/nyq], btype='band'),
        )
        return b, a

    @staticmethod
    def notch_filter(notch_freq, fs, quality=30):
        b, a = cast(
            Tuple[np.ndarray, np.ndarray],
            iirnotch(notch_freq/(0.5*fs), quality),
        )
        return b, a

class SamplingThread(QThread):
    data_chunk_received = pyqtSignal(np.ndarray)
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    finished_sampling = pyqtSignal(np.ndarray, str, float)
    paused = pyqtSignal(bool)

    def __init__(self, board_id, params, duration, save_path):
        super().__init__()
        self.board_id = board_id
        self.params = params
        self.duration = duration
        self.save_path = save_path
        self.board_shim = None
        self.is_running = False
        self.is_paused = False
        self.actual_duration = 0.0
        self.data_buffer = []

    def run(self):
        if not BRAINFLOW_AVAILABLE or self.board_id == -1:
            self._run_synthetic()
            return

        try:
            board_config = BOARD_CONFIG.get(self.board_id, BOARD_CONFIG[-1])
            self.status_update.emit(f"正在初始化 {board_config['name']}...")

            self.board_shim = BoardShim(self.board_id, self.params)
            self.board_shim.prepare_session()
            self.board_shim.start_stream()

            self.status_update.emit(f"🚀 数据流已启动 ({board_config['rate']}Hz)")
            self.is_running = True

            start_time = time.time()
            last_progress = -1

            while self.is_running:
                if self.is_paused:
                    self.msleep(100)
                    continue
                    
                current_time = time.time()
                elapsed = current_time - start_time

                if elapsed >= self.duration:
                    break

                data = self._get_available_data()
                if data is not None and data.size > 0:
                    self.data_buffer.append(data)
                    self.data_chunk_received.emit(data)

                progress = int((elapsed / self.duration) * 100)
                if progress != last_progress:
                    self.progress_update.emit(progress)
                    last_progress = progress

                self.msleep(50)

            self.actual_duration = time.time() - start_time
            self._finalize_sampling(board_config['name'])

        except Exception as e:
            self.status_update.emit(f"❌ 通信错误: {str(e)}")
            self._safe_release_session()

    def _run_synthetic(self):
        self.status_update.emit("启动模拟信号发生器...")
        self.is_running = True

        board_config = BOARD_CONFIG.get(self.board_id, BOARD_CONFIG[-1])
        fs = board_config['rate']
        rows = board_config['rows']
        channels = board_config['channels']

        start_time = time.time()
        last_progress = -1
        sample_count = 0

        while self.is_running:
            if self.is_paused:
                self.msleep(100)
                continue
                
            current_time = time.time()
            elapsed = current_time - start_time

            if elapsed >= self.duration:
                break

            num_samples = 10
            synth_data = self._generate_synthetic_data(rows, num_samples, sample_count, fs)
            self.data_buffer.append(synth_data)
            self.data_chunk_received.emit(synth_data)
            sample_count += num_samples

            progress = int((elapsed / self.duration) * 100)
            if progress != last_progress:
                self.progress_update.emit(progress)
                last_progress = progress

            self.msleep(40)

        self.actual_duration = time.time() - start_time
        self._finalize_sampling("模拟合成数据", is_synthetic=True)

    def pause(self):
        self.is_paused = True
        self.paused.emit(True)

    def resume(self):
        self.is_paused = False
        self.paused.emit(False)

    def _get_available_data(self):
        try:
            if self.board_shim and self.board_shim.get_board_data_count() > 0:
                return self.board_shim.get_board_data()
        except Exception as e:
            self.status_update.emit(f"数据获取警告: {str(e)}")
        return None

    def _generate_synthetic_data(self, rows, num_samples, sample_count, fs):
        synth_data = np.random.normal(0, 2, (rows, num_samples))
        
        t = (sample_count + np.arange(num_samples)) / fs
        for i in range(min(8, rows-4)):
            freq = 10 + i * 2
            synth_data[i, :] += 5 * np.sin(2 * np.pi * freq * t)
            synth_data[i, :] += 15 * np.sin(2 * np.pi * 50 * t)

        synth_data[rows-2, :] = time.time()
        synth_data[rows-1, :] = sample_count + np.arange(num_samples)

        return synth_data

    def _finalize_sampling(self, source_name, is_synthetic=False):
        self.status_update.emit("停止数据流并断开连接...")

        if not is_synthetic and self.board_shim:
            self._safe_release_session()

        if self.data_buffer:
            final_data = np.hstack(self.data_buffer)
            self._save_optimized_data(final_data, source_name)
            self.finished_sampling.emit(final_data, f"{source_name} 数据", self.actual_duration)
        else:
            self.status_update.emit("警告：未采集到任何信号")

    def _safe_release_session(self):
        try:
            if self.board_shim and self.board_shim.is_prepared():
                self.board_shim.stop_stream()
                self.board_shim.release_session()
        except Exception as e:
            self.status_update.emit(f"释放会话警告: {str(e)}")

    def _save_optimized_data(self, data, source_name):
        try:
            save_dir = os.path.dirname(self.save_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)

            header = (f"NabuEEG_Data_{source_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}\n"
                     f"Channels: {data.shape[0]}, Samples: {data.shape[1]}, "
                     f"Duration: {self.actual_duration:.2f}s")

            np.savetxt(self.save_path, data.T, delimiter=',', header=header, comments='')
            self.status_update.emit(f"💾 数据已保存至: {self.save_path}")

        except Exception as e:
            self.status_update.emit(f"保存失败: {e}")

    def stop(self):
        self.is_running = False
        self.is_paused = False

class OpenBCISamplingDialog(QDialog):
    board_combo: QComboBox
    comm_combo: QComboBox

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NabuEEG采集终端")
        self.setMinimumSize(1600, 750)
        self.sampled_data = None
        self.save_path = ""
        self.actual_duration = 0.0
        self.worker = None
        self._sampling_in_progress = False
        
        self.fs = 250
        self.channel_count = 8
        self.display_data = np.zeros((16, 1250))
        self.channel_enabled = [True] * 16
        
        self.filter_processor = FilterProcessor()
        self.b_band, self.a_band = self.filter_processor.butter_bandpass(0.5, 45, self.fs)
        self.b_notch, self.a_notch = self.filter_processor.notch_filter(50, self.fs)
        
        self._init_ui()
        self._init_plot()

    def _init_ui(self):
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
        self.setStyleSheet(BG_DIALOG)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)
        
        ui_components = [
            self._create_header,
            self._create_config_section,
            self._create_save_section,
            self._create_log_section,
            self._create_progress_section,
            self._create_button_section
        ]

        for component in ui_components:
            component(left_panel)

        left_panel.addStretch()
        
        right_panel = QVBoxLayout()
        
        control_container = QWidget()
        control_layout = QHBoxLayout(control_container)
        control_layout.setSpacing(15)
        control_layout.setContentsMargins(5, 5, 5, 10)
        
        filter_group = QGroupBox("🧹 实时预览滤波器")
        filter_group.setStyleSheet(GROUP_BOX_SMALL)
        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(5, 2, 5, 2)
        filter_layout.setSpacing(1)

        self.bp_check = QCheckBox("0.5-45 Hz 带通")
        self.notch_check = QCheckBox("50 Hz 陷波")
        self.bp_check.setStyleSheet(FONT_SMALL_9PT)
        self.notch_check.setStyleSheet(FONT_SMALL_9PT)

        filter_layout.addWidget(self.bp_check)
        filter_layout.addWidget(self.notch_check)
        filter_group.setLayout(filter_layout)
        control_layout.addWidget(filter_group, 0)

        ch_group = QGroupBox("✅ 通道管理")
        ch_group.setStyleSheet(GROUP_BOX_SMALL)
        ch_layout = QVBoxLayout()
        ch_layout.setContentsMargins(5, 2, 5,2)

        self.ch_vbox = QVBoxLayout()
        self.ch_vbox.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        ch_widget = QWidget()
        ch_widget.setLayout(self.ch_vbox)
        scroll.setWidget(ch_widget)
        scroll.setFixedHeight(150)
        scroll.setStyleSheet("border: none; background: transparent;")

        ch_layout.addWidget(scroll)
        ch_group.setLayout(ch_layout)
        control_layout.addWidget(ch_group, 0)                      

        right_panel.addWidget(control_container)
        
        self.pw = pg.PlotWidget()
        self.pw.setBackground('w')
        self.pw.showGrid(x=True, y=True, alpha=0.3)
        self.pw.setLabel('bottom', '时间', 's')
        self.pw.setLabel('left', '通道')
        right_panel.addWidget(self.pw)

        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(right_panel, 3)
        
        self.setLayout(main_layout)
        self._initialize_settings()
        self._update_channel_controls()

    def _init_plot(self):
        self.pw.clear()
        self.curves = []
        self.display_data = np.zeros((self.channel_count, 1250))
        
        for i in range(self.channel_count):
            pen = pg.mkPen(color=pg.intColor(i, self.channel_count), width=1)
            curve = self.pw.plot(pen=pen)
            self.curves.append(curve)
        
        self.pw.setYRange(0, (self.channel_count + 1) * 100)
        self.pw.setXRange(0, 5)

    def _update_channel_controls(self):
        while self.ch_vbox.count():
            item = self.ch_vbox.takeAt(0)
            if item is not None and item.widget() is not None:
                item.widget().deleteLater()
        
        self.ch_checks = []
        for i in range(self.channel_count):
            cb = QCheckBox(f"通道 {i+1}")
            cb.setChecked(True)
            cb.setStyleSheet(FONT_SMALL_9PT_PADDING)
            cb.toggled.connect(lambda checked, idx=i: self._toggle_channel(idx, checked))
            self.ch_vbox.addWidget(cb)
            self.ch_checks.append(cb)

    def _toggle_channel(self, idx, state):
        self.channel_enabled[idx] = state
        if hasattr(self, 'curves') and idx < len(self.curves):
            self.curves[idx].setVisible(state)

    def process_and_plot_data(self, chunk):
        eeg_data = chunk[:self.channel_count, :].copy()
        num_new = eeg_data.shape[1]
        
        for i in range(self.channel_count):
            if self.channel_enabled[i]:
                if self.notch_check.isChecked():
                    eeg_data[i] = lfilter(self.b_notch, self.a_notch, eeg_data[i])
                if self.bp_check.isChecked():
                    eeg_data[i] = lfilter(self.b_band, self.a_band, eeg_data[i])

        self.display_data = np.roll(self.display_data, -num_new, axis=1)
        self.display_data[:, -num_new:] = eeg_data
        
        for i in range(self.channel_count):
            if self.channel_enabled[i]:
                offset = (self.channel_count - i) * 100
                display_points = min(1250, int(5 * self.fs))
                x_data = np.linspace(0, 5, display_points)
                y_data = self.display_data[i, -display_points:] + offset
                self.curves[i].setData(x_data, y_data)

    def _create_header(self, layout):
        header = QLabel("NabuEEG数据采集系统")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(HEADER_CYTON)
        header.setMinimumHeight(50)
        layout.addWidget(header)

    def _create_config_section(self, layout):
        config_group = QGroupBox("📊 硬件配置")
        config_group.setStyleSheet(GROUP_BOX_CONFIG)

        config_layout = QVBoxLayout()
        config_layout.setSpacing(8)
        config_layout.setContentsMargins(10, 15, 10, 10)

        config_controls = [
            self._create_board_selection,
            self._create_comm_selection,
            self._create_port_selection,
            self._create_duration_selection
        ]

        for control in config_controls:
            control(config_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

    def _create_board_selection(self, layout):
        self._create_labeled_combo(
            layout, "板型选择:", "board_combo", 
            ["Cyton (8通道)", "Cyton+Daisy (16通道)", "Ganglion (4通道)", "模拟模式"],
            self.on_board_changed
        )

    def _create_comm_selection(self, layout):
        self._create_labeled_combo(
            layout, "通信方式:", "comm_combo",
            ["串口 (Serial)", "蓝牙 (Bluetooth)", "WiFi"],
            self.update_port_options
        )

    def _create_port_selection(self, layout):
        port_layout = QHBoxLayout()
        self._create_label(port_layout, "端口/地址:", 90)

        self.port_combo = QComboBox()
        self.port_combo.setFixedHeight(28)
        self.port_combo.setStyleSheet(COMBO_BOX_BASE)
        self.port_combo.setEditable(True)
        port_layout.addWidget(self.port_combo)

        scan_btn = QPushButton("🔍 扫描")
        scan_btn.setFixedHeight(28)
        scan_btn.setFixedWidth(80)
        scan_btn.setStyleSheet(BTN_BLUE_SMALL)
        scan_btn.clicked.connect(self._safe_scan_ports)
        port_layout.addWidget(scan_btn)

        layout.addLayout(port_layout)

    def _create_duration_selection(self, layout):
        dur_layout = QHBoxLayout()
        self._create_label(dur_layout, "采样时长:", 90)

        self.duration_spin = QSpinBox()
        self.duration_spin.setFixedHeight(28)
        self.duration_spin.setRange(5, 7200)
        self.duration_spin.setValue(60)
        self.duration_spin.setSuffix(" 秒")
        self.duration_spin.setStyleSheet(SPIN_BOX_BASE)
        dur_layout.addWidget(self.duration_spin)

        quick_durations = [30, 60, 300, 600, 1800]
        for duration in quick_durations:
            btn_text = f"{duration//60}分" if duration >= 60 else f"{duration}秒"
            btn = QPushButton(btn_text)
            btn.setFixedHeight(25)
            btn.setFixedWidth(50)
            btn.setStyleSheet(BTN_GRAY_SMALL)
            btn.clicked.connect(lambda checked, d=duration: self._safe_set_duration(d))
            dur_layout.addWidget(btn)

        dur_layout.addStretch()
        layout.addLayout(dur_layout)

    def _create_save_section(self, layout):
        save_group = QGroupBox("💾 数据保存设置")
        save_group.setStyleSheet(GROUP_BOX_CONFIG)

        save_layout = QVBoxLayout()
        save_layout.setSpacing(8)
        save_layout.setContentsMargins(10, 15, 10, 10)

        path_layout = QHBoxLayout()
        self._create_label(path_layout, "保存路径:", 90)

        self.path_edit = QLineEdit()
        self.path_edit.setFixedHeight(28)
        self.path_edit.setPlaceholderText("点击浏览选择保存位置或自动生成...")
        self.path_edit.setStyleSheet(LINE_EDIT_BASE)
        path_layout.addWidget(self.path_edit)

        generate_btn = QPushButton("自动生成")
        generate_btn.setFixedHeight(28)
        generate_btn.setFixedWidth(85)
        generate_btn.setStyleSheet(BTN_ORANGE_SMALL)
        generate_btn.clicked.connect(self._safe_generate_auto_path)
        path_layout.addWidget(generate_btn)

        browse_btn = QPushButton("📁 浏览")
        browse_btn.setFixedHeight(28)
        browse_btn.setFixedWidth(70)
        browse_btn.setStyleSheet(BTN_GREEN_SMALL)
        browse_btn.clicked.connect(self._safe_browse_save_path)
        path_layout.addWidget(browse_btn)

        save_layout.addLayout(path_layout)

        save_group.setLayout(save_layout)
        layout.addWidget(save_group)

    def _create_log_section(self, layout):
        log_group = QGroupBox("📋 系统日志")
        log_group.setStyleSheet(GROUP_BOX_CONFIG)

        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(10, 15, 10, 10)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(120)
        self.console.setMaximumHeight(150)
        self.console.setStyleSheet(CONSOLE_STYLE)
        log_layout.addWidget(self.console)

        control_layout = QHBoxLayout()
        clear_btn = QPushButton("清空日志")
        clear_btn.setFixedHeight(25)
        clear_btn.setFixedWidth(80)
        clear_btn.setStyleSheet(BTN_RED_SMALL)
        clear_btn.clicked.connect(self._safe_clear_log)
        control_layout.addWidget(clear_btn)

        export_btn = QPushButton("导出日志")
        export_btn.setFixedHeight(25)
        export_btn.setFixedWidth(80)
        export_btn.setStyleSheet(BTN_BLUE_SMALL)
        export_btn.clicked.connect(self._safe_export_log)
        control_layout.addWidget(export_btn)

        control_layout.addStretch()
        log_layout.addLayout(control_layout)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def _create_progress_section(self, layout):
        progress_layout = QVBoxLayout()

        progress_label = QLabel("采集进度:")
        progress_label.setStyleSheet(f"{LABEL_BOLD_INFO} font-size: 11pt;")
        progress_layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setStyleSheet(PROGRESS_BAR)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)

    def _create_button_section(self, layout):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        button_width = 285
        button_height = 35

        self.start_btn = QPushButton("🚀 开始采集")
        self.start_btn.setFixedSize(button_width, button_height)
        self.start_btn.setStyleSheet(BTN_START)
        self.start_btn.clicked.connect(self._safe_start_sampling)

        self.pause_btn = QPushButton("⏸️ 暂停采集")
        self.pause_btn.setFixedSize(button_width, button_height)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet(BTN_PAUSE)
        self.pause_btn.clicked.connect(self._safe_pause_sampling)

        self.stop_btn = QPushButton("⏹️ 停止采集")
        self.stop_btn.setFixedSize(button_width, button_height)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(BTN_STOP)
        self.stop_btn.clicked.connect(self._safe_stop_sampling)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)

    def _create_labeled_combo(self, layout, label_text, attr_name, items, callback):
        h_layout = QHBoxLayout()
        self._create_label(h_layout, label_text, 90)

        combo = QComboBox()
        combo.setFixedHeight(28)
        combo.addItems(items)
        combo.currentTextChanged.connect(callback)
        combo.setStyleSheet(COMBO_BOX_BASE)
        setattr(self, attr_name, combo)
        h_layout.addWidget(combo)

        layout.addLayout(h_layout)

    def _create_label(self, layout, text, width=None):
        label = QLabel(text)
        if width:
            label.setFixedWidth(width)
        label.setStyleSheet(LABEL_FONT_BOLD)
        layout.addWidget(label)

    def _initialize_settings(self):
        self.on_board_changed()
        self.generate_auto_path()
        self.scan_ports()
        self._check_serial_availability()

    def _safe_scan_ports(self):
        try:
            self.scan_ports()
        except Exception as e:
            self.log(f"❌ 端口扫描异常: {str(e)}")

    def _safe_set_duration(self, duration):
        try:
            self.duration_spin.setValue(duration)
        except Exception as e:
            self.log(f"❌ 设置时长异常: {str(e)}")

    def _safe_browse_save_path(self):
        try:
            self.browse_save_path()
        except Exception as e:
            self.log(f"❌ 路径选择异常: {str(e)}")

    def _safe_generate_auto_path(self):
        try:
            self._generate_auto_path_with_timestamp()
        except Exception as e:
            self.log(f"❌ 生成文件名异常: {str(e)}")

    def _safe_clear_log(self):
        try:
            self.console.clear()
        except Exception as e:
            print(f"清空日志异常: {str(e)}")

    def _safe_export_log(self):
        try:
            self.export_log()
        except Exception as e:
            self.log(f"❌ 日志导出异常: {str(e)}")

    def _safe_start_sampling(self):
        if self._sampling_in_progress:
            self.log("⚠️ 采样正在进行中，请勿重复点击")
            return
            
        try:
            self.start_sampling()
        except Exception as e:
            self.log(f"❌ 开始采样异常: {str(e)}")
            self._reset_sampling_state()

    def _safe_pause_sampling(self):
        if not self._sampling_in_progress:
            self.log("⚠️ 当前没有进行中的采样")
            return
        if self.worker is None:
            self.log("⚠️ 采样工作线程未就绪")
            return

        try:
            if self.worker.is_paused:
                self.worker.resume()
                self.pause_btn.setText("⏸️ 暂停采集")
                self.log("▶️ 采样已恢复")
            else:
                self.worker.pause()
                self.pause_btn.setText("▶️ 继续采集")
                self.log("⏸️ 采样已暂停")
        except Exception as e:
            self.log(f"❌ 暂停/恢复操作异常: {str(e)}")

    def _safe_stop_sampling(self):
        if not self._sampling_in_progress:
            self.log("⚠️ 当前没有进行中的采样")
            return
            
        try:
            self.stop_sampling()
        except Exception as e:
            self.log(f"❌ 停止采样异常: {str(e)}")
            self._reset_sampling_state()

    def _reset_sampling_state(self):
        self._sampling_in_progress = False
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("⏸️ 暂停采集")

    def _generate_auto_path_with_timestamp(self):
        board_name = self.board_combo.currentText().split(' ')[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_dir = os.path.join(os.path.expanduser("~"), "Documents", "NabuEEG_Data")
        os.makedirs(default_dir, exist_ok=True)
        
        filename = f"{board_name}_EEG_{timestamp}.csv"
        self.save_path = os.path.join(default_dir, filename)
        self.path_edit.setText(self.save_path)
        self.log(f"✅ 已生成新文件名: {filename}")

    def scan_ports(self):
        self.log("正在扫描可用串口...")

        if not SERIAL_AVAILABLE:
            self.log("警告: 串口检测库未安装，无法自动扫描端口")
            self.log("请安装pyserial库: pip install pyserial")
            if "模拟" not in self.board_combo.currentText():
                self.start_btn.setEnabled(False)
            return

        try:
            ports = list(serial.tools.list_ports.comports())
            available_ports = []

            for port, desc, hwid in sorted(ports):
                port_info = f"{port} - {desc}"
                if any(keyword in desc for keyword in ["USB", "Serial", "ACM"]):
                    port_info += " (可能为OpenBCI设备)"
                available_ports.append(port_info)
                self.log(f"发现端口: {port_info}")

            if available_ports:
                self.port_combo.clear()
                self.port_combo.addItems(available_ports)
                self.log(f"✅ 发现 {len(available_ports)} 个可用串口")
                self.start_btn.setEnabled(True)
            else:
                self.log("❌ 未发现可用串口")
                if "模拟" not in self.board_combo.currentText():
                    self.start_btn.setEnabled(False)

        except Exception as e:
            self.log(f"❌ 端口扫描失败: {str(e)}")
            if "模拟" not in self.board_combo.currentText():
                self.start_btn.setEnabled(False)

    def _check_serial_availability(self):
        if not SERIAL_AVAILABLE:
            self.start_btn.setEnabled(False)
            return
            
        try:
            ports = list(serial.tools.list_ports.comports())
            if not ports:
                self.start_btn.setEnabled(False)
                self.log("⚠️ 未发现可用串口，开始采样按钮已禁用")
            else:
                self.start_btn.setEnabled(True)
        except Exception:
            self.start_btn.setEnabled(False)

    def update_port_options(self):
        comm_text = self.comm_combo.currentText()
        default_options = {
            "串口 (Serial)": ["COM{}".format(i) for i in range(1, 21)] if sys.platform == 'win32' 
                            else ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"],
            "蓝牙 (Bluetooth)": ["00:11:22:33:44:55"],
            "WiFi": ["192.168.1.100:8000"]
        }

        options = default_options.get(comm_text, [])
        self.port_combo.clear()
        self.port_combo.addItems(options)
        self.port_combo.setEditable(True)

    def on_board_changed(self):
        is_simulated = "模拟" in self.board_combo.currentText()
        self.comm_combo.setEnabled(not is_simulated)
        self.port_combo.setEnabled(not is_simulated)

        board_map = {"Cyton": 8, "Cyton+Daisy": 16, "Ganglion": 4, "模拟模式": 8}
        board_name = self.board_combo.currentText().split(' ')[0]
        self.channel_count = board_map.get(board_name, 8)
        
        self._init_plot()
        self._update_channel_controls()

        if is_simulated:
            self.log("切换到模拟模式，无需硬件连接")
            self.start_btn.setEnabled(True)
        else:
            self._check_serial_availability()
        
        self.update_port_options()
        self.generate_auto_path()

    def generate_auto_path(self):
        board_name = self.board_combo.currentText().split(' ')[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_dir = os.path.join(os.path.expanduser("~"), "Documents", "NabuEEG_Data")
        os.makedirs(default_dir, exist_ok=True)
        filename = f"{board_name}_EEG_{timestamp}.csv"
        self.save_path = os.path.join(default_dir, filename)
        self.path_edit.setText(self.save_path)

    def browse_save_path(self):
        default_dir = os.path.join(os.path.expanduser("~"), "Documents", "NabuEEG_Data")
        os.makedirs(default_dir, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存EEG数据", 
            os.path.join(default_dir, "EEG_Data.csv"),
            "CSV文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            self.save_path = file_path
            self.path_edit.setText(file_path)

    def export_log(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", 
            os.path.join(os.path.expanduser("~"), "Documents", 
                       f"NabuEEG_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.console.toPlainText())
                self.log(f"📄 日志已导出至: {file_path}")
            except Exception as e:
                self.log(f"❌ 日志导出失败: {str(e)}")

    def log(self, text):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.console.append(f"[{timestamp}] {text}")
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )

    def get_board_id(self):
        board_map = {
            "Cyton+Daisy": 1,
            "Cyton": 0,
            "Ganglion": 2
        }
        board_name = self.board_combo.currentText().split(' ')[0]
        return board_map.get(board_name, -1)

    def get_board_params(self):
        params = BrainFlowInputParams() if BRAINFLOW_AVAILABLE else _FallbackBoardParams()
        board_id = self.get_board_id()

        if board_id == -1:
            return params

        comm_text = self.comm_combo.currentText()
        port_text = self.port_combo.currentText().split(" - ")[0].strip()

        if comm_text == "串口 (Serial)":
            params.serial_port = port_text or self._get_default_port()
        elif comm_text == "蓝牙 (Bluetooth)":
            params.mac_address = port_text
        elif comm_text == "WiFi":
            if ':' in port_text:
                ip, port = port_text.split(':', 1)
                params.ip_address = ip
                params.ip_port = int(port)
            else:
                params.ip_address = port_text
                params.ip_port = 8000

        return params

    def _get_default_port(self):
        return 'COM3' if sys.platform == 'win32' else '/dev/ttyUSB0'

    def validate_inputs(self):
        if not self.save_path.strip():
            QMessageBox.warning(self, "警告", "请选择保存路径！")
            return False

        if self.get_board_id() != -1:
            port_text = self.port_combo.currentText().strip()
            if not port_text:
                QMessageBox.warning(self, "警告", "请输入通信端口/地址！")
                return False

        return True

    def start_sampling(self):
        if not self.validate_inputs():
            return

        board_id = self.get_board_id()
        params = self.get_board_params()
        duration = self.duration_spin.value()

        self.worker = SamplingThread(board_id, params, duration, self.save_path)
        self.worker.status_update.connect(self.log)
        self.worker.progress_update.connect(self.progress_bar.setValue)
        self.worker.finished_sampling.connect(self.on_finished)
        self.worker.paused.connect(self.on_pause_state_changed)
        self.worker.data_chunk_received.connect(self.process_and_plot_data)

        self._sampling_in_progress = True
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setText("⏸️ 暂停采集")
        self.progress_bar.setValue(0)

        self.display_data = np.zeros((self.channel_count, 1250))
        self._init_plot()

        self.log(f"开始采集: {self.board_combo.currentText()}")
        self.worker.start()

    def on_pause_state_changed(self, is_paused):
        if is_paused:
            self.pause_btn.setText("▶️ 继续采集")
        else:
            self.pause_btn.setText("⏸️ 暂停采集")

    def stop_sampling(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log("用户请求停止采集...")
            self._sampling_in_progress = False
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)

    def on_finished(self, data, source, actual_duration):
        self.sampled_data = data
        self.actual_duration = actual_duration
        self._sampling_in_progress = False

        if actual_duration < 60:
            duration_str = f"{actual_duration:.1f}秒"
        else:
            minutes = int(actual_duration // 60)
            seconds = actual_duration % 60
            duration_str = f"{minutes}分{seconds:.1f}秒"

        self.log(f"✅ 采集完成! 来源: {source}")
        self.log(f"📊 数据维度: {data.shape}")
        self.log(f"⏱️ 实际采样时间: {duration_str}")

        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("⏸️ 暂停采集")
        self.progress_bar.setValue(100)

        QMessageBox.information(self, "采集成功", 
            f"数据采集完成！\n\n"
            f"• 板型: {self.board_combo.currentText()}\n"
            f"• 文件: {os.path.basename(self.save_path)}\n"
            f"• 数据点数: {data.shape[1]}\n"
            f"• 设定采样时长: {self.duration_spin.value()}秒\n"
            f"• 实际采样时间: {duration_str}")

CytonSamplingDialog = OpenBCISamplingDialog
