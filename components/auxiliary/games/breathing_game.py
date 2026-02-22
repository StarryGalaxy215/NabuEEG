from enum import Enum, auto
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QWidget, 
                             QPushButton, QHBoxLayout)
from PyQt5.QtCore import QTimer, Qt, QRectF
from PyQt5.QtGui import (QPainter, QColor, QFont, QBrush, 
                         QRadialGradient, QPen)

class BreathingPhase(Enum):
    INHALE = auto()
    HOLD_IN = auto()
    EXHALE = auto()
    HOLD_OUT = auto()

class BreathingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 100
        self.min_radius = 100
        self.max_radius = 280
        self.step = 1.5
        
        # Phase configuration: (text, color)
        self.phase_config = {
            BreathingPhase.INHALE: ("吸  气", QColor(100, 200, 255)),
            BreathingPhase.HOLD_IN: ("保  持", QColor(100, 200, 255)),
            BreathingPhase.EXHALE: ("呼  气", QColor(100, 255, 150)),
            BreathingPhase.HOLD_OUT: ("保  持", QColor(100, 255, 150)),
        }
        
        self.current_phase = BreathingPhase.INHALE
        self.hold_counter = 0
        self.hold_limits = {BreathingPhase.HOLD_IN: 120, BreathingPhase.HOLD_OUT: 60}
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_state)

    def start_animation(self):
        if not self.timer.isActive():
            self.timer.start(16)  # ~60 FPS

    def stop_animation(self):
        self.timer.stop()

    def _update_state(self):
        phase = self.current_phase
        
        if phase == BreathingPhase.INHALE:
            self.radius += self.step
            if self.radius >= self.max_radius:
                self._switch_phase(BreathingPhase.HOLD_IN)
                
        elif phase == BreathingPhase.EXHALE:
            self.radius -= self.step
            if self.radius <= self.min_radius:
                self._switch_phase(BreathingPhase.HOLD_OUT)
                
        elif phase in (BreathingPhase.HOLD_IN, BreathingPhase.HOLD_OUT):
            self.hold_counter += 1
            if self.hold_counter >= self.hold_limits[phase]:
                next_phase = BreathingPhase.EXHALE if phase == BreathingPhase.HOLD_IN else BreathingPhase.INHALE
                self._switch_phase(next_phase)
                
        self.update()

    def _switch_phase(self, new_phase):
        self.current_phase = new_phase
        self.hold_counter = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        center = rect.center()

        # Background
        painter.fillRect(rect, QColor(245, 247, 250))

        # Outer guide circle
        painter.setPen(QPen(QColor(220, 220, 220), 2, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, self.max_radius, self.max_radius)

        # Breathing circle
        text, color = self.phase_config[self.current_phase]
        
        gradient = QRadialGradient(center, self.radius)
        gradient.setColorAt(0, color.lighter(120))
        gradient.setColorAt(1, color)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, self.radius, self.radius)

        # Text
        painter.setPen(QColor(60, 60, 60))
        painter.setFont(QFont("Microsoft YaHei", 36, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, text)

        # Instruction hint
        painter.setPen(QColor(150, 150, 150))
        painter.setFont(QFont("Microsoft YaHei", 14))
        painter.drawText(QRectF(0, rect.height() - 50, rect.width(), 40), 
                        Qt.AlignCenter, "跟随圆圈大小调节呼吸节奏")

class BreathingGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("呼吸放松训练")
        self.resize(800, 700)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #f5f7fa; }
            QPushButton {
                background-color: #3498db; color: white; border: none;
                padding: 12px 30px; font-size: 16px; border-radius: 6px;
                font-family: "Microsoft YaHei"; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1f618d; }
            QLabel { color: #2c3e50; font-family: "Microsoft YaHei"; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QVBoxLayout()
        title = QLabel("深呼吸放松")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        
        desc = QLabel("通过控制呼吸节奏来调节身心状态，缓解压力。")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 16px; color: #7f8c8d;")
        
        header.addWidget(title)
        header.addWidget(desc)
        layout.addLayout(header)

        # Game Widget
        self.game_widget = BreathingWidget()
        layout.addWidget(self.game_widget, 1)

        # Controls
        controls = QHBoxLayout()
        controls.setSpacing(20)
        
        start_btn = QPushButton("开始训练")
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.clicked.connect(self.game_widget.start_animation)
        
        stop_btn = QPushButton("停止训练")
        stop_btn.setCursor(Qt.PointingHandCursor)
        stop_btn.setStyleSheet("QPushButton { background-color: #e74c3c; } "
                               "QPushButton:hover { background-color: #c0392b; }")
        stop_btn.clicked.connect(self.game_widget.stop_animation)
        
        controls.addStretch()
        controls.addWidget(start_btn)
        controls.addWidget(stop_btn)
        controls.addStretch()
        
        layout.addLayout(controls)
