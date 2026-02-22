import random
import time
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QMessageBox, QWidget)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor

class ReactionGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("反应速度测试")
        self.resize(500, 400)
        
        self.state = "waiting_start" # waiting_start, waiting_green, waiting_click, result
        self.times = []
        self.rounds = 0
        self.max_rounds = 5
        self.start_time = 0
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.turn_green)
        
        self.init_ui()
        
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_label = QLabel("点击开始测试")
        self.main_label.setAlignment(Qt.AlignCenter)
        self.main_label.setFont(QFont("Microsoft YaHei", 32, QFont.Bold))
        self.main_label.setStyleSheet("color: white;")
        self.main_layout.addWidget(self.main_label)
        
        self.sub_label = QLabel("当屏幕变绿时，请立即点击")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setFont(QFont("Microsoft YaHei", 16))
        self.sub_label.setStyleSheet("color: white;")
        self.main_layout.addWidget(self.sub_label)
        
        self.setStyleSheet("background-color: #3498db;") # Blue for start

    def mousePressEvent(self, event):
        if self.state == "waiting_start":
            self.start_round()
        elif self.state == "waiting_green":
            # Too early
            self.timer.stop()
            self.setStyleSheet("background-color: #e74c3c;") # Red
            self.main_label.setText("太早了！")
            self.sub_label.setText("请等待屏幕变绿后再点击。点击重试。")
            self.state = "waiting_start"
        elif self.state == "waiting_click":
            # Success
            end_time = time.time()
            reaction_time = (end_time - self.start_time) * 1000 # ms
            self.times.append(reaction_time)
            self.rounds += 1
            
            self.setStyleSheet("background-color: #3498db;") # Blue
            
            if self.rounds >= self.max_rounds:
                avg = sum(self.times) / len(self.times)
                self.main_label.setText(f"平均: {int(avg)} ms")
                self.sub_label.setText("测试完成。点击重新开始")
                self.rounds = 0
                self.times = []
                self.state = "waiting_start"
            else:
                self.main_label.setText(f"{int(reaction_time)} ms")
                self.sub_label.setText(f"第 {self.rounds}/{self.max_rounds} 轮。点击继续")
                self.state = "waiting_start"
                
    def start_round(self):
        self.state = "waiting_green"
        self.setStyleSheet("background-color: #e74c3c;") # Red
        self.main_label.setText("等待...")
        self.sub_label.setText("看到绿色立即点击")
        
        # Random delay 2-5 seconds
        delay = random.randint(2000, 5000)
        self.timer.start(delay)
        
    def turn_green(self):
        self.state = "waiting_click"
        self.setStyleSheet("background-color: #2ecc71;") # Green
        self.main_label.setText("点击！")
        self.sub_label.setText("")
        self.start_time = time.time()
