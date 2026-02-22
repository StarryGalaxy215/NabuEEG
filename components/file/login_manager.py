import re
import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QApplication,
                             QCheckBox, QFrame, QButtonGroup, QWidget, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

class LoginManager:
    def __init__(self, filepath="users.json"):
        self.users_file = Path(filepath)
        self.login_attempts = {}  # 记录登录尝试次数

    def _load_users(self):
        if not self.users_file.exists():
            return {}
        try:
            return json.loads(self.users_file.read_text(encoding='utf-8'))
        except Exception:
            return {}

    def _save_users(self, users):
        try:
            self.users_file.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding='utf-8')
            return True
        except Exception as e:
            print(f"Save failed: {e}")
            return False

    def validate_email(self, email):
        """验证邮箱格式"""
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

    def validate_password_strength(self, password):
        """验证密码强度，返回 (是否有效，强度等级，提示信息)"""
        if len(password) < 8:
            return False, 0, "密码长度至少 8 位"
        
        # 检查是否只包含字母
        is_only_alpha = password.isalpha()
        # 检查是否只包含数字
        is_only_digit = password.isdigit()
        
        # 如果只包含字母或只包含数字，强度不足
        if is_only_alpha or is_only_digit:
            return False, 1, "密码需包含字母和数字的组合"
        
        strength = 0
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        strength = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength < 2:
            return False, strength, "密码需包含大小写字母、数字或特殊符号中的至少两种"
        
        return True, strength, "密码强度符合要求"

    def _hash(self, password):
        """SHA256 加密密码"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, email, password, remember_me=False):
        """用户认证，支持防暴力破解"""
        # 检查是否被临时锁定
        if email in self.login_attempts and self.login_attempts[email] >= 5:
            return False, "账户已锁定，请 10 分钟后再试"
        
        users = self._load_users()
        if email not in users:
            self.login_attempts[email] = self.login_attempts.get(email, 0) + 1
            if self.login_attempts[email] >= 5:
                QTimer.singleShot(600000, lambda: self.login_attempts.pop(email, None))  # 10 分钟后重置
            return False, "邮箱或密码错误"
        
        if users[email]['password'] != self._hash(password):
            self.login_attempts[email] = self.login_attempts.get(email, 0) + 1
            if self.login_attempts[email] >= 5:
                QTimer.singleShot(600000, lambda: self.login_attempts.pop(email, None))
            return False, "邮箱或密码错误"
        
        # 登录成功
        users[email]['last_login'] = datetime.now().isoformat()
        if remember_me:
            users[email]['remember_me'] = True
        self._save_users(users)
        return True, "登录成功"

    def register(self, email, password, confirm_password):
        """用户注册"""
        if not self.validate_email(email):
            return False, "邮箱格式不正确"
        
        is_valid, strength, msg = self.validate_password_strength(password)
        if not is_valid:
            return False, msg
        
        if password != confirm_password:
            return False, "两次输入的密码不一致"
        
        users = self._load_users()
        if email in users:
            return False, "该邮箱已被注册"
        
        users[email] = {
            'password': self._hash(password),
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'password_strength': strength
        }
        return (True, "注册成功") if self._save_users(users) else (False, "注册失败")

    def change_password(self, email, old_password, new_password, confirm_password):
        """修改密码"""
        if not self.authenticate(email, old_password)[0]:
            return False, "原密码错误"
        
        is_valid, strength, msg = self.validate_password_strength(new_password)
        if not is_valid:
            return False, msg
        
        if new_password != confirm_password:
            return False, "两次输入的新密码不一致"
        
        users = self._load_users()
        users[email]['password'] = self._hash(new_password)
        users[email]['password_strength'] = strength
        return (True, "密码修改成功") if self._save_users(users) else (False, "修改失败")


class ModernLineEdit(QLineEdit):
    """现代化的输入框"""
    def __init__(self, placeholder="", echo_mode=QLineEdit.Normal, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setEchoMode(echo_mode)
        self.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
                font-size: 14px;
                font-family: 'Microsoft YaHei', 'SimHei', Arial;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
                background-color: #ffffff;
            }
            QLineEdit:hover {
                border: 2px solid #bdbdbd;
            }
        """)


class ModernButton(QPushButton):
    """现代化的按钮"""
    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#4CAF50' if primary else '#f5f5f5'};
                color: {'white' if primary else '#333333'};
                border: {'none' if primary else '2px solid #e0e0e0'};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'SimHei', Arial;
            }}
            QPushButton:hover {{
                background-color: {'#45a049' if primary else '#e8e8e8'};
            }}
            QPushButton:pressed {{
                background-color: {'#3d8b40' if primary else '#d0d0d0'};
            }}
        """)


class PasswordStrengthIndicator(QWidget):
    """密码强度指示器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(5)
        
        self.bars = []
        colors = ['#f44336', '#ff9800', '#ffeb3b', '#4CAF50']
        for i in range(4):
            bar = QFrame()
            bar.setFixedHeight(4)
            bar.setStyleSheet(f"background-color: {colors[i]}; border-radius: 2px;")
            bar.setEnabled(False)
            layout.addWidget(bar)
            self.bars.append(bar)
    
    def update_strength(self, strength):
        for i, bar in enumerate(self.bars):
            bar.setEnabled(i < strength)


class LoginTab(QWidget):
    """登录标签页"""
    login_success = pyqtSignal(dict)
    
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setup_ui()
    
    def setup_ui(self):
        # 使用 setLayout 来设置独立布局，而不是直接操作父布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # 邮箱输入
        email_label = QLabel("📧 邮箱")
        email_label.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        main_layout.addWidget(email_label)
        
        self.email_input = ModernLineEdit("请输入邮箱地址")
        main_layout.addWidget(self.email_input)
        
        # 密码输入
        password_label = QLabel("🔒 密码")
        password_label.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        main_layout.addWidget(password_label)
        
        self.password_input = ModernLineEdit("请输入密码", QLineEdit.Password)
        main_layout.addWidget(self.password_input)
        
        # 记住我和忘记密码
        options_layout = QHBoxLayout()
        self.remember_checkbox = QCheckBox("记住我")
        self.remember_checkbox.setStyleSheet("QCheckBox { color: #666; font-size: 13px; }")
        options_layout.addWidget(self.remember_checkbox)
        options_layout.addStretch()
        self.forgot_btn = QPushButton("忘记密码？")
        self.forgot_btn.setStyleSheet("QPushButton { background: none; border: none; color: #4CAF50; text-decoration: underline; font-size: 13px; }")
        self.forgot_btn.clicked.connect(self.show_forgot_password)
        options_layout.addWidget(self.forgot_btn)
        main_layout.addLayout(options_layout)
        
        # 登录按钮
        self.login_btn = ModernButton("登 录")
        self.login_btn.clicked.connect(self.handle_login)
        main_layout.addWidget(self.login_btn)
        
        # 添加弹性空间
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # 回车键登录
        self.password_input.returnPressed.connect(self.handle_login)
    
    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "提示", "请输入邮箱和密码")
            return
        
        if not self.manager.validate_email(email):
            QMessageBox.warning(self, "提示", "邮箱格式不正确")
            return
        
        success, msg = self.manager.authenticate(email, password, self.remember_checkbox.isChecked())
        if success:
            user_info = {"email": email, "username": email.split('@')[0], "remember_me": self.remember_checkbox.isChecked()}
            self.login_success.emit(user_info)
        else:
            QMessageBox.warning(self, "登录失败", msg)
    
    def show_forgot_password(self):
        QMessageBox.information(self, "提示", "请联系管理员重置密码")


class RegisterTab(QWidget):
    """注册标签页"""
    register_success = pyqtSignal()
    
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setup_ui()
    
    def setup_ui(self):
        # 使用 setLayout 来设置独立布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # 邮箱输入
        email_label = QLabel("📧 邮箱")
        email_label.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        main_layout.addWidget(email_label)
        
        self.email_input = ModernLineEdit("请输入邮箱地址")
        main_layout.addWidget(self.email_input)
        
        # 密码输入
        password_label = QLabel("🔒 密码")
        password_label.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        main_layout.addWidget(password_label)
        
        self.password_input = ModernLineEdit("请输入密码（至少 8 位，包含大小写字母、数字或特殊符号）", QLineEdit.Password)
        self.password_input.textChanged.connect(self.check_password_strength)
        main_layout.addWidget(self.password_input)
        
        # 密码强度指示器
        self.strength_indicator = PasswordStrengthIndicator()
        main_layout.addWidget(self.strength_indicator)
        
        # 确认密码
        confirm_label = QLabel("🔒 确认密码")
        confirm_label.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        main_layout.addWidget(confirm_label)
        
        self.confirm_input = ModernLineEdit("请再次输入密码", QLineEdit.Password)
        main_layout.addWidget(self.confirm_input)
        
        # 注册协议
        self.agree_checkbox = QCheckBox("我已阅读并同意《用户服务协议》和《隐私政策》")
        self.agree_checkbox.setStyleSheet("QCheckBox { color: #666; font-size: 13px; }")
        main_layout.addWidget(self.agree_checkbox)
        
        # 注册按钮
        self.register_btn = ModernButton("注 册", primary=True)
        self.register_btn.clicked.connect(self.handle_register)
        main_layout.addWidget(self.register_btn)
        
        # 添加弹性空间
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # 回车键注册
        self.confirm_input.returnPressed.connect(self.handle_register)
    
    def check_password_strength(self, text):
        is_valid, strength, _ = self.manager.validate_password_strength(text)
        self.strength_indicator.update_strength(strength if is_valid else 0)
    
    def handle_register(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        if not email or not password or not confirm:
            QMessageBox.warning(self, "提示", "请填写所有字段")
            return
        
        if not self.agree_checkbox.isChecked():
            QMessageBox.warning(self, "提示", "请先同意用户服务协议")
            return
        
        success, msg = self.manager.register(email, password, confirm)
        if success:
            QMessageBox.information(self, "注册成功", msg)
            self.register_success.emit()
        else:
            QMessageBox.warning(self, "注册失败", msg)


class ChangePasswordDialog(QDialog):
    """修改密码对话框"""
    def __init__(self, email, manager, parent=None):
        super().__init__(parent)
        self.email = email
        self.manager = manager
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("修改密码")
        self.setModal(True)
        self.setFixedSize(400, 350)
        self.setStyleSheet("QDialog { background-color: #ffffff; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = QLabel("🔐 修改密码")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 原密码
        layout.addWidget(QLabel("原密码"))
        self.old_password_input = ModernLineEdit("请输入原密码", QLineEdit.Password)
        layout.addWidget(self.old_password_input)
        
        # 新密码
        layout.addWidget(QLabel("新密码"))
        self.new_password_input = ModernLineEdit("请输入新密码", QLineEdit.Password)
        self.new_password_input.textChanged.connect(self.check_password_strength)
        layout.addWidget(self.new_password_input)
        
        # 密码强度
        self.strength_indicator = PasswordStrengthIndicator()
        layout.addWidget(self.strength_indicator)
        
        # 确认新密码
        layout.addWidget(QLabel("确认新密码"))
        self.confirm_input = ModernLineEdit("请再次输入新密码", QLineEdit.Password)
        layout.addWidget(self.confirm_input)
        
        # 按钮
        btn_layout = QHBoxLayout()
        cancel_btn = ModernButton("取消", primary=False)
        cancel_btn.clicked.connect(self.reject)
        submit_btn = ModernButton("确定", primary=True)
        submit_btn.clicked.connect(self.handle_change_password)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(submit_btn)
        layout.addLayout(btn_layout)
    
    def check_password_strength(self, text):
        is_valid, strength, _ = self.manager.validate_password_strength(text)
        self.strength_indicator.update_strength(strength if is_valid else 0)
    
    def handle_change_password(self):
        old_pwd = self.old_password_input.text()
        new_pwd = self.new_password_input.text()
        confirm = self.confirm_input.text()
        
        if not old_pwd or not new_pwd or not confirm:
            QMessageBox.warning(self, "提示", "请填写所有字段")
            return
        
        success, msg = self.manager.change_password(self.email, old_pwd, new_pwd, confirm)
        if success:
            QMessageBox.information(self, "成功", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "失败", msg)


class LoginDialog(QDialog):
    """现代化的登录/注册对话框"""
    login_successful = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = LoginManager()
        self.user_info = {}
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("用户登录")
        self.setModal(True)
        self.setFixedSize(450, 550)
        self.setStyleSheet("QDialog { background-color: #ffffff; }")
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(Qt.black)
        self.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部彩色条
        header = QFrame()
        header.setFixedHeight(8)
        header.setStyleSheet("background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CAF50, stop:1 #8BC34A);")
        main_layout.addWidget(header)
        
        # Logo 区域
        logo_label = QLabel("🧠 NabuEEG")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #333; padding: 20px;")
        main_layout.addWidget(logo_label)
        
        # 标签页切换
        self.tab_widget = QWidget()
        tab_layout = QVBoxLayout(self.tab_widget)
        tab_layout.setContentsMargins(30, 10, 30, 30)
        tab_layout.setSpacing(0)
        
        # 自定义标签页标题
        tab_header = QHBoxLayout()
        self.login_tab_btn = QPushButton("登录")
        self.login_tab_btn.setCheckable(True)
        self.login_tab_btn.setChecked(True)
        self.login_tab_btn.setStyleSheet(self.get_tab_style(True))
        self.login_tab_btn.clicked.connect(lambda: self.switch_tab(0))
        
        self.register_tab_btn = QPushButton("注册")
        self.register_tab_btn.setCheckable(True)
        self.register_tab_btn.setStyleSheet(self.get_tab_style(False))
        self.register_tab_btn.clicked.connect(lambda: self.switch_tab(1))
        
        for btn in [self.login_tab_btn, self.register_tab_btn]:
            btn.setFixedHeight(50)
            btn.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            tab_header.addWidget(btn)
        
        tab_layout.addLayout(tab_header)
        
        # 分隔线
        separator = QFrame()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #e0e0e0;")
        tab_layout.addWidget(separator)
        
        # 标签页内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 20, 0, 0)
        tab_layout.addWidget(self.content_widget)
        
        main_layout.addWidget(self.tab_widget)
        
        # 初始化标签页
        self.login_tab = LoginTab(self.manager)
        self.login_tab.login_success.connect(self.on_login_success)
        self.register_tab = RegisterTab(self.manager)
        self.register_tab.register_success.connect(self.on_register_success)
        
        self.content_layout.addWidget(self.login_tab)
        
        # 连接信号
        self.login_tab.forgot_btn.clicked.connect(self.show_forgot_password)
    
    def get_tab_style(self, active):
        return f"""
            QPushButton {{
                background-color: {'#4CAF50' if active else '#f5f5f5'};
                color: {'white' if active else '#666666'};
                border: none;
                border-radius: 0;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {'#45a049' if active else '#e8e8e8'};
            }}
        """
    
    def switch_tab(self, index):
        """切换标签页"""
        if index == 0:
            self.login_tab_btn.setChecked(True)
            self.register_tab_btn.setChecked(False)
            self.login_tab_btn.setStyleSheet(self.get_tab_style(True))
            self.register_tab_btn.setStyleSheet(self.get_tab_style(False))
            self.content_layout.removeWidget(self.register_tab)
            self.content_layout.addWidget(self.login_tab)
        else:
            self.register_tab_btn.setChecked(True)
            self.login_tab_btn.setChecked(False)
            self.register_tab_btn.setStyleSheet(self.get_tab_style(True))
            self.login_tab_btn.setStyleSheet(self.get_tab_style(False))
            self.content_layout.removeWidget(self.login_tab)
            self.content_layout.addWidget(self.register_tab)
    
    def on_login_success(self, user_info):
        self.user_info = user_info
        QMessageBox.information(self, "登录成功", f"欢迎回来，{user_info['username']}!")
        self.accept()
    
    def on_register_success(self):
        self.switch_tab(0)  # 切换到登录页
    
    def show_forgot_password(self):
        QMessageBox.information(self, "提示", "请联系管理员重置密码")
    
    def get_current_user_email(self):
        return self.user_info.get("email")
    
    def get_current_username(self):
        return self.user_info.get("username")


class UserProfileDialog(QDialog):
    """用户资料对话框"""
    def __init__(self, email, manager, parent=None):
        super().__init__(parent)
        self.email = email
        self.manager = manager
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("用户资料")
        self.setModal(True)
        self.setFixedSize(400, 400)
        self.setStyleSheet("QDialog { background-color: #ffffff; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 用户头像
        avatar_label = QLabel("👤")
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setStyleSheet("font-size: 60px; background-color: #f5f5f5; border-radius: 50px; padding: 20px;")
        layout.addWidget(avatar_label)
        
        # 用户信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        
        items = [
            ("📧 邮箱", self.email),
            ("👤 用户名", self.email.split('@')[0]),
            ("📅 注册时间", "未知"),
            ("🕐 最后登录", "未知")
        ]
        
        for label, value in items:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #666; font-weight: bold;")
            val = QLabel(value)
            val.setStyleSheet("color: #333;")
            val.setAlignment(Qt.AlignRight)
            
            item_layout.addWidget(lbl)
            item_layout.addStretch()
            item_layout.addWidget(val)
            info_layout.addWidget(item_widget)
        
        layout.addLayout(info_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        change_pwd_btn = ModernButton("修改密码", primary=True)
        change_pwd_btn.clicked.connect(self.show_change_password)
        close_btn = ModernButton("关闭", primary=False)
        close_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(change_pwd_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
    
    def show_change_password(self):
        dlg = ChangePasswordDialog(self.email, self.manager, self)
        if dlg.exec_() == QDialog.Accepted:
            self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = LoginDialog()
    if dialog.exec_() == QDialog.Accepted:
        print(f"登录成功：{dialog.get_current_user_email()}")
    sys.exit(app.exec_())
