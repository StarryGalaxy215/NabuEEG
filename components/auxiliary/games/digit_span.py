import random
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox, QWidget)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIntValidator

class DigitSpanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数字记忆广度测试")
        self.resize(400, 300)
        
        self.level = 3
        self.sequence = ""
        self.is_showing = False
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_sequence)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Info
        self.info_label = QLabel("记住屏幕上出现的数字序列，然后输入它。")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Display Area
        self.display_label = QLabel("准备好")
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setFont(QFont("Consolas", 48, QFont.Bold))
        self.display_label.setStyleSheet("color: #2c3e50; background-color: #ecf0f1; border-radius: 10px; padding: 20px;")
        layout.addWidget(self.display_label)
        
        # Input Area (Hidden initially)
        self.input_widget = QWidget()
        input_layout = QVBoxLayout(self.input_widget)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("在此输入数字...")
        self.input_field.setFont(QFont("Consolas", 24))
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.setValidator(QIntValidator())
        self.input_field.returnPressed.connect(self.check_answer)
        input_layout.addWidget(self.input_field)
        
        self.submit_btn = QPushButton("提交")
        self.submit_btn.clicked.connect(self.check_answer)
        input_layout.addWidget(self.submit_btn)
        
        self.input_widget.setVisible(False)
        layout.addWidget(self.input_widget)
        
        # Start Button
        self.start_btn = QPushButton("开始测试")
        self.start_btn.setFont(QFont("Microsoft YaHei", 14))
        self.start_btn.clicked.connect(self.start_game)
        layout.addWidget(self.start_btn)
        
    def start_game(self):
        self.level = 3
        self.start_round()
        self.start_btn.setVisible(False)
        
    def start_round(self):
        self.input_widget.setVisible(False)
        self.input_field.clear()
        self.display_label.setVisible(True)
        
        # Generate sequence
        self.sequence = "".join([str(random.randint(0, 9)) for _ in range(self.level)])
        self.display_label.setText(self.sequence)
        
        # Show time depends on length
        show_time = max(1000, self.level * 800)
        self.timer.start(show_time)
        
    def hide_sequence(self):
        self.display_label.setText("?")
        # self.display_label.setVisible(False) # Keep visible as placeholder
        self.input_widget.setVisible(True)
        self.input_field.setFocus()
        
    def check_answer(self):
        user_input = self.input_field.text()
        if user_input == self.sequence:
            QMessageBox.information(self, "正确", f"恭喜！通过 {self.level} 位数字测试。")
            self.level += 1
            self.start_round()
        else:
            QMessageBox.critical(self, "错误", f"回答错误。\n正确答案: {self.sequence}\n你的回答: {user_input}\n\n最终成绩: {self.level - 1} 位")
            self.start_btn.setVisible(True)
            self.start_btn.setText("重新开始")
            self.input_widget.setVisible(False)
            self.display_label.setText("游戏结束")
