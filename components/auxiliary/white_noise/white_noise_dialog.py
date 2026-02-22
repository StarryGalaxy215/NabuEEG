from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QComboBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

from .noise_engine import NoiseEngine

class WhiteNoiseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("白噪音发生器 (White Noise)")
        self.resize(400, 300)
        
        self.engine = NoiseEngine()
        self.is_playing = False
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🌊 白噪音发生器")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("生成不同颜色的噪音，帮助您放松、专注或助眠。")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #7f8c8d;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Control Panel
        ctrl_group = QGroupBox("控制面板")
        ctrl_layout = QVBoxLayout(ctrl_group)
        
        # Noise Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("噪音类型:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["白噪音 (White Noise)", "粉红噪音 (Pink Noise)", "红噪音 (Brown Noise)"])
        self.combo_type.currentIndexChanged.connect(self.change_noise_type)
        type_layout.addWidget(self.combo_type)
        ctrl_layout.addLayout(type_layout)
        
        # Volume
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("音量:"))
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(50)
        self.slider_vol.valueChanged.connect(self.set_volume)
        vol_layout.addWidget(self.slider_vol)
        ctrl_layout.addLayout(vol_layout)
        
        layout.addWidget(ctrl_group)
        
        # Play/Stop Button
        self.btn_start = QPushButton("开始播放")
        self.btn_start.setMinimumHeight(50)
        self.btn_start.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 25px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1abc9c;
            }
        """)
        self.btn_start.clicked.connect(self.toggle_play)
        layout.addWidget(self.btn_start)
        
        # Footer
        footer = QLabel("提示: 建议佩戴耳机使用以获得最佳体验")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #95a5a6; font-size: 10pt;")
        layout.addWidget(footer)
        
    def change_noise_type(self, index):
        types = ["white", "pink", "brown"]
        if 0 <= index < len(types):
            self.engine.set_noise_type(types[index])
            
    def set_volume(self, val):
        self.engine.set_volume(val / 100.0)
        
    def toggle_play(self):
        if self.is_playing:
            self.stop()
        else:
            self.start()
            
    def start(self):
        self.is_playing = True
        self.btn_start.setText("停止播放")
        self.btn_start.setStyleSheet(self.btn_start.styleSheet().replace("#3498db", "#e74c3c").replace("#2980b9", "#c0392b"))
        
        # Set initial params
        self.change_noise_type(self.combo_type.currentIndex())
        self.set_volume(self.slider_vol.value())
        
        self.engine.start()
        
    def stop(self):
        self.is_playing = False
        self.btn_start.setText("开始播放")
        self.btn_start.setStyleSheet(self.btn_start.styleSheet().replace("#e74c3c", "#3498db").replace("#c0392b", "#2980b9"))
        self.engine.stop()
        
    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)
