import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
os.chdir(ROOT_DIR)
sys.path.insert(0, str(ROOT_DIR / "app"))

from PyQt6.QtWidgets import QStackedWidget, QApplication, QMainWindow
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QTranslator, QLocale, QLibraryInfo

from login import *
from main_window import *
'''
собираем 2 окна в приложение(MainWimdow и LoginWindow) 
по сути соединяем 2 класса и заставляем их работать вместе
+ есть возможность переключаться между ними(кнопка назад в основном окне)
'''

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(str(ROOT_DIR / "resources" / "Icon.png")))
        self.setWindowTitle("ShoeShop — Обувной магазин")
        self.stacked = QStackedWidget()
        self.login_window = LoginWindow(self)
        self.stacked.addWidget(self.login_window)
        self.setCentralWidget(self.stacked)

    def show_main_window(self, role, user_display_name):
        # Создаём главное окно и добавляем в стек
        self.main_window = MainWindow(role, user_display_name, self)
        self.stacked.addWidget(self.main_window)
        self.stacked.setCurrentWidget(self.main_window)
        self.setWindowTitle("Обувной магазин")
        self.setGeometry(100, 100, 800, 600)

    def return_to_login(self):
        # Удаляем главное окно из стека
        if hasattr(self, 'main_window'):
            self.stacked.removeWidget(self.main_window)
            self.main_window.deleteLater()
            del self.main_window

        self.stacked.setCurrentWidget(self.login_window)
        self.setWindowTitle("Обувной магазин — Вход")
        self.setGeometry(100, 100, 400, 200)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # === УСТАНОВКА РУССКОЙ ЛОКАЛИЗАЦИИ ===
    translator = QTranslator()
    # Пытаемся загрузить официальный перевод Qt на русский
    qt_trans_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load(QLocale("ru_RU"), "qt", "_", qt_trans_dir):
        app.installTranslator(translator)
    else:
        print("Внимание: русская локализация Qt не загружена (кнопки QMessageBox останутся на английском)")

    # Устанавливаем шрифт приложения
    font = QFont("Times New Roman", 12)
    app.setFont(font)

    # Запуск приложения
    window = App()
    window.show()
    sys.exit(app.exec())