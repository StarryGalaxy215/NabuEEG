# config.py - 应用配置
import os
import sys
from pathlib import Path

# 应用配置
APP_NAME = "NabuEEG脑电信号采集分析一体化智能诊断系统"
VERSION = "1.1"
SAMPLING_RATE = 250

# 路径配置
APP_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
LOGO_PATH = str(APP_DIR / "resources" / "logo.png")

# 样式配置
STYLES = {
    'title': "font-size: 24pt; font-weight: bold; margin: 20px; color: #2c3e50;",
    'description': "font-size: 12pt; margin: 15px; color: #7f8c8d;",
    'group_box': (
        "QGroupBox { font-size: 14pt; font-weight: bold; margin-top: 10px; padding-top: 10px; "
        "border: 2px solid #cccccc; border-radius: 5px; } "
        "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }"
    ),
    'button': (
        "QPushButton { font-size: 12pt; padding: 15px; margin: 8px; "
        "border: 2px solid #cccccc; border-radius: 8px; font-weight: bold; } "
        "QPushButton:hover { background-color: #e6e6e6; } "
        "QPushButton:pressed { background-color: #d4d4d4; }"
    )
}
