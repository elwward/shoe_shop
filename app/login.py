from PyQt6.QtWidgets import QWidget, QVBoxLayout,QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from database import *
'''
Обработка неверного логина и пароля есть(Выводит сообщение об ошибке)
Корректный вход есть
Иконка и название магазина есть
Оформление соответсвует(кнопки зеленые)

Нужно доработать сплошной белый цвет
'''

class LoginWindow(QWidget):
    def __init__(self, parent):
        super().__init__()


        self.parent_app = parent
        self.init_ui()
    def init_ui(self):

        layout = QVBoxLayout()

        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)

        logo_label = QLabel()
        pixmap = QPixmap("resources/Icon.JPG")
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_detail = QLabel("🖼️ Логотип не найден")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_label)


        title_label = QLabel("ООО «Обувь»\nАвторизация")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        header_layout.addWidget(title_label)

        layout.addWidget(header_widget)

        # === Поля ввода ===
        login_label = QLabel("Логин:")
        login_label.setStyleSheet("background-color: #7FFF00;")
        layout.addWidget(login_label)
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")
        layout.addWidget(self.login_input)

        password_label = QLabel("Пароль:")
        password_label.setStyleSheet("background-color: #7FFF00;")
        layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Кнопки
        login_btn = QPushButton("Войти")
        login_btn.setStyleSheet("background-color: #00FA9A;")
        guest_btn = QPushButton("Войти как гость")
        guest_btn.setStyleSheet("background-color: #00FA9A;")

        login_btn.clicked.connect(self.handle_login)
        guest_btn.clicked.connect(self.handle_guest)

        layout.addWidget(login_btn)
        layout.addWidget(guest_btn)

        self.setLayout(layout)

    def handle_login(self):
        login = self.login_input.text()
        password = self.password_input.text()
        role = authenticate_user(login, password)
        if role:
            full_name = get_user_full_name(login)
            self.parent_app.show_main_window(role, full_name)
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль")

    def handle_guest(self):
        self.parent_app.show_main_window("guest", "Гость")