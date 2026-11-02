from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)
from products import *
from orders import *


'''
здесь мы берем классы и функции из products.py и orders.py и объединяем их воедино
'''


class MainWindow(QMainWindow):
    def __init__(self, role, user_display_name, parent_app):
        super().__init__()
        self.role = role
        self.user_display_name = user_display_name
        self.parent_app = parent_app
        self.setWindowTitle(f"Обувной магазин ({role})")
        self.setStyleSheet("background-color: white;")
        self.setGeometry(100, 100, 800, 600)

        # Основной виджет и макет
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Верхняя панель: логотип + название + кнопка "Выйти"
        # Верхняя панель
        # === Верхняя панель (заголовок) ===
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #7FFF00;")  # ← цвет фона

        header_layout = QHBoxLayout(header_widget)  # ← макет привязан к виджету
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(15)

        # === Левая группа: иконка + название ===
        left_group = QHBoxLayout()
        left_group.setSpacing(10)

        # Логотип
        logo_label = QLabel()
        pixmap = QPixmap("resources/Icon.JPG")
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        left_group.addWidget(logo_label)

        # Название (сохраняем как атрибут класса)
        self.header_title_label = QLabel("Обувной магазин")
        self.header_title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #222;")
        left_group.addWidget(self.header_title_label)

        header_layout.addLayout(left_group)
        header_layout.addStretch()

        # === Правая группа: ФИО + кнопка ===
        logout_button = QPushButton("Выйти")
        logout_button.setStyleSheet("padding: 5px 15px; background-color: #00FA9A;")
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)

        user_label = QLabel(self.user_display_name)
        user_label.setStyleSheet("font-size: 14px; color: #000000; padding: 2px 8px;")
        header_layout.addWidget(user_label)

        # Добавляем шапку в основной макет
        main_layout.addWidget(header_widget)  # ← добавляем ВИДЖЕТ, а не макет

        # === Разделительная линия ===
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #FFFFFF;")
        main_layout.addWidget(separator)

        # === Вкладки ===
        tabs = QTabWidget()
        tabs.currentChanged.connect(self.on_tab_changed)

        # Товары — для всех, но с разным интерфейсом
        products_widget = QWidget()
        products_layout = QVBoxLayout(products_widget)
        products_layout.setContentsMargins(10, 10, 10, 10)

        if self.role in ("Менеджер", "Администратор"):
            # Для менеджера и админа — с интерактивной панелью
            self.products_list = ProductListWidget(role=self.role)
            products_layout.addWidget(self.products_list)
        else:
            # Для клиента — просто статичный список
            from PyQt6.QtWidgets import QScrollArea  # для совместимости
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("background-color: white;")

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(10)

            for product in PRODUCTS:
                card = ProductCard(product)
                container_layout.addWidget(card)


            scroll_area.setWidget(container)
            products_layout.addWidget(scroll_area)

        tabs.addTab(products_widget, "Товары")


        # Заказы — только для manager и admin
        if self.role in ("Менеджер", "Администратор"):
            orders_widget = QWidget()
            orders_layout = QVBoxLayout(orders_widget)
            orders_layout.setContentsMargins(10, 10, 10, 10)
            #orders_layout.addWidget(QLabel("Список заказов"))
            orders_layout.addWidget(create_order_cards_widget(self, is_admin=(self.role == "Администратор")))
            tabs.addTab(orders_widget, "Заказы")

        main_layout.addWidget(tabs)



        # Устанавливаем центральный виджет
        self.setCentralWidget(main_widget)

    def logout(self):
        self.parent_app.return_to_login()

    def on_tab_changed(self, index):
        tabs = self.findChild(QTabWidget)
        if not tabs:
            return
        current_tab_text = tabs.tabText(index)
        if current_tab_text == "Товары":
            self.header_title_label.setText("Каталог товаров")
        elif current_tab_text == "Заказы":
            self.header_title_label.setText("Каталог заказов")

    def open_order_form(self, order_data=None):
        def on_save(order, is_new):
            # order может быть None при удалении.
            # На этом уровне мы не пытаемся снова сохранять — просто обновляем UI.
            self.refresh_orders_tab()

        form = OrderFormWindow(
            parent=self,
            order_data=order_data,
            callback=on_save,
            role=self.role
        )
        form.exec()

    def refresh_orders_tab(self):
        tabs = self.findChild(QTabWidget)
        if not tabs:
            return

        # Находим вкладку "Заказы"
        order_tab_index = -1
        for i in range(tabs.count()):
            if tabs.tabText(i) == "Заказы":
                order_tab_index = i
                break

        if order_tab_index == -1:
            return

        # Получаем текущий виджет вкладки
        old_widget = tabs.widget(order_tab_index)

        # Создаём новый виджет с обновлёнными заказами
        new_widget = create_order_cards_widget(self, is_admin=(self.role == "Администратор"))

        # Заменяем виджет вкладки
        tabs.removeTab(order_tab_index)
        tabs.insertTab(order_tab_index, new_widget, "Заказы")
        tabs.setCurrentIndex(order_tab_index)

        # Удаляем старый виджет (опционально, но хорошо для памяти)
        if old_widget:
            old_widget.deleteLater()