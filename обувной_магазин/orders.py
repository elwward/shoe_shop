from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QScrollArea, QDialog, QComboBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate

from database import *

ORDERS = get_all_orders()

def create_order_cards_widget(parent_window, is_admin=False):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setStyleSheet("background-color: white;")

    container = QWidget()
    container_layout = QVBoxLayout(container)
    container_layout.setContentsMargins(0, 0, 0, 0)
    container_layout.setSpacing(10)

    def open_edit_form(order):
        parent_window.open_order_form(order_data=order)

    for order in get_all_orders():
        card = OrderCard(order, is_admin=is_admin, on_edit=open_edit_form)
        container_layout.addWidget(card)

    container_layout.addStretch()
    scroll_area.setWidget(container)
    layout.addWidget(scroll_area)

    if is_admin:
        add_btn = QPushButton("Добавить заказ")
        add_btn.setStyleSheet("background-color: #00FA9A; padding: 8px;")
        add_btn.clicked.connect(lambda: parent_window.open_order_form())
        layout.addWidget(add_btn)

    return widget


class OrderCard(QWidget):
    def __init__(self, order, is_admin=False, on_edit=None):
        super().__init__()
        self.order = order
        self.is_admin = is_admin
        self.on_edit = on_edit
        self.init_ui()

    def init_ui(self):
        # Внешний макет без отступов
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Внутренний wrapper с рамкой
        self.wrapper = QWidget()
        self.wrapper.setObjectName("wrapper")
        wrapper_layout = QHBoxLayout(self.wrapper)
        wrapper_layout.setContentsMargins(10, 10, 10, 10)
        wrapper_layout.setSpacing(30)
        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === Левая часть: информация о заказе ===
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Артикул
        self.article_label = QLabel(f"<b>Артикул заказа:</b> {self.order['article']}")
        self.article_label.setStyleSheet("font-size: 13pt;")
        info_layout.addWidget(self.article_label)

        # Статус
        self.status_label = QLabel(f"<b>Статус заказа:</b> {self.order['status']}")
        info_layout.addWidget(self.status_label)

        # Адрес
        self.address_label = QLabel(f"<b>Адрес пункта выдачи:</b> {self.order['pickup_address']}")
        self.address_label.setWordWrap(True)
        self.address_label.setMaximumHeight(40)
        info_layout.addWidget(self.address_label)

        # Дата заказа
        self.order_date_label = QLabel(f"<b>Дата заказа:</b> {self.order['order_date']}")
        info_layout.addWidget(self.order_date_label)

        wrapper_layout.addLayout(info_layout)

        # === Вертикальная линия (как в ProductCard) ===
        from PyQt6.QtWidgets import QFrame, QSizePolicy
        line = QFrame()
        line.setFrameShape(QFrame.Shape.NoFrame)
        line.setFixedWidth(2)
        line.setStyleSheet("background-color: black;")
        line.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        wrapper_layout.addWidget(line)

        # === Правая часть: дата доставки (аналог скидки) ===
        self.delivery_label = QLabel()
        self.delivery_label.setText(f"<b>Дата доставки:</b><br>{self.order['delivery_date']}")
        self.delivery_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.delivery_label.setFixedSize(140, 60)
        self.delivery_label.setStyleSheet("""
            background-color: #FFFFFF;
            padding: 5px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 10pt;
        """)

        # Цвет фона можно менять по условиям (например, просрочен?)
        # Например: если дата доставки < сегодня — красный фон
        from datetime import datetime
        try:
            delivery_date = datetime.strptime(self.order['delivery_date'], "%Y-%m-%d")
            today = datetime.today()
            if delivery_date < today and self.order['status'] != "Доставлен":
                self.delivery_label.setStyleSheet("""
                    background-color: #FFFFFF; /* светло-красный */
                    padding: 5px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 10pt;
                """)
        except:
            pass  # игнорируем ошибки парсинга

        wrapper_layout.addWidget(self.delivery_label)


        # === Стиль обёртки (как у ProductCard) ===
        '''
        self.wrapper.setStyleSheet("""
            #wrapper {
                border: 1px solid #000000;
                border-radius: 8px;
                background-color: white;
            }
        """)
        '''

        outer_layout.addWidget(self.wrapper)

        # Курсор
        if self.is_admin:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        base_color, _ = self._get_base_colors()
        self._apply_background_color(base_color)

    def mousePressEvent(self, event):
        if self.is_admin and event.button() == Qt.MouseButton.LeftButton:
            if self.on_edit:
                self.on_edit(self.order)
        super().mousePressEvent(event)

    def delete_order(self):
        reply = QMessageBox.question(
            self, "Удалить заказ?",
            f"Вы уверены, что хотите удалить заказ {self.order['article']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_order(self.order["id"])
            global ORDERS
            ORDERS = [o for o in ORDERS if o["id"] != self.order["id"]]

            # Безопасно обновляем список — вызываем метод у главного окна (если есть)
            top = self.window()
            if hasattr(top, "refresh_orders_tab"):
                try:
                    top.refresh_orders_tab()
                except Exception:
                    pass
            # не вызываем self.on_edit(None) — это могло бы открыть форму с пустыми данными

    def _get_base_colors(self):
        base_color = "white"
        hover_color = "#f0f0f0"

        return base_color, hover_color

    def _apply_background_color(self, color):
        """Применяет цвет фона ко всем элементам карточки"""
        # Оболочка
        self.wrapper.setStyleSheet(f"""
            #wrapper {{
                border: 1px solid #000000;
                border-radius: 8px;
                background-color: {color};
            }}
        """)

        # Все текстовые метки
        for label in [
            self.article_label,
            self.status_label,
            self.address_label,
            self.order_date_label
        ]:
            label.setStyleSheet(
                f"background-color: {color}; font-size: 13pt;" if label == self.article_label else f"background-color: {color};")

        # Метка даты доставки
        self.delivery_label.setStyleSheet(f"""
            background-color: {color};
            padding: 5px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 10pt;
        """)

    def enterEvent(self, event):
        _, hover_color = self._get_base_colors()
        self._apply_background_color(hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        base_color, _ = self._get_base_colors()
        self._apply_background_color(base_color)
        super().leaveEvent(event)



class OrderFormWindow(QDialog):
    def __init__(self, parent=None, order_data=None, callback=None, role=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.order_data = order_data
        self.callback = callback
        self.role = role  # ← новое!
        self.setWindowTitle("Редактировать заказ" if order_data else "Добавить заказ")
        self.setModal(True)
        self.resize(400, 320)  # чуть выше, чтобы поместилась кнопка
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # === Все поля формы ===
        label = QLabel("Артикул заказа:")
        label.setStyleSheet("background-color: #7FFF00;")
        layout.addWidget(label)

        self.article_input = QLineEdit()
        if self.order_data:
            self.article_input.setText(self.order_data.get("article", ""))
        layout.addWidget(self.article_input)

        label = QLabel("Статус заказа:")
        label.setStyleSheet("background-color: #7FFF00;")
        layout.addWidget(label)

        self.status_combo = QComboBox()
        statuses = ["Новый", "В обработке", "Ожидает оплаты", "Оплачен", "Доставлен", "Отменён"]
        self.status_combo.addItems(statuses)
        if self.order_data:
            current = self.order_data.get("status", "")
            if current in statuses:
                self.status_combo.setCurrentText(current)
        layout.addWidget(self.status_combo)

        label = QLabel("Адрес пункта выдачи:")
        label.setStyleSheet("background-color: #7FFF00;")
        layout.addWidget(label)

        self.address_input = QLineEdit()
        if self.order_data:
            self.address_input.setText(self.order_data.get("pickup_address", ""))
        layout.addWidget(self.address_input)

        label = QLabel("Дата заказа:")
        label.setStyleSheet("background-color: #7FFF00;")
        layout.addWidget(label)

        self.order_date_edit = QDateEdit()
        self.order_date_edit.setCalendarPopup(True)
        self.order_date_edit.setDate(QDate.currentDate())
        if self.order_data:
            date_str = self.order_data.get("order_date", "")
            if date_str:
                self.order_date_edit.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
        layout.addWidget(self.order_date_edit)

        label = QLabel("Дата выдачи:")
        label.setStyleSheet("background-color: #7FFF00;")
        layout.addWidget(label)

        self.delivery_date_edit = QDateEdit()
        self.delivery_date_edit.setCalendarPopup(True)
        self.delivery_date_edit.setDate(QDate.currentDate().addDays(3))
        if self.order_data:
            date_str = self.order_data.get("delivery_date", "")
            if date_str:
                self.delivery_date_edit.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
        layout.addWidget(self.delivery_date_edit)

        # === Кнопки ===
        buttons_layout = QHBoxLayout()

        cancel_btn = QPushButton("Назад")
        cancel_btn.setStyleSheet("background-color: #00FA9A; color: black;  outline: none;")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Сохранить")
        save_btn.setStyleSheet("background-color: #00FA9A; color: black;  outline: none;")
        save_btn.clicked.connect(self.save)
        buttons_layout.addWidget(save_btn)

        # Кнопка "Удалить" (только при редактировании и для админа)
        if self.order_data and self.role == "Администратор":
            delete_btn = QPushButton("Удалить заказ")
            delete_btn.setStyleSheet("background-color: #00FA9A; color: black;  outline: none;")
            delete_btn.clicked.connect(self.delete_order)
            buttons_layout.addWidget(delete_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def save(self):
        article = self.article_input.text().strip()
        if not article:
            QMessageBox.critical(self, "Ошибка", "Артикул не может быть пустым!")
            return

        pickup_address = self.address_input.text().strip()
        if not pickup_address:
            QMessageBox.critical(self, "Ошибка", "Пункт выдачи не может быть пустым!")
            return

        order = {
            "article": article,
            "status": self.status_combo.currentText(),
            "pickup_address": self.address_input.text().strip(),
            "order_date": self.order_date_edit.date().toString("yyyy-MM-dd"),
            "delivery_date": self.delivery_date_edit.date().toString("yyyy-MM-dd")
        }

        if self.order_data:
            order["id"] = self.order_data["id"]

        saved_order = save_order(order)
        if self.callback:
            self.callback(saved_order, is_new=(self.order_data is None))
        self.accept()

    def delete_order(self):
        reply = QMessageBox.warning(
            self, "Предупреждение",
            f"Вы уверены, что хотите удалить заказ {self.order_data['article']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_order(self.order_data["id"])
            if self.callback:
                self.callback(None, is_new=False)  # сигнал на обновление
            self.accept()  # закрываем форму