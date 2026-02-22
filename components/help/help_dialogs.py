import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QTextBrowser
)

from common import HTML
from common.config import LOGO_PATH, APP_NAME
from common.styles import (
    NO_LOGO_LABEL,
    BTN_ABOUT_CLOSE,
    BTN_RESOURCE_CLOSE,
    TITLE_RESOURCE,
    TEXT_BROWSER,
    BG_DIALOG_RESOURCE,
    Colors,
)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"关于{APP_NAME}")
        self.setFixedSize(400, 500)
        layout = QVBoxLayout()
        
        logo_label = QLabel()
        logo_path = LOGO_PATH
        
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
        else:
            no_logo_label = QLabel("logo.png 文件未找到")
            no_logo_label.setAlignment(Qt.AlignCenter)
            no_logo_label.setStyleSheet(NO_LOGO_LABEL)
            layout.addWidget(no_logo_label)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(HTML.ABOUT_HTML)
        layout.addWidget(text_edit)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet(BTN_ABOUT_CLOSE)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

class TutorialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("使用教程")
        self.setFixedSize(500, 400)
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(HTML.TUTORIAL_HTML)
        layout.addWidget(text_edit)
        self.setLayout(layout)

class ResourceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("相关资源")
        self.setFixedSize(650, 550)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        title_label = QLabel("🔗 EEG信号处理相关资源")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(TITLE_RESOURCE)
        layout.addWidget(title_label)
        
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setReadOnly(True)
        
        text_browser.setHtml(HTML.RESOURCE_HTML)
        
        text_browser.setStyleSheet(TEXT_BROWSER)
        
        layout.addWidget(text_browser)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet(BTN_RESOURCE_CLOSE)
        
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        self.setStyleSheet(BG_DIALOG_RESOURCE)
