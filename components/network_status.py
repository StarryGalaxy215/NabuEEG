import socket
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread

class ConnectionChecker(QThread):
    status_signal = pyqtSignal(bool)

    def run(self):
        # Try connecting to reliable DNS servers (AliDNS, 114DNS)
        servers = [("223.5.5.5", 53), ("114.114.114.114", 53)]
        for server in servers:
            try:
                # Reduced timeout to 0.5s for faster feedback
                socket.create_connection(server, timeout=0.5)
                self.status_signal.emit(True)
                return
            except OSError:
                continue
        self.status_signal.emit(False)

class NetworkStatusLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.ArrowCursor)
        self.connected = False

        self._styles = {
            True: ("🌐 已连接互联网", "#27ae60", "#eafaf1", "网络连接正常"),
            False: ("🚫 未连接互联网", "#e74c3c", "#fdedec", "请检查网络连接")
        }
        
        self._style_tpl = (
            "QLabel {{ color: {0}; border: 1px solid {0}; background-color: {1}; "
            "font-family: 'Microsoft YaHei'; font-size: 12px; font-weight: bold; "
            "padding: 4px 12px; border-radius: 12px; }}"
        )

        self.checker = ConnectionChecker()
        self.checker.status_signal.connect(self._update_state)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.checker.start)
        self.timer.start(2000)  # Check every 2 seconds
        
        self.checker.start()
        self._update_ui(False)

    def _update_state(self, is_connected):
        self.connected = is_connected
        self._update_ui(is_connected)

    def _update_ui(self, is_connected):
        text, color, bg, tooltip = self._styles[is_connected]
        self.setText(text)
        self.setStyleSheet(self._style_tpl.format(color, bg))
        self.setToolTip(tooltip)

    def mousePressEvent(self, event):
        pass
