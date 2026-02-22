class Colors:
    # 基礎色
    BLACK, WHITE = "#000000", "#ffffff"
    RED = "red"
    
    # 灰色系
    GRAY_666 = "#666666"
    GRAY_666_ALT = GRAY_666
    GRAY_777, GRAY_888, GRAY_999 = "#777777", "#888888", "#999999"
    GRAY_AAA, GRAY_BBB, GRAY_CCC = "#a0a0a0", "#b3b3b3", "#cccccc"
    GRAY_DDD, GRAY_EEE, GRAY_E0 = "#dddddd", "#eee", "#e0e0e0"
    GRAY_E8, GRAY_D4, GRAY_D0 = "#e8f5e8", "#d4d4d4", "#d0d0d0"
    GRAY_C0, GRAY_DC, GRAY_DE = "#c0c0c0", "#dcdde1", "#dee2e6"
    GRAY_F0, GRAY_F2 = "#f0f0f0", "#f2f2f2"
    
    # 主色
    PRIMARY, SECONDARY = "#2c3e50", "#34495e"
    MUTED, BORDER = "#7f8c8d", "#bdc3c7"
    
    # 功能色 (Normal, Hover, Pressed/Alt)
    BLUE = "#3498db"
    BLUE_HOVER, BLUE_PRESSED = "#2980b9", "#21618c"
    
    GREEN = "#27ae60"
    GREEN_HOVER = "#229954"
    GREEN_ALT, GREEN_HOVER_ALT = "#4CAF50", "#45a049"
    
    ORANGE = "#f39c12"
    ORANGE_DARK, ORANGE_HOVER = "#d35400", "#e67e22"
    ORANGE_ALT = ORANGE_ALT2 = "#ff9800"
    YELLOW, YELLOW_WARN, YELLOW_BG = "#ffd700", "#ffc107", "#fff3cd"
    
    RED_DARK = "#e74c3c"
    RED_HOVER, RED_PRESSED = "#c0392b", "#cc0000"
    RED_ALT, RED_HOVER_ALT = "#f44336", "#da190b"
    RED_BRIGHT, RED_BORDER = "#ff4444", "#ff0000"
    
    PURPLE = "#9b59b6"
    PURPLE_HOVER, PURPLE_PRESSED = "#8e44ad", "#71368a"
    TEAL = "#16a085"
    
    # 背景
    BG_LIGHT, BG_MAIN, BG_PANEL = "#f5f6fa", "#f5f7fa", "#f8f9fa"
    BG_CARD, BG_CONSOLE = "#ecf0f1", "#1e1e1e"
    CONSOLE_TEXT = "#00ff00"
    
    # 按鈕
    BTN_GRAY, BTN_GRAY_HOVER = "#95a5a6", "#7f8c8d"
    BTN_DISABLED, BTN_DISABLED_TEXT = "#bdc3c7", "#7f8c8d"
    
    # 左側按鈕配色 (BG, Border)
    BTN_SAMPLING_BG, BTN_SAMPLING_BORDER = "#d9ffd9", "#99e699"
    BTN_PREPROCESS_BG, BTN_PREPROCESS_BORDER = "#fff0d9", "#ffcc99"
    BTN_FEATURE_BG, BTN_FEATURE_BORDER = "#d9f0ff", "#99ccff"
    BTN_DIAGNOSIS_BG, BTN_DIAGNOSIS_BORDER = "#ffffff", "#9b59b6"
    BTN_CLEAR_BG, BTN_CLEAR_BORDER = "#e0e0e0", "#b3b3b3"
    BTN_ICA_BG, BTN_ICA_BORDER = "#e0f2f1", "#4db6ac"
    BTN_SEGMENT_BG, BTN_SEGMENT_BORDER = "#f5e0d9", "#d4a574"
    
    # Tokyo Night 主题配色
    TOKYO_CYAN = "#7aa2f7"
    TOKYO_CYAN_HOVER = "#5d8fe6"
    TOKYO_BLUE = "#2ac3de"
    TOKYO_BLUE_HOVER = "#1ba3c0"
    TOKYO_PURPLE = "#bb9af7"
    TOKYO_PURPLE_HOVER = "#a583e6"
    TOKYO_PINK = "#f7768e"
    TOKYO_PINK_HOVER = "#e05a73"
    TOKYO_GREEN = "#9ece6a"
    TOKYO_GREEN_HOVER = "#82b54d"
    TOKYO_ORANGE = "#ff9e64"
    TOKYO_ORANGE_HOVER = "#e8854a"
    TOKYO_YELLOW = "#e0af68"
    TOKYO_YELLOW_HOVER = "#c9964f"
    TOKYO_RED = "#f7768e"
    TOKYO_RED_HOVER = "#e05a73"
    TOKYO_TEAL = "#73daca"
    TOKYO_TEAL_HOVER = "#5bc4b2"
    
    # 報告狀態
    STATUS_EXCELLENT, STATUS_GOOD = "#8527ae", "#27ae60"
    STATUS_NORMAL, STATUS_BAD = "#e74c3c", "#c0392b"


# ==================== 樣式生成輔助 ====================
def _btn(bg, hover=None, pressed=None, color="white", radius="4px", pad="5px", font="bold 9pt", extra=""):
    """生成按鈕樣式"""
    base = f"background-color: {bg}; color: {color}; border-radius: {radius}; padding: {pad}; font-weight: bold; font-size: {font.replace('bold ', '')}; {extra}"
    s = f"QPushButton {{ {base} }}"
    if hover: s += f" QPushButton:hover {{ background-color: {hover}; }}"
    if pressed: s += f" QPushButton:pressed {{ background-color: {pressed}; }}"
    return s

def _btn_ctrl(bg, hover):
    """生成控制按鈕樣式 (Start/Pause/Stop)"""
    return _btn(bg, hover, radius="6px", font="11pt") + \
           f" QPushButton:disabled {{ background-color: {Colors.BTN_DISABLED}; color: {Colors.BTN_DISABLED_TEXT}; }}"

# ==================== 樣式常量 ====================

# --- 背景 ---
BG_DIALOG = f"background-color: {Colors.BG_LIGHT};"
BG_MAIN_WINDOW = f"""
    QMainWindow {{ background-color: {Colors.BG_MAIN}; color: {Colors.BLACK}; }}
    QWidget {{ color: {Colors.BLACK}; font-family: "Microsoft YaHei", Arial, sans-serif; }}
    QLabel {{ color: {Colors.BLACK}; font-size: 11pt; }}
    QPushButton {{ color: {Colors.BLACK}; font-size: 12pt; font-weight: bold; }}
    QGroupBox {{ color: {Colors.BLACK}; font-weight: bold; font-size: 12pt; }}
    QStatusBar {{ color: {Colors.BLACK}; font-size: 10pt; }}
    QMenuBar {{ color: {Colors.BLACK}; font-size: 10pt; background-color: {Colors.BG_MAIN}; }}
    QMenuBar::item {{ padding: 4px 12px; background-color: transparent; color: {Colors.BLACK}; border: 1px solid transparent; border-radius: 3px; margin: 2px; }}
    QMenuBar::item:hover {{ background-color: {Colors.GRAY_CCC}; color: {Colors.BLACK}; border: 1px solid {Colors.GRAY_999}; }}
    QMenuBar::item:pressed {{ background-color: {Colors.GRAY_BBB}; color: {Colors.BLACK}; }}
    QMenuBar::item:selected {{ background-color: {Colors.GRAY_CCC}; color: {Colors.BLACK}; }}
    QTextEdit {{ background-color: {Colors.WHITE}; color: {Colors.BLACK}; font-size: 10pt; padding: 10px; border: 2px solid {Colors.YELLOW}; border-radius: 8px; font-weight: bold; }}
"""

BG_MAIN_WINDOW_DARK = f"""
    QMainWindow {{ background-color: #2b2b2b; color: {Colors.WHITE}; }}
    QWidget {{ color: {Colors.WHITE}; font-family: "Microsoft YaHei", Arial, sans-serif; }}
    QLabel {{ color: {Colors.WHITE}; font-size: 11pt; }}
    QPushButton {{ color: {Colors.WHITE}; font-size: 12pt; font-weight: bold; }}
    QGroupBox {{ color: {Colors.WHITE}; font-weight: bold; font-size: 12pt; }}
    QStatusBar {{ color: {Colors.WHITE}; font-size: 10pt; background-color: #2b2b2b; }}
    QMenuBar {{ color: {Colors.WHITE}; font-size: 10pt; background-color: #2b2b2b; }}
    QMenuBar::item {{ padding: 4px 12px; background-color: transparent; color: {Colors.WHITE}; border: 1px solid transparent; border-radius: 3px; margin: 2px; }}
    QMenuBar::item:hover {{ background-color: #444444; color: {Colors.WHITE}; border: 1px solid {Colors.GRAY_666}; }}
    QMenuBar::item:pressed {{ background-color: #555555; color: {Colors.WHITE}; }}
    QMenuBar::item:selected {{ background-color: #444444; color: {Colors.WHITE}; }}
    QTextEdit {{ background-color: #333333; color: {Colors.WHITE}; font-size: 10pt; padding: 10px; border: 2px solid {Colors.YELLOW}; border-radius: 8px; font-weight: bold; }}
"""

BG_RIGHT_PANEL = f"""
    QWidget {{ color: {Colors.BLACK}; font-family: "Microsoft YaHei", Arial, sans-serif; }}
    QLabel {{ color: {Colors.BLACK}; font-size: 11pt; }}
    QGroupBox {{ color: {Colors.BLACK}; font-weight: bold; font-size: 12pt; border: 2px solid {Colors.GRAY_CCC}; border-radius: 8px; margin-top: 10px; padding-top: 15px; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; color: {Colors.BLACK}; }}
    QTextEdit {{ color: {Colors.BLACK}; font-size: 10pt; background-color: white; border: 1px solid {Colors.GRAY_CCC}; border-radius: 4px; }}
    QTabWidget::pane {{ border: 1px solid {Colors.GRAY_CCC}; border-radius: 4px; background-color: white; }}
    QTabBar::tab {{ background-color: {Colors.GRAY_F0}; color: {Colors.BLACK}; padding: 8px 16px; margin-right: 2px; border: 1px solid {Colors.GRAY_CCC}; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }}
    QTabBar::tab:selected {{ background-color: white; color: {Colors.BLACK}; border-bottom: 1px solid white; }}
"""

BG_DIALOG_RESOURCE = f"QDialog {{ background-color: {Colors.BG_PANEL}; }}"

# --- QGroupBox ---
GROUP_BOX_SMALL = f"QGroupBox {{ font-weight: bold; font-size: 9pt; border: 1px solid {Colors.BORDER}; border-radius: 5px; margin-top: 5px; }} QGroupBox::title {{ subcontrol-origin: margin; padding: 0 5px; background-color: {Colors.BG_LIGHT}; }}"
GROUP_BOX_CONFIG = f"QGroupBox {{ font-weight: bold; color: {Colors.SECONDARY}; font-size: 11pt; margin-top: 8px; border: none; }} QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: 0 8px; background-color: transparent; }}"
GROUP_BOX_MAIN = f"QGroupBox {{ font-size: 12pt; font-weight: bold; margin-top: 10px; padding-top: 15px; padding-bottom: 5px; border: 2px solid {Colors.GRAY_CCC}; border-radius: 8px; background-color: {Colors.BG_PANEL}; color: {Colors.BLACK}; }} QGroupBox::title {{ subcontrol-origin: margin; left: 15px; padding: 0 10px 0 10px; color: {Colors.BLACK}; }}"

# --- QListWidget ---
LIST_WIDGET_FEATURE = f"""
    QListWidget {{ background-color: white; alternate-background-color: {Colors.GRAY_F0}; selection-background-color: {Colors.GREEN_ALT}; selection-color: white; outline: none; }}
    QListWidget::item {{ padding: 5px; border-bottom: 1px solid {Colors.GRAY_E0}; }}
    QListWidget::item:selected {{ background-color: {Colors.GREEN_ALT}; color: white; }}
    QListWidget::item:hover {{ background-color: {Colors.GRAY_E8}; }}
"""

# --- 輸入控件 ---
COMBO_BOX_BASE = "QComboBox { font-size: 10pt; background-color: white; border: none; border-radius: 3px; padding: 2px; } QComboBox::drop-down { border: none; }"
SPIN_BOX_BASE = "QSpinBox { font-size: 10pt; background-color: white; border: none; border-radius: 3px; }"
LINE_EDIT_BASE = "QLineEdit { font-size: 10pt; background-color: white; border: none; border-radius: 3px; padding: 5px; }"

# --- 按鈕 ---
BTN_BLUE_SMALL = _btn(Colors.BLUE, Colors.BLUE_HOVER)
BTN_ORANGE_SMALL = _btn(Colors.ORANGE, Colors.ORANGE_HOVER)
BTN_GREEN_SMALL = _btn(Colors.GREEN, Colors.GREEN_HOVER)
BTN_RED_SMALL = _btn(Colors.RED_DARK, Colors.RED_HOVER)
BTN_GRAY_SMALL = _btn(Colors.BTN_GRAY, Colors.BTN_GRAY_HOVER)

BTN_START = _btn_ctrl(Colors.GREEN, Colors.GREEN_HOVER)
BTN_PAUSE = _btn_ctrl(Colors.ORANGE, Colors.ORANGE_HOVER)
BTN_STOP = _btn_ctrl(Colors.RED_DARK, Colors.RED_HOVER)

# Flat Buttons (Padding variants)
BTN_SUCCESS_8 = f"background-color: {Colors.GREEN_ALT}; color: white; padding: 8px;"
BTN_WARNING_8 = f"background-color: {Colors.ORANGE_ALT}; color: white; padding: 8px;"
BTN_PRIMARY_8 = "background-color: #2196F3; color: white; padding: 8px;"
BTN_DANGER_8 = f"background-color: {Colors.RED_ALT}; color: white; padding: 8px;"

BTN_PRIMARY_5 = "QPushButton { background-color: #2196F3; color: white; padding: 5px; }"
BTN_WARNING_5 = f"QPushButton {{ background-color: {Colors.ORANGE_ALT}; color: white; padding: 5px; }}"
BTN_SUCCESS_16 = f"QPushButton {{ background-color: {Colors.GREEN_ALT}; color: white; padding: 8px 16px; }}"
BTN_DANGER_16 = f"QPushButton {{ background-color: {Colors.RED_ALT}; color: white; padding: 8px 16px; }}"
BTN_DANGER_16_HOVER = _btn(Colors.RED_ALT, Colors.RED_HOVER_ALT, pad="8px 16px")

# Dialog Buttons
BTN_ABOUT_CLOSE = _btn(Colors.GREEN_ALT, Colors.GREEN_HOVER_ALT, pad="8px 16px", font="14px", extra="border: none;")
BTN_RESOURCE_CLOSE = _btn(Colors.BLUE, Colors.BLUE_HOVER, Colors.BLUE_PRESSED, radius="6px", pad="10px 25px", font="12pt", extra="border: none; margin: 5px;")

# Panel Buttons
BTN_EXPORT_HTML = _btn(Colors.PURPLE, Colors.PURPLE_HOVER, Colors.PURPLE_PRESSED, pad="8px 16px", extra="border: none;")
BTN_EXPORT_PDF = _btn(Colors.BLUE, Colors.BLUE_HOVER, Colors.BLUE_PRESSED, pad="8px 16px", extra="border: none;")
BTN_PRINT = _btn(Colors.GREEN, "#219653", "#1e8449", pad="8px 16px", extra="border: none;")

# Tokyo Night 风格按钮 (诊断报告)
BTN_TOKYO_CYAN = _btn(Colors.TOKYO_CYAN, Colors.TOKYO_CYAN_HOVER, pad="6px 12px", font="10pt", extra="border: none; color: #1a1b26; font-weight: bold;")
BTN_TOKYO_BLUE = _btn(Colors.TOKYO_BLUE, Colors.TOKYO_BLUE_HOVER, pad="6px 12px", font="10pt", extra="border: none; color: #1a1b26; font-weight: bold;")
BTN_TOKYO_PURPLE = _btn(Colors.TOKYO_PURPLE, Colors.TOKYO_PURPLE_HOVER, pad="6px 12px", font="10pt", extra="border: none; color: #1a1b26; font-weight: bold;")
BTN_TOKYO_PINK = _btn(Colors.TOKYO_PINK, Colors.TOKYO_PINK_HOVER, pad="6px 12px", font="10pt", extra="border: none; color: #1a1b26; font-weight: bold;")
BTN_TOKYO_GREEN = _btn(Colors.TOKYO_GREEN, Colors.TOKYO_GREEN_HOVER, pad="6px 12px", font="10pt", extra="border: none; color: #1a1b26; font-weight: bold;")
BTN_TOKYO_ORANGE = _btn(Colors.TOKYO_ORANGE, Colors.TOKYO_ORANGE_HOVER, pad="6px 12px", font="10pt", extra="border: none; color: #1a1b26; font-weight: bold;")
BTN_TOKYO_YELLOW = _btn(Colors.TOKYO_YELLOW, Colors.TOKYO_YELLOW_HOVER, pad="6px 12px", font="10pt", extra="border: none; color: #1a1b26; font-weight: bold;")
BTN_TOKYO_TEAL = _btn(Colors.TOKYO_TEAL, Colors.TOKYO_TEAL_HOVER, pad="6px 12px", font="10pt", extra="border: none; color: #1a1b26; font-weight: bold;")
BTN_TOKYO_RED = _btn(Colors.TOKYO_RED, Colors.TOKYO_RED_HOVER, pad="6px 12px", font="10pt", extra="border: none; color: #1a1b26; font-weight: bold;")

# Window Control
_win_btn = lambda bg_h, bd_h, c_h, bg_p: f"""
    QPushButton {{ background-color: transparent; border: 1px solid {Colors.GRAY_CCC}; border-radius: 3px; font-size: 14pt; font-weight: bold; color: {Colors.BLACK}; }}
    QPushButton:hover {{ background-color: {bg_h}; border: 1px solid {bd_h}; color: {c_h}; }}
    QPushButton:pressed {{ background-color: {bg_p}; }}
"""
BTN_WINDOW_MINIMIZE = _win_btn(Colors.GRAY_E0, Colors.GRAY_999, Colors.BLACK, Colors.GRAY_D0)
BTN_WINDOW_CLOSE = _win_btn(Colors.RED_BRIGHT, Colors.RED_BORDER, "white", Colors.RED_PRESSED)

BTN_MAIN_BASE = f"""
    QPushButton {{ font-size: 12pt; padding: 15px 20px; margin: 8px; border-radius: 8px; font-weight: bold; text-align: left; color: {Colors.BLACK}; min-height: 25px; }}
    QPushButton:hover {{ background-color: #e6e6e6; border: 2px solid {Colors.GRAY_999}; color: {Colors.BLACK}; }}
    QPushButton:pressed {{ background-color: {Colors.GRAY_D4}; color: {Colors.BLACK}; }}
"""

# --- 標籤 / 字體 ---
FONT_SMALL_9PT = "font-size: 9pt;"
FONT_SMALL_9PT_PADDING = "font-size: 9pt; padding: 2px;"
LABEL_BOLD_INFO = f"font-weight: bold; color: {Colors.PRIMARY}; margin: 10px;"
LABEL_PATH_SELECTED = f"color: {Colors.PRIMARY}; font-weight: bold;"
LABEL_FONT_BOLD = "font-size: 10pt; font-weight: bold;"

# --- 其他組件 ---
CONSOLE_STYLE = f"QTextEdit {{ background-color: {Colors.BG_CONSOLE}; color: {Colors.CONSOLE_TEXT}; font-family: 'Consolas', 'Monaco'; font-size: 9pt; border: none; padding: 4px; border-radius: 3px; }}"
PROGRESS_BAR = f"QProgressBar {{ text-align: center; background-color: {Colors.BG_CARD}; font-size: 9pt; border: none; border-radius: 4px; }} QProgressBar::chunk {{ background-color: {Colors.BLUE}; border-radius: 3px; }}"
HEADER_CYTON = f"QLabel {{ font-size: 18pt; font-weight: bold; color: {Colors.PRIMARY}; margin: 10px; padding: 8px; background-color: {Colors.BG_CARD}; border-radius: 6px; border: none; }}"
TITLE_MAIN = f"font-size: 20pt; font-weight: bold; margin: 10px; color: {Colors.BLACK}; padding: 15px; background-color: white; border: 2px solid {Colors.BLACK}; border-radius: 10px;"
TITLE_RESOURCE = f"font-size: 18pt; font-weight: bold; color: {Colors.PRIMARY}; margin: 10px; padding: 12px; background-color: {Colors.BG_CARD}; border-radius: 10px; border: 2px solid {Colors.BLUE};"

TEXT_BROWSER = f"""
    QTextBrowser {{ background-color: white; border: 2px solid {Colors.GRAY_D0}; border-radius: 8px; padding: 5px; font-size: 10pt; }}
    QScrollBar:vertical {{ border: none; background-color: {Colors.GRAY_F0}; width: 12px; border-radius: 6px; }}
    QScrollBar::handle:vertical {{ background-color: {Colors.GRAY_C0}; border-radius: 6px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background-color: {Colors.GRAY_AAA}; }}
"""

NO_LOGO_LABEL = "color: red; font-weight: bold;"
VERSION_LABEL = f"QLabel {{ color: {Colors.GRAY_666}; font-size: 10pt; font-weight: bold; padding: 5px; }}"
COPYRIGHT_LABEL = f"QLabel {{ color: {Colors.GRAY_888}; font-size: 9pt; font-style: italic; padding: 3px; }}"
TEAM_LABEL = f"QLabel {{ color: {Colors.GRAY_777}; font-size: 9pt; padding: 2px; }}"
SEPARATOR = f"QLabel {{ background-color: {Colors.GRAY_DDD}; max-height: 1px; margin: 5px 0px; }}"
STATUS_LABEL = f"color: {Colors.BLACK}; padding: 5px 10px; font-style: italic; font-size: 10pt;"
STATUS_LABEL_DARK = f"color: {Colors.WHITE}; padding: 5px 10px; font-style: italic; font-size: 10pt;"

BEIJING_TIME_LABEL = f"font-weight: bold; color: {Colors.BLACK}; padding: 5px 10px; background-color: {Colors.BG_CARD}; border-radius: 5px; border: 1px solid {Colors.BORDER}; font-size: 10pt;"
BEIJING_TIME_LABEL_DARK = f"font-weight: bold; color: {Colors.WHITE}; padding: 5px 10px; background-color: #333; border-radius: 5px; border: 1px solid #555; font-size: 10pt;"

INFO_LABEL_RIGHT = f"font-size: 12pt; color: {Colors.BLACK}; padding: 10px; font-weight: bold; background-color: {Colors.BG_PANEL}; border-radius: 4px;"
DIAGNOSIS_TEXT = f"QTextEdit {{ background-color: {Colors.WHITE}; color: {Colors.BLACK}; font-size: 10pt; padding: 10px; border: 1px solid {Colors.GRAY_CCC}; }}"

# analyzer
LABEL_PLACEHOLDER = "color: #666; font-style: italic; min-width: 200px;"
BTN_PADDING_SMALL = "padding: 5px 10px;"
STATUS_LABEL_ANALYZER = "font-size: 12pt; margin: 10px;"
DETAIL_LABEL = "color: #666; margin: 5px;"

BTN_ANALYZE = _btn(Colors.GREEN_ALT, Colors.GREEN_HOVER_ALT, pad="10px 20px", font="14px", radius="5px")
BTN_ANALYZE_CANCEL = _btn(Colors.RED_ALT, Colors.RED_HOVER_ALT, pad="10px 20px", font="14px", radius="5px")

# target
TITLE_TARGET = f"QLabel {{ font-size: 16pt; font-weight: bold; color: {Colors.PRIMARY}; background-color: {Colors.BG_CARD}; border-radius: 5px; border: 1px solid {Colors.BORDER}; }}"
IMAGE_LABEL = "border: none; margin: 0px; padding: 0px;"
IMAGE_LABEL_PLACEHOLDER = f"background-color: {Colors.BG_PANEL}; border: 1px dashed {Colors.BORDER}; color: {Colors.MUTED};"
DETAIL_FRAME = f"QFrame {{ border: 1px solid {Colors.GRAY_DC}; background-color: {Colors.WHITE}; border-radius: 8px; padding: 2px; }}"
