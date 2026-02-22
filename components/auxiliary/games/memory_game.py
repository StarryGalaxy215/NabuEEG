from PyQt5.QtWidgets import QDialog, QGridLayout, QPushButton, QVBoxLayout, QLabel, QMessageBox, QWidget, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QFont, QColor
import random

class MemoryGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("记忆翻牌游戏")
        self.resize(800, 900)
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
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_layout = QVBoxLayout()
        title = QLabel("记忆力挑战")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; margin-bottom: 10px;")
        
        desc = QLabel("翻开卡片寻找相同的图案配对，考验你的瞬间记忆。")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 18px; color: #7f8c8d;")
        
        self.steps_label = QLabel("步数: 0")
        self.steps_label.setAlignment(Qt.AlignCenter)
        self.steps_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #3498db; margin-top: 10px;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(desc)
        header_layout.addWidget(self.steps_label)
        layout.addLayout(header_layout)
        
        # Game Grid Container (for centering)
        grid_container = QWidget()
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(grid_container)
        
        self.buttons = []
        self.cards = []
        self.flipped = []
        self.matched = []
        self.is_checking = False
        self.steps = 0
        
        # Control Buttons
        btn_layout = QHBoxLayout()
        self.restart_btn = QPushButton("重新开始")
        self.restart_btn.setCursor(Qt.PointingHandCursor)
        self.restart_btn.setMinimumHeight(50)
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 40px;
                font-size: 18px;
                border-radius: 8px;
                font-family: "Microsoft YaHei";
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
        """)
        self.restart_btn.clicked.connect(self.start_game)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.restart_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.start_game()
        
    def start_game(self):
        # Clear existing buttons
        for btn in self.buttons:
            self.grid_layout.removeWidget(btn)
            btn.deleteLater()
        self.buttons = []
        self.flipped = []
        self.matched = []
        self.is_checking = False
        self.steps = 0
        self.steps_label.setText("步数: 0")
        
        # Create pairs
        symbols = ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼']
        self.cards = symbols * 2
        random.shuffle(self.cards)
        
        # Card Style
        self.card_style_hidden = """
            QPushButton {
                background-color: #2c3e50;
                border-radius: 10px;
                border: 2px solid #34495e;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """
        self.card_style_shown = """
            QPushButton {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #3498db;
                color: black;
            }
        """
        self.card_style_matched = """
            QPushButton {
                background-color: #2ecc71;
                border-radius: 10px;
                border: 2px solid #27ae60;
                color: white;
            }
        """
        
        # Create buttons
        for i in range(4):
            for j in range(4):
                btn = QPushButton("")
                btn.setFont(QFont("Segoe UI Emoji", 40)) # Larger emoji
                btn.setFixedSize(140, 140) # Larger cards
                btn.setStyleSheet(self.card_style_hidden)
                btn.setCursor(Qt.PointingHandCursor)
                
                index = i * 4 + j
                btn.clicked.connect(lambda checked, idx=index: self.on_card_click(idx))
                self.grid_layout.addWidget(btn, i, j)
                self.buttons.append(btn)
                
    def on_card_click(self, index):
        if self.is_checking or index in self.matched or index in self.flipped:
            return
            
        self.buttons[index].setText(self.cards[index])
        self.buttons[index].setStyleSheet(self.card_style_shown)
        self.flipped.append(index)
        
        if len(self.flipped) == 2:
            self.steps += 1
            self.steps_label.setText(f"步数: {self.steps}")
            self.is_checking = True
            QTimer.singleShot(600, self.check_match)
            
    def check_match(self):
        idx1, idx2 = self.flipped
        if self.cards[idx1] == self.cards[idx2]:
            self.matched.extend(self.flipped)
            self.buttons[idx1].setStyleSheet(self.card_style_matched)
            self.buttons[idx2].setStyleSheet(self.card_style_matched)
            self.buttons[idx1].setEnabled(False)
            self.buttons[idx2].setEnabled(False)
            
            if len(self.matched) == len(self.cards):
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("胜利")
                msg_box.setText(f"恭喜！你用了 {self.steps} 步完成了游戏！")
                msg_box.setStyleSheet("QLabel{font-size: 16px;}")
                msg_box.exec_()
        else:
            self.buttons[idx1].setText("")
            self.buttons[idx2].setText("")
            self.buttons[idx1].setStyleSheet(self.card_style_hidden)
            self.buttons[idx2].setStyleSheet(self.card_style_hidden)
            
        self.flipped = []
        self.is_checking = False
