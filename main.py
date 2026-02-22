import sys
import os
import warnings
import traceback
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QFont

def create_splash_screen():
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "logo.png")
    
    if not os.path.exists(logo_path):
        QMessageBox.critical(None, "启动错误", f"未找到logo.png文件: {logo_path}")
        sys.exit(1)
    
    pixmap = QPixmap(logo_path)
    # 修正：使用正确的 Qt.KeepAspectRatio
    scaled_pixmap = pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    if scaled_pixmap.width() != 600 or scaled_pixmap.height() != 400:
        final_pixmap = QPixmap(600, 400)
        final_pixmap.fill(Qt.white)
        
        # 修正：使用标准的 begin/end 模式管理 QPainter
        painter = QPainter(final_pixmap)
        try:
            x = (600 - scaled_pixmap.width()) // 2
            y = (400 - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.setPen(Qt.darkGray)
            painter.setFont(QFont("Arial", 12))
            painter.drawText(0, 350, 600, 30, Qt.AlignCenter, "正在初始化系统...")
        finally:
            painter.end()
        
        splash = QSplashScreen(final_pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    else:
        splash = QSplashScreen(scaled_pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    
    # 删除重复的 setWindowFlags 调用
    return splash

def initialize_application():
    try:
        from ui.main_window import NABUEEGApp
        return NABUEEGApp
    except ImportError as e:
        traceback.print_exc()
        QMessageBox.critical(None, "导入错误", f"模块导入失败: {str(e)}")
        return None
    except Exception as e:
        traceback.print_exc()
        QMessageBox.critical(None, "初始化错误", f"应用程序初始化失败: {str(e)}")
        return None

def main():
    try:
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Try to enable WebEngine specific attributes
        if hasattr(Qt, 'AA_ShareOpenGLContexts'):
            QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

        # Enable WebEngine Audio
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-features=AudioServiceOutOfProcess --autoplay-policy=no-user-gesture-required"

        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        splash = create_splash_screen()
        splash.show()
        app.processEvents()
        
        align = int(Qt.AlignBottom | Qt.AlignCenter)
        splash.showMessage("正在加载主界面...", align, Qt.white)
        app.processEvents()
        
        splash.showMessage("初始化系统模块...", align, Qt.white)
        app.processEvents()
        
        window_class = initialize_application()
        if window_class is None:
            splash.close()
            return 1
        
        splash.showMessage("创建主界面...", align, Qt.white)
        app.processEvents()
        
        window = window_class()
        window.setWindowFlags(Qt.FramelessWindowHint)
        
        splash.finish(window)
        splash.close()
        
        window.showMaximized()
        return app.exec_()
        
    except Exception as e:
        error_msg = f"应用程序启动失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        QMessageBox.critical(None, "启动错误", error_msg)
        return 1

if __name__ == "__main__":
    sys.exit(main())