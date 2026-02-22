from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QWidget, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QTimer, Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QRadialGradient, QPen
import random

class FocusGameWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.score = 0
        self.time_left = 30
        self.target_pos = (200, 200)
        self.target_radius = 40
        self.is_playing = False
        self.click_effect = None # (x, y, radius, opacity)
        
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.update_game_time)
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(16) # 60 FPS
        
    def start_game(self):
        self.score = 0
        self.time_left = 30
        self.is_playing = True
        self.spawn_target()
        self.game_timer.start(1000)
        self.update()
        
    def stop_game(self):
        self.game_timer.stop()
        self.is_playing = False
        self.update()
        
    def spawn_target(self):
        w = self.width() - 100
        h = self.height() - 100
        self.target_pos = (random.randint(50, w), random.randint(50, h))
        
    def update_game_time(self):
        self.time_left -= 1
        if self.time_left <= 0:
            self.stop_game()
            msg = QMessageBox(self)
            msg.setWindowTitle("游戏结束")
            msg.setText(f"时间到！\n你的最终得分是: {self.score}")
            msg.setStyleSheet("QLabel{font-size: 16px;}")
            msg.exec_()
        self.update()
        
    def update_animation(self):
        if self.click_effect:
            x, y, r, o = self.click_effect
            r += 2
            o -= 15
            if o <= 0:
                self.click_effect = None
            else:
                self.click_effect = (x, y, r, o)
            self.update()

    def mousePressEvent(self, event):
        if not self.is_playing:
            return
            
        x, y = event.x(), event.y()
        tx, ty = self.target_pos
        dist = ((x - tx)**2 + (y - ty)**2)**0.5
        
        if dist <= self.target_radius + 10: # A bit of tolerance
            self.score += 1
            self.click_effect = (tx, ty, self.target_radius, 255)
            self.spawn_target()
            self.update()
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background with grid
        painter.fillRect(self.rect(), QColor(245, 247, 250))
        painter.setPen(QPen(QColor(220, 220, 220), 1))
        grid_size = 50
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
        
        if self.is_playing:
            # Draw target (Red with gradient)
            tx, ty = self.target_pos
            
            # Outer glow
            gradient = QRadialGradient(tx, ty, self.target_radius)
            gradient.setColorAt(0, QColor(255, 80, 80))
            gradient.setColorAt(1, QColor(200, 0, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(Qt.white, 2))
            painter.drawEllipse(QPoint(tx, ty), self.target_radius, self.target_radius)
            
            # Inner rings
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(Qt.white, 2))
            painter.drawEllipse(QPoint(tx, ty), self.target_radius * 0.6, self.target_radius * 0.6)
            painter.drawEllipse(QPoint(tx, ty), self.target_radius * 0.3, self.target_radius * 0.3)
            
            # Click effect
            if self.click_effect:
                cx, cy, cr, co = self.click_effect
                painter.setPen(QPen(QColor(255, 215, 0, int(co)), 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPoint(cx, cy), cr, cr)
            
            # HUD (Heads-Up Display)
            painter.setBrush(QColor(0, 0, 0, 150))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(10, 10, 150, 80, 10, 10)
            
            painter.setPen(Qt.white)
            painter.setFont(QFont("Microsoft YaHei", 14))
            painter.drawText(25, 40, f"得分: {self.score}")
            
            # Time bar
            painter.drawText(25, 70, f"时间: {self.time_left}s")
            
        else:
            painter.setPen(QColor(44, 62, 80))
            painter.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "准备好了吗？\n点击下方按钮开始挑战")

class FocusGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("专注力训练")
        self.resize(1000, 800)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QLabel {
                font-family: "Microsoft YaHei";
                color: #2c3e50;
            }
        """)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QVBoxLayout()
        title = QLabel("专注力训练")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        
        desc = QLabel("快速点击出现的红色靶点，在30秒内挑战最高分。")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 16px; color: #7f8c8d;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(desc)
        layout.addLayout(header_layout)
        
        self.game_widget = FocusGameWidget()
        layout.addWidget(self.game_widget, 1)
        
        btn_layout = QHBoxLayout()
        start_btn = QPushButton("开始挑战")
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.setMinimumHeight(50)
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 40px;
                font-size: 18px;
                border-radius: 8px;
                font-family: "Microsoft YaHei";
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        start_btn.clicked.connect(self.game_widget.start_game)
        
        btn_layout.addStretch()
        btn_layout.addWidget(start_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
