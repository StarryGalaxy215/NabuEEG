import random
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QComboBox, QMessageBox, QWidget, QSizePolicy)
from PyQt5.QtCore import QTimer, Qt, QTime
from PyQt5.QtGui import QFont, QColor

class SchulteGridDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("舒尔特方格专注力训练")
        self.resize(600, 700)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        
        self.grid_size = 5
        self.expected_number = 1
        self.start_time = None
        self.is_playing = False
        self.elapsed_time = 0 # in milliseconds
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        self.buttons = []
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("舒尔特方格")
        title.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.size_combo = QComboBox()
        self.size_combo.addItems(["3x3 (简单)", "4x4 (普通)", "5x5 (标准)", "6x6 (困难)", "7x7 (挑战)"])
        self.size_combo.setCurrentIndex(2) # Default 5x5
        self.size_combo.currentIndexChanged.connect(self.change_grid_size)
        header_layout.addWidget(self.size_combo)
        
        main_layout.addLayout(header_layout)
        
        # Status Bar
        status_layout = QHBoxLayout()
        
        self.next_label = QLabel("下一个: 1")
        self.next_label.setFont(QFont("Microsoft YaHei", 16))
        self.next_label.setStyleSheet("color: #2c3e50;")
        status_layout.addWidget(self.next_label)
        
        status_layout.addStretch()
        
        self.timer_label = QLabel("00:00.00")
        self.timer_label.setFont(QFont("Consolas", 20, QFont.Bold))
        self.timer_label.setStyleSheet("color: #e74c3c;")
        status_layout.addWidget(self.timer_label)
        
        main_layout.addLayout(status_layout)
        
        # Game Grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        main_layout.addWidget(self.grid_widget, 1) # Expand vertically
        
        # Controls
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始游戏")
        self.start_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 8px;
                padding: 10px 30px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #219150;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.start_btn.clicked.connect(self.start_game)
        control_layout.addWidget(self.start_btn)
        
        main_layout.addLayout(control_layout)
        
        # Instructions
        desc = QLabel("说明: 按顺序点击数字(从1开始)，越快越好。这是训练注意力和视幅的经典方法。")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; font-size: 14px; margin-top: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(desc)
        
        # Initialize grid (disabled state)
        self.create_grid()
        
    def change_grid_size(self, index):
        sizes = [3, 4, 5, 6, 7]
        self.grid_size = sizes[index]
        if self.is_playing:
            self.stop_game()
        self.create_grid()
        
    def create_grid(self):
        # Clear existing grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.buttons = []
        numbers = list(range(1, self.grid_size * self.grid_size + 1))
        # Don't shuffle yet, just show ordered numbers in disabled state
        
        font_size = 24
        if self.grid_size >= 6: font_size = 18
        if self.grid_size >= 7: font_size = 16
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                num = numbers[r * self.grid_size + c]
                btn = QPushButton(str(num))
                btn.setFont(QFont("Arial", font_size, QFont.Bold))
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                btn.setStyleSheet(self.get_btn_style())
                btn.clicked.connect(lambda checked, n=num, b=btn: self.on_btn_clicked(n, b))
                btn.setEnabled(False)
                
                self.grid_layout.addWidget(btn, r, c)
                self.buttons.append(btn)
                
    def get_btn_style(self, state="normal"):
        base_style = """
            QPushButton {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                color: #2c3e50;
            }
        """
        if state == "normal":
            return base_style + """
                QPushButton:hover {
                    background-color: #d5dbdb;
                    border-color: #95a5a6;
                }
            """
        elif state == "correct":
            return """
                QPushButton {
                    background-color: #2ecc71;
                    border: 2px solid #27ae60;
                    border-radius: 5px;
                    color: white;
                }
            """
        elif state == "wrong": # Usually flashes, but static style here just in case
            return """
                QPushButton {
                    background-color: #e74c3c;
                    border: 2px solid #c0392b;
                    border-radius: 5px;
                    color: white;
                }
            """
        return base_style

    def start_game(self):
        self.is_playing = True
        self.start_btn.setText("重新开始")
        self.start_btn.setStyleSheet(self.start_btn.styleSheet().replace("#27ae60", "#f39c12").replace("#2ecc71", "#f1c40f").replace("#219150", "#d35400"))
        
        self.expected_number = 1
        self.next_label.setText(f"下一个: {self.expected_number}")
        self.elapsed_time = 0
        self.timer_label.setText("00:00.00")
        
        # Shuffle numbers
        numbers = list(range(1, self.grid_size * self.grid_size + 1))
        random.shuffle(numbers)
        
        for i, btn in enumerate(self.buttons):
            btn.setText(str(numbers[i]))
            btn.setEnabled(True)
            btn.setStyleSheet(self.get_btn_style("normal"))
            # Store the number in the button object for easier access
            btn.setProperty("number", numbers[i])
            
        self.timer.start(10) # 10ms update interval
        
    def stop_game(self):
        self.is_playing = False
        self.timer.stop()
        self.start_btn.setText("开始游戏")
        # Reset button style back to green
        self.start_btn.setStyleSheet(self.start_btn.styleSheet().replace("#f39c12", "#27ae60").replace("#f1c40f", "#2ecc71").replace("#d35400", "#219150"))
        
        for btn in self.buttons:
            btn.setEnabled(False)

    def update_timer(self):
        self.elapsed_time += 10
        seconds = (self.elapsed_time // 1000) % 60
        minutes = (self.elapsed_time // 60000)
        milliseconds = (self.elapsed_time % 1000) // 10
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}.{milliseconds:02d}")
        
    def on_btn_clicked(self, num_placeholder, btn):
        if not self.is_playing: return
        
        actual_num = btn.property("number")
        
        if actual_num == self.expected_number:
            # Correct!
            btn.setStyleSheet(self.get_btn_style("correct"))
            
            # Check if finished
            if self.expected_number == self.grid_size * self.grid_size:
                self.game_over()
            else:
                self.expected_number += 1
                self.next_label.setText(f"下一个: {self.expected_number}")
        else:
            # Wrong! Flash red briefly
            original_style = btn.styleSheet()
            btn.setStyleSheet(self.get_btn_style("wrong"))
            QTimer.singleShot(200, lambda: btn.setStyleSheet(original_style) if self.is_playing and btn.property("number") >= self.expected_number else None)

    def game_over(self):
        self.stop_game()
        seconds = self.elapsed_time / 1000.0
        
        # Rating
        rating = "一般"
        if self.grid_size == 5:
            if seconds < 25: rating = "神级"
            elif seconds < 35: rating = "优秀"
            elif seconds < 50: rating = "良好"
        
        QMessageBox.information(self, "挑战成功！", 
                              f"恭喜你完成了 {self.grid_size}x{self.grid_size} 舒尔特方格！\n"
                              f"用时: {self.timer_label.text()}\n"
                              f"评价: {rating}")
