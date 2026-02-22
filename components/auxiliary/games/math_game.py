import random
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox, QWidget)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIntValidator

class MathGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("速算训练")
        self.resize(400, 300)
        
        self.score = 0
        self.time_left = 60
        self.is_playing = False
        self.current_answer = 0
        
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
        
        # Question Display
        self.question_label = QLabel("准备开始")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setFont(QFont("Consolas", 36, QFont.Bold))
        layout.addWidget(self.question_label)
        
        # Input Area
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("答案")
        self.input_field.setFont(QFont("Consolas", 24))
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.setValidator(QIntValidator())
        self.input_field.returnPressed.connect(self.check_answer)
        self.input_field.setEnabled(False)
        layout.addWidget(self.input_field)
        
        # Start Button
        self.start_btn = QPushButton("开始测试")
        self.start_btn.setFont(QFont("Microsoft YaHei", 14))
        self.start_btn.clicked.connect(self.start_game)
        layout.addWidget(self.start_btn)
        
    def start_game(self):
        self.score = 0
        self.time_left = 60
        self.is_playing = True
        self.score_label.setText(f"得分: {self.score}")
        self.time_label.setText(f"时间: {self.time_left}s")
        self.start_btn.setEnabled(False)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        
        self.next_question()
        self.timer.start(1000)
        
    def next_question(self):
        ops = ['+', '-', '*']
        op = random.choice(ops)
        
        if op == '+':
            a = random.randint(1, 50)
            b = random.randint(1, 50)
            self.current_answer = a + b
        elif op == '-':
            a = random.randint(10, 99)
            b = random.randint(1, a)
            self.current_answer = a - b
        else: # *
            a = random.randint(2, 12)
            b = random.randint(2, 12)
            self.current_answer = a * b
            
        self.question_label.setText(f"{a} {op} {b} = ?")
        self.input_field.clear()
        
    def check_answer(self):
        if not self.is_playing: return
        
        try:
            val = int(self.input_field.text())
            if val == self.current_answer:
                self.score += 1
                self.score_label.setText(f"得分: {self.score}")
                # Optional: Green flash?
            else:
                # Wrong answer, maybe penalty? or just next
                pass
            
            self.next_question()
        except ValueError:
            pass
            
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
        self.input_field.setEnabled(False)
        self.question_label.setText("时间到")
        
        QMessageBox.information(self, "时间到", f"最终得分: {self.score}")
