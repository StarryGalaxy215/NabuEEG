import random
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QWidget)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor

class StroopGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("斯特鲁普效应测试 (Stroop Test)")
        self.resize(500, 400)
        
        self.score = 0
        self.time_left = 60
        self.is_playing = False
        
        self.colors = {
            "红色": "#e74c3c",
            "蓝色": "#3498db",
            "绿色": "#2ecc71",
            "黄色": "#f1c40f"
        }
        self.color_names = list(self.colors.keys())
        self.current_color_name = "" # Text content
        self.current_ink_color = ""  # Text color
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        self.score_label = QLabel("得分: 0")
        self.time_label = QLabel("时间: 60s")
        header.addWidget(self.score_label)
        header.addStretch()
        header.addWidget(self.time_label)
        layout.addLayout(header)
        
        # Word Display
        self.word_label = QLabel("准备开始")
        self.word_label.setAlignment(Qt.AlignCenter)
        self.word_label.setFont(QFont("Microsoft YaHei", 48, QFont.Bold))
        self.word_label.setFixedHeight(150)
        layout.addWidget(self.word_label)
        
        # Instruction
        inst = QLabel("请点击文字的 **颜色** (而不是文字内容)")
        inst.setAlignment(Qt.AlignCenter)
        layout.addWidget(inst)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.choice_btns = []
        for name in ["红色", "蓝色", "绿色", "黄色"]:
            btn = QPushButton(name)
            btn.setFixedSize(100, 60)
            btn.setFont(QFont("Microsoft YaHei", 14))
            # Style each button with a neutral background but colored border maybe?
            # Or just colored text? Let's keep it simple.
            btn.setStyleSheet(f"background-color: {self.colors[name]}; color: white; border-radius: 8px; font-weight: bold;")
            btn.clicked.connect(lambda checked, n=name: self.check_answer(n))
            btn.setEnabled(False)
            btn_layout.addWidget(btn)
            self.choice_btns.append(btn)
        
        layout.addLayout(btn_layout)
        
        # Control
        self.start_btn = QPushButton("开始测试")
        self.start_btn.clicked.connect(self.start_game)
        layout.addWidget(self.start_btn)
        
    def start_game(self):
        self.score = 0
        self.time_left = 60
        self.is_playing = True
        self.score_label.setText(f"得分: {self.score}")
        self.time_label.setText(f"时间: {self.time_left}s")
        self.start_btn.setEnabled(False)
        self.start_btn.setText("游戏中...")
        
        for btn in self.choice_btns:
            btn.setEnabled(True)
            
        self.next_round()
        self.timer.start(1000)
        
    def next_round(self):
        # Pick a word (text)
        text_idx = random.randint(0, 3)
        self.current_color_name = self.color_names[text_idx]
        
        # Pick a color (ink) - ensure it's often different from text for Stroop effect
        # But sometimes same to trick user.
        ink_idx = random.randint(0, 3)
        self.current_ink_color = self.color_names[ink_idx]
        
        self.word_label.setText(self.current_color_name)
        self.word_label.setStyleSheet(f"color: {self.colors[self.current_ink_color]}")
        
    def check_answer(self, selected_color_name):
        if not self.is_playing: return
        
        if selected_color_name == self.current_ink_color:
            self.score += 1
            self.score_label.setText(f"得分: {self.score}")
            # Optional: Visual feedback for correct?
        else:
            # Penalty?
            self.score = max(0, self.score - 1)
            self.score_label.setText(f"得分: {self.score}")
            
        self.next_round()
        
    def update_timer(self):
        self.time_left -= 1
        self.time_label.setText(f"时间: {self.time_left}s")
        if self.time_left <= 0:
            self.game_over()
            
    def game_over(self):
        self.is_playing = False
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.start_btn.setText("重新开始")
        for btn in self.choice_btns:
            btn.setEnabled(False)
        
        rating = "一般"
        if self.score > 40: rating = "神级反应"
        elif self.score > 30: rating = "优秀"
        elif self.score > 20: rating = "不错"
        
        QMessageBox.information(self, "时间到", f"最终得分: {self.score}\n评价: {rating}")
