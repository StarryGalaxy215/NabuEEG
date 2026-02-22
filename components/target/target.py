import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QFrame, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from common.styles import TITLE_TARGET, IMAGE_LABEL, IMAGE_LABEL_PLACEHOLDER, DETAIL_FRAME

class TargetPointDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("10-20国际脑电电极定位系统")
        self.setFixedSize(600, 750)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # 标题
        title = QLabel("10-20国际脑电电极定位系统")
        title.setFixedHeight(50)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(TITLE_TARGET)
        layout.addWidget(title)
        layout.addSpacing(-10)
        
        # 图片
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(570, 480)
        self.image_label.setStyleSheet(IMAGE_LABEL)
        self._load_image()
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        layout.addSpacing(-5)
        
        # 说明区域
        detail_frame = QFrame()
        detail_frame.setStyleSheet(DETAIL_FRAME)
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(5, 5, 5, 5)
        
        text = QTextEdit()
        text.setFrameStyle(QFrame.NoFrame)
        text.setReadOnly(True)
        text.setHtml("""
        <div style='font-family: "Segoe UI", "Microsoft YaHei";'>
            <div style='background-color: #f8f9fa; padding: 5px; border-bottom: 1px solid #eee; margin-bottom: 8px;'>
                <b style='color: #34495e; font-size: 11pt;'>10-20 系统标注说明</b>
            </div>
            <table style='width: 100%; border-collapse: collapse; font-size: 9pt;'>
                <tr style='color: #7f8c8d;'>
                    <th align='left' style='padding: 4px;'>代码</th>
                    <th align='left' style='padding: 4px;'>脑区含义</th>
                    <th align='left' style='padding: 4px;'>电极示例</th>
                </tr>
                <tr><td style='padding: 4px;'><b>F</b></td><td>额叶 (Frontal)</td><td>F3, F4, Fz</td></tr>
                <tr><td style='padding: 4px;'><b>C</b></td><td>中央区 (Central)</td><td>C3, C4, Cz</td></tr>
                <tr><td style='padding: 4px;'><b>P</b></td><td>顶叶 (Parietal)</td><td>P3, P4, Pz</td></tr>
                <tr><td style='padding: 4px;'><b>O</b></td><td>枕叶 (Occipital)</td><td>O1, O2</td></tr>
                <tr><td style='padding: 4px;'><b>T</b></td><td>颞叶 (Temporal)</td><td>T7, T8</td></tr>
            </table>
        </div>
        """)
        text.setFixedHeight(160)
        detail_layout.addWidget(text)
        layout.addWidget(detail_frame)
        layout.addStretch(1)

    def _load_image(self):
        base_dir = Path(__file__).resolve().parent.parent.parent
        candidates = [
            base_dir / "resources" / "10-20.png",
            Path("10-20.png"),
            Path("images") / "10-20.png",
            Path(__file__).parent / "10-20.png"
        ]
        
        for path in candidates:
            if path.exists():
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    self.image_label.setPixmap(pixmap.scaled(
                        550, 460, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    ))
                    return

        self.image_label.setText("未找到 10-20.png 图片文件\n请确认图片在程序目录下")
        self.image_label.setStyleSheet(IMAGE_LABEL_PLACEHOLDER)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    TargetPointDialog().show()
    sys.exit(app.exec_())
