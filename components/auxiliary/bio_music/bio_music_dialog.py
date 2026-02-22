import random
import time
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QSlider, QProgressBar, QGroupBox, QComboBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPainter, QColor, QPen

from .audio_engine import BioMusicEngine

class WaveformWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.setStyleSheet("background-color: #2c3e50; border-radius: 10px;")
        self.stress_level = 0.5
        self.history = []
        
    def update_data(self, stress_level):
        self.stress_level = stress_level
        self.history.append(stress_level)
        if len(self.history) > 100:
            self.history.pop(0)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor("#2c3e50"))
        
        w = self.width()
        h = self.height()
        
        # Draw Grid
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1, Qt.DotLine))
        painter.drawLine(0, h//2, w, h//2)
        
        # Draw Wave
        if not self.history: return
        
        # Color based on current stress
        # Green (Relaxed) -> Red (Stressed)
        r = int(self.stress_level * 255)
        g = int((1 - self.stress_level) * 255)
        color = QColor(r, g, 100)
        
        painter.setPen(QPen(color, 2))
        
        step_x = w / 100
        
        prev_x = 0
        prev_y = h - (self.history[0] * h * 0.8 + h * 0.1)
        
        for i, val in enumerate(self.history):
            x = i * step_x
            y = h - (val * h * 0.8 + h * 0.1)
            painter.drawLine(int(prev_x), int(prev_y), int(x), int(y))
            prev_x = x
            prev_y = y

class BioMusicDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("脑波音乐生成 (Bio-Music)")
        self.resize(600, 500)
        
        self.engine = BioMusicEngine()
        self.is_playing = False
        
        # Simulated EEG Data Timer
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.simulate_eeg)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🧠 脑波音乐生成")
        title.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("系统将根据您的实时脑电波生成环境音乐。\n放松时音乐舒缓，紧张时节奏加快。")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(desc)
        
        # Visualizer
        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform)
        
        # Info Panel
        info_layout = QHBoxLayout()
        
        self.lbl_alpha = QLabel("Alpha (放松): 0%")
        self.lbl_beta = QLabel("Beta (专注): 0%")
        self.lbl_state = QLabel("当前状态: --")
        self.lbl_state.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        
        info_layout.addWidget(self.lbl_alpha)
        info_layout.addStretch()
        info_layout.addWidget(self.lbl_state)
        info_layout.addStretch()
        info_layout.addWidget(self.lbl_beta)
        
        layout.addLayout(info_layout)
        
        # Controls
        ctrl_group = QGroupBox("控制面板")
        ctrl_layout = QVBoxLayout(ctrl_group)
        
        # Volume
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("音量:"))
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(50)
        self.slider_vol.valueChanged.connect(self.set_volume)
        vol_layout.addWidget(self.slider_vol)
        ctrl_layout.addLayout(vol_layout)
        
        # Mode (Simulated for now, would be real EEG channel selection)
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("数据源:"))
        self.combo_source = QComboBox()
        self.combo_source.addItems(["模拟数据 (演示)", "实时 EEG (未连接)"])
        mode_layout.addWidget(self.combo_source)
        ctrl_layout.addLayout(mode_layout)
        
        layout.addWidget(ctrl_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始生成")
        self.btn_start.setMinimumHeight(50)
        self.btn_start.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_start.clicked.connect(self.toggle_play)
        
        btn_layout.addWidget(self.btn_start)
        layout.addLayout(btn_layout)
        
    def toggle_play(self):
        if self.is_playing:
            self.stop()
        else:
            self.start()
            
    def start(self):
        self.is_playing = True
        self.btn_start.setText("停止生成")
        self.btn_start.setStyleSheet(self.btn_start.styleSheet().replace("#3498db", "#e74c3c").replace("#2980b9", "#c0392b"))
        self.engine.start()
        self.data_timer.start(100) # Update every 100ms
        
    def stop(self):
        self.is_playing = False
        self.btn_start.setText("开始生成")
        self.btn_start.setStyleSheet(self.btn_start.styleSheet().replace("#e74c3c", "#3498db").replace("#c0392b", "#2980b9"))
        self.engine.stop()
        self.data_timer.stop()
        
    def set_volume(self, val):
        self.engine.set_volume(val / 100.0)
        
    def simulate_eeg(self):
        """
        Generate random but smooth EEG data for demonstration.
        In a real app, this would be replaced by data from the LSL stream or Cyton board.
        """
        # Simulate drifting values
        import math
        import time # Explicit import to avoid NameError if time wasn't imported globally or correctly
        t = time.time()
        
        # Alpha (Relaxed) oscillates slowly
        alpha = (math.sin(t * 0.5) + 1) * 25 + random.uniform(-5, 5)
        
        # Beta (Stress) oscillates faster
        beta = (math.sin(t * 2.0) + 1) * 25 + random.uniform(-5, 5)
        
        # Occasionally spike beta to show "Stress"
        if int(t) % 10 < 3:
            beta += 40
            alpha -= 10
            
        alpha = max(0, min(100, alpha))
        beta = max(0, min(100, beta))
        
        stress = self.engine.update_eeg_state(alpha, beta)
        
        # Update UI
        self.waveform.update_data(stress)
        self.lbl_alpha.setText(f"Alpha: {int(alpha)}%")
        self.lbl_beta.setText(f"Beta: {int(beta)}%")
        
        if stress < 0.3:
            self.lbl_state.setText("状态: 深度放松 😌")
            self.lbl_state.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 16px;")
        elif stress < 0.6:
            self.lbl_state.setText("状态: 平静专注 🙂")
            self.lbl_state.setStyleSheet("color: #f1c40f; font-weight: bold; font-size: 16px;")
        else:
            self.lbl_state.setText("状态: 紧张/兴奋 😫")
            self.lbl_state.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 16px;")
            
    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)
