import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, 
    QFrame, QGraphicsDropShadowEffect, QApplication, QStackedWidget, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QRect, QEasingCurve, QPoint
from PyQt5.QtGui import QDesktopServices, QColor

# --- Web Engine Support ---
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
    WEB_ENGINE_AVAILABLE = True
    WEB_ENGINE_ERROR = None
except ImportError as e:
    WEB_ENGINE_AVAILABLE = False
    WEB_ENGINE_ERROR = str(e)
except Exception as e:
    WEB_ENGINE_AVAILABLE = False
    WEB_ENGINE_ERROR = str(e)

# --- Constants & Templates ---
APLAYER_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>NabuEEG Online Music</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/aplayer/dist/APlayer.min.css"><style>body,html{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}.aplayer{margin:0!important;box-shadow:0 8px 32px rgba(0,0,0,0.1)!important;border-radius:0!important;height:calc(100vh - 60px)!important;display:flex!important;flex-direction:column;background:rgba(255,255,255,0.95)!important;backdrop-filter:blur(10px)}.aplayer-body{flex:0 0 auto;width:100%!important}.aplayer-list{flex:1 1 auto;overflow-y:auto!important;height:auto!important;max-height:none!important;padding-bottom:0!important;background:rgba(255,255,255,0.5)!important}.aplayer-pic{height:90px!important;width:90px!important;border-radius:8px!important;box-shadow:0 4px 12px rgba(0,0,0,0.15)!important}.aplayer-info{height:90px!important;margin-left:90px!important;padding:10px 7px 0 10px!important}.aplayer-icon-menu{display:none!important}.aplayer .aplayer-list li{border-top:1px solid rgba(200,200,200,0.3)!important}.aplayer .aplayer-list li:hover{background:rgba(102,126,234,0.1)!important}.aplayer .aplayer-list ol::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:rgba(255,255,255,0.3)}::-webkit-scrollbar-thumb{background:linear-gradient(135deg, #667eea, #764ba2);border-radius:3px}::-webkit-scrollbar-thumb:hover{background:linear-gradient(135deg, #764ba2, #667eea)}#playlist-bar{position:absolute;bottom:0;left:0;width:100%;height:60px;background:linear-gradient(135deg, #667eea, #764ba2);display:flex;align-items:center;justify-content:center;gap:20px;box-shadow:0 -4px 12px rgba(0,0,0,0.2);z-index:1000}#playlist-bar button{background:rgba(255,255,255,0.2);color:white;border:2px solid rgba(255,255,255,0.3);padding:10px 20px;border-radius:8px;font-size:16px;font-weight:bold;cursor:pointer;transition:all 0.3s ease;backdrop-filter:blur(5px)}#playlist-bar button:hover{background:rgba(255,255,255,0.3);transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,0.3)}#playlist-bar button:active{transform:translateY(0)}#playlist-bar span{color:white;font-size:14px;font-weight:bold;text-shadow:0 2px 4px rgba(0,0,0,0.3);min-width:150px;text-align:center}</style></head><body><div id="player-container"></div><div id="playlist-bar"><button id="prev-playlist" onclick="switchPlaylist(-1)">◀</button><span id="playlist-indicator">Playlist 1/2</span><button id="next-playlist" onclick="switchPlaylist(1)">▶</button></div><script src="https://cdn.jsdelivr.net/npm/aplayer/dist/APlayer.min.js"></script><script src="https://cdn.jsdelivr.net/npm/meting@2/dist/Meting.min.js"></script><script>window.addEventListener("load",function(){var container=document.getElementById("player-container");var playlists=[{id:"3778678",name:"精选歌单"},{id:"13912531641",name:"古风 DJ"},{id:"7593158581",name:"华北浪革"}];var currentPlaylistIndex=0;var aplayerInstance=null;function loadPlaylist(index){try{if(aplayerInstance&&typeof aplayerInstance.destroy==="function"){aplayerInstance.destroy()}container.innerHTML="";var p=document.createElement("meting-js");p.setAttribute("server","netease");p.setAttribute("type","playlist");p.setAttribute("id",playlists[index].id);p.setAttribute("fixed","false");p.setAttribute("autoplay","false");p.setAttribute("loop","all");p.setAttribute("order","list");p.setAttribute("preload","auto");p.setAttribute("list-folded","false");container.appendChild(p);setTimeout(function(){var metingElement=container.querySelector("meting-js");if(metingElement&&metingElement.aplayer){aplayerInstance=metingElement.aplayer}},100);document.getElementById("playlist-indicator").textContent="Playlist "+(index+1)+"/"+playlists.length+" - "+playlists[index].name}catch(e){console.error("Error loading playlist:",e)}}window.switchPlaylist=function(direction){currentPlaylistIndex+=direction;if(currentPlaylistIndex<0)currentPlaylistIndex=playlists.length-1;if(currentPlaylistIndex>=playlists.length)currentPlaylistIndex=0;loadPlaylist(currentPlaylistIndex)};loadPlaylist(0);document.addEventListener("click",function(e){var t=e.target.closest(".aplayer-list");t&&!e.target.closest("li")&&(e.stopPropagation(),e.stopImmediatePropagation(),e.preventDefault())},!0)});</script></body></html>"""



class FloatingMusicPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.expanded_w, self.collapsed_w, self.h = 320, 30, 400
        self.is_collapsed, self.dragging = False, False
        self.dock_side = None # None, 'left', 'right'
        self.drag_pos = QPoint()
        self.drag_start_pos = QPoint()
        
        self.collapse_timer = QTimer(self)
        self.collapse_timer.setSingleShot(True)
        self.collapse_timer.timeout.connect(self._do_collapse)

        self.setup_ui()
        self.setup_anim()
        
        s = QApplication.primaryScreen().geometry()
        self.setGeometry(s.width() - self.expanded_w - 20, (s.height() - self.h)//2, self.expanded_w, self.h)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Wrapper for content to manage visibility easily
        self.main_wrapper = QWidget()
        wrapper_layout = QGridLayout(self.main_wrapper)
        wrapper_layout.setContentsMargins(15, 15, 15, 15)  # Margin for shadow
        
        # 1. Background Layer (with Shadow)
        self.bg_frame = QFrame()
        modern_gradient = """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
        """
        self.bg_frame.setStyleSheet(modern_gradient)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.bg_frame.setGraphicsEffect(shadow)
        wrapper_layout.addWidget(self.bg_frame, 0, 0)
        
        # 2. Content Layer (Transparent, No Effect)
        self.content_frame = QFrame()
        content_style = """
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
            }
        """
        self.content_frame.setStyleSheet(content_style)
        c_layout = QVBoxLayout(self.content_frame)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)
        wrapper_layout.addWidget(self.content_frame, 0, 0)
        
        # Header
        header = QWidget()
        header.setFixedHeight(30)
        header_style = """
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.9), stop:1 rgba(118, 75, 162, 0.9));
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }
        """
        header.setStyleSheet(header_style)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10,0,10,0)
        
        # Remove minimize button since we have auto-collapse
        btn_close = QPushButton("×")
        btn_close.clicked.connect(self.hide)
        
        btn_close.setFixedSize(20, 20)
        btn_close.setStyleSheet("""
            QPushButton {
                border: none;
                font-weight: bold;
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
            }
        """)
        
        lbl_title = QLabel("🎵 音乐")
        lbl_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: white;
                border: none;
                font-size: 13px;
                padding: 2px;
            }
        """)
        h_layout.addWidget(lbl_title)
        h_layout.addStretch()
        h_layout.addWidget(btn_close)
        c_layout.addWidget(header)
        
        # Content Stack
        self.stack = QStackedWidget()
        c_layout.addWidget(self.stack)
        c_layout.setStretchFactor(self.stack, 1)
        
        if WEB_ENGINE_AVAILABLE:
            try:
                self.web = QWebEngineView()
                s = self.web.settings()
                s.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
                self.web.setHtml(APLAYER_HTML, QUrl("https://music.163.com/"))
                self.stack.addWidget(self.web)
            except:
                error_lbl = QLabel("WebEngine Error")
                error_lbl.setStyleSheet("""
                    QLabel {
                        color: #e74c3c;
                        font-size: 13px;
                        font-weight: bold;
                        padding: 15px;
                        background: rgba(231, 76, 60, 0.1);
                        border-radius: 8px;
                        text-align: center;
                    }
                """)
                self.stack.addWidget(error_lbl)
        else:
            error_lbl = QLabel("WebEngine Unavailable")
            error_lbl.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 15px;
                    background: rgba(231, 76, 60, 0.1);
                    border-radius: 8px;
                    text-align: center;
                }
            """)
            self.stack.addWidget(error_lbl)
            
        layout.addWidget(self.main_wrapper)
        
        # Collapse Handle
        self.handle = QPushButton("🎵", self)
        self.handle.setFixedSize(30, 50)
        handle_gradient = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 8px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                font-size: 18px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #764ba2, stop:1 #667eea);
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """
        self.handle.setStyleSheet(handle_gradient)
        self.handle.clicked.connect(self.expand)
        self.handle.hide()

    def setup_anim(self):
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def expand(self):
        if not self.is_collapsed: return
        
        s = QApplication.primaryScreen().geometry()
        cur = self.geometry()
        
        # Determine target geometry based on dock side
        if self.dock_side == 'left':
            target_x = 0
        elif self.dock_side == 'right':
            target_x = s.width() - self.expanded_w
        else:
            # Should not happen if is_collapsed is True, but fallback
            target_x = cur.x()
            
        geo = QRect(target_x, cur.y(), self.expanded_w, self.h)
        
        self.main_wrapper.show()
        self.handle.hide()
            
        self.anim.setStartValue(cur)
        self.anim.setEndValue(geo)
        self.anim.start()
        self.is_collapsed = False

    def _do_collapse(self):
        if not self.dock_side or self.is_collapsed: return
        
        s = QApplication.primaryScreen().geometry()
        cur = self.geometry()
        
        # Determine target geometry based on dock side
        if self.dock_side == 'left':
            target_x = 0
            # Handle style for left dock (rounded on right)
            self.handle.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border-top-right-radius: 8px;
                    border-bottom-right-radius: 8px;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    font-size: 18px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #764ba2, stop:1 #667eea);
                    border: 2px solid rgba(255, 255, 255, 0.5);
                }
            """)
        else: # right
            target_x = s.width() - self.collapsed_w
            # Handle style for right dock (rounded on left)
            self.handle.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border-top-left-radius: 8px;
                    border-bottom-left-radius: 8px;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    font-size: 18px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #764ba2, stop:1 #667eea);
                    border: 2px solid rgba(255, 255, 255, 0.5);
                }
            """)
            
        geo = QRect(target_x, cur.y(), self.collapsed_w, 50)
        
        self.main_wrapper.hide()
        self.handle.show()
        self.handle.move(0, 0)
            
        self.anim.setStartValue(cur)
        self.anim.setEndValue(geo)
        self.anim.start()
        self.is_collapsed = True

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_pos = e.globalPos() - self.frameGeometry().topLeft()
            self.collapse_timer.stop()
            e.accept()

    def mouseMoveEvent(self, e):
        if self.dragging:
            self.move(e.globalPos() - self.drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e):
        self.dragging = False
        self._check_docking()

    def _check_docking(self):
        # Simple edge detection
        s = QApplication.primaryScreen().geometry()
        x = self.x()
        w = self.width()
        sw = s.width()
        threshold = 20
        
        if x < threshold:
            self.move(0, self.y())
            self.dock_side = 'left'
            self.collapse_timer.start(500)
        elif x + w > sw - threshold:
            self.move(sw - w, self.y())
            self.dock_side = 'right'
            self.collapse_timer.start(500)
        else:
            self.dock_side = None
            if self.is_collapsed:
                self.expand()

    def enterEvent(self, e):
        self.collapse_timer.stop()
        if self.dock_side and self.is_collapsed:
            self.expand()
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self.dock_side and not self.is_collapsed and not self.dragging:
            self.collapse_timer.start(500)
        super().leaveEvent(e)

class MusicPlayerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("音乐播放器")
        self.resize(1024, 768)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        
        # Apply modern gradient background to dialog
        dialog_style = """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
            }
        """
        self.setStyleSheet(dialog_style)
        
        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        
        # Style the stack with glass morphism effect
        stack_style = """
            QStackedWidget {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
        """
        self.stack.setStyleSheet(stack_style)
        layout.addWidget(self.stack)
        
        # Web View
        web_widget = QWidget()
        web_layout = QVBoxLayout(web_widget)
        web_layout.setContentsMargins(15, 15, 15, 15)
        
        # Add modern container for web view
        web_container_style = """
            QWidget {
                background: rgba(255, 255, 255, 0.5);
                border-radius: 10px;
            }
        """
        web_widget.setStyleSheet(web_container_style)
        
        if WEB_ENGINE_AVAILABLE:
            try:
                wv = QWebEngineView()
                wv.settings().setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
                wv.setHtml(APLAYER_HTML, QUrl("https://music.163.com/"))
                web_layout.addWidget(wv)
            except Exception as e:
                error_label = QLabel(f"加载失败：{e}")
                error_label.setStyleSheet("""
                    QLabel {
                        color: #e74c3c;
                        font-size: 13px;
                        font-weight: bold;
                        padding: 15px;
                        background: rgba(231, 76, 60, 0.1);
                        border-radius: 8px;
                        border: 2px solid rgba(231, 76, 60, 0.3);
                    }
                """)
                web_layout.addWidget(error_label)
        else:
            error_label = QLabel(f"内置浏览器组件不可用：{WEB_ENGINE_ERROR or 'Unknown Error'}")
            error_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 15px;
                    background: rgba(231, 76, 60, 0.1);
                    border-radius: 8px;
                    border: 2px solid rgba(231, 76, 60, 0.3);
                }
            """)
            web_layout.addWidget(error_label)
            btn_open = QPushButton("🌐 在系统浏览器中打开")
            btn_open.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #764ba2, stop:1 #667eea);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5b3f8a, stop:1 #5a67d8);
                }
            """)
            btn_open.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.sharelikes.com.cn/")))
            web_layout.addWidget(btn_open)
            
        self.stack.addWidget(web_widget)
        
        # Set initial view
        self.stack.setCurrentIndex(0)
