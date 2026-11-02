from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QScrollArea, QRadioButton, QButtonGroup
)

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

from PIL import Image
import os
from database import *


PRODUCTS = get_all_products()



class ProductEditDialog(QDialog):
    # Сигнал, который будет испускаться при успешном сохранении или удалении
    product_saved = pyqtSignal(dict)   # при сохранении
    product_deleted = pyqtSignal(int)  # при удалении (передаём id)

    def __init__(self, product_data=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.product_data = product_data
        self.init_ui()
        self.populate_fields()

    def init_ui(self):
        self.setWindowTitle("Редактировать товар" if self.product_data else "Добавить товар")
        self.setModal(True)
        self.resize(500, 480)

        layout = QVBoxLayout(self)


        # Поля ввода
        self.category_input = QComboBox()
        self.category_input.addItems(["Обувь", "Мужская обувь", "Женская обувь"])

        self.name_input = QLineEdit()
        self.description_input = QLineEdit()

        self.manufacturer_input = QComboBox()
        manufacturers = sorted({p["manufacturer"] for p in PRODUCTS if p.get("manufacturer")})
        self.manufacturer_input.addItems(manufacturers)

        self.supplier_input = QLineEdit()
        self.price_input = QLineEdit()
        self.unit_input = QLineEdit()
        self.stock_input = QLineEdit()
        self.discount_input = QLineEdit()
        self.photo_path_input = QLineEdit()

        # Вспомогательная функция для стилизованной метки
        def create_styled_label(text):
            label = QLabel(text)
            label.setStyleSheet("background-color: #7FFF00;")
            return label

        form_layout = QFormLayout()
        # Добавляем строки с кастомной меткой
        form_layout.addRow(create_styled_label("Категория:"), self.category_input)
        form_layout.addRow(create_styled_label("Название:"), self.name_input)
        form_layout.addRow(create_styled_label("Описание:"), self.description_input)
        form_layout.addRow(create_styled_label("Производитель:"), self.manufacturer_input)
        form_layout.addRow(create_styled_label("Поставщик:"), self.supplier_input)
        form_layout.addRow(create_styled_label("Цена:"), self.price_input)
        form_layout.addRow(create_styled_label("Ед. изм.:"), self.unit_input)
        form_layout.addRow(create_styled_label("Кол-во на складе:"), self.stock_input)
        form_layout.addRow(create_styled_label("Скидка (%):"), self.discount_input)

        # Предпросмотр фото
        self.photo_preview = QLabel()
        self.photo_preview.setFixedSize(150, 150)
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        # Убираем setText — он мешает при наличии изображения

        # Сразу устанавливаем заглушку
        self.update_photo_preview("resources/picture.png")

        form_layout.addRow(
            create_styled_label(
                "Фото товара:\nОграничение: 300×200 пикселей.\nУчтите это при загрузке фото.\nИначе оно будет масштабировано."
            ),
            self.photo_preview
        )

        # Кнопка выбора файла
        browse_btn = QPushButton("Выбрать фото")
        browse_btn.clicked.connect(self.browse_photo)
        form_layout.addRow("", browse_btn)
        form_layout.addRow(create_styled_label("Путь к фото:"), self.photo_path_input)

        layout.addLayout(form_layout)


        # Кнопки: Назад | Сохранить | Удалить
        buttons_layout = QHBoxLayout()

        # Кнопка "Назад" (Отмена)
        self.back_btn = QPushButton("Назад")
        self.back_btn.setStyleSheet("background-color: #00FA9A;")
        self.back_btn.clicked.connect(self.reject)  # стандартное поведение: закрыть с результатом Rejected
        buttons_layout.addWidget(self.back_btn)

        # Кнопка "Сохранить"
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setStyleSheet("background-color: #00FA9A;")
        self.save_btn.clicked.connect(self.save_product)
        buttons_layout.addWidget(self.save_btn)

        # Кнопка "Удалить" — только при редактировании
        if self.product_data:
            self.delete_btn = QPushButton("Удалить")
            self.delete_btn.setStyleSheet("background-color: #00FA9A;")
            self.delete_btn.clicked.connect(self.delete_product_confirm)
            buttons_layout.addWidget(self.delete_btn)

        layout.addLayout(buttons_layout)

    def resize_image(self, input_path, output_path, max_width=300, max_height=200):
        try:
            with Image.open(input_path) as img:
                width, height = img.size
                ratio = min(max_width / width, max_height / height)
                new_size = (int(width * ratio), int(height * ratio))
                resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                resized_img.save(output_path, quality=95, optimize=True)
                return True
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось обработать изображение:\n{e}")
            return False

    def browse_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not file_path:
            return

        # Готовим имя выходного файла
        base_name = os.path.basename(file_path)
        name, ext = os.path.splitext(base_name)
        save_dir = "resources/images"
        os.makedirs(save_dir, exist_ok=True)
        resized_path = os.path.join(save_dir, f"resized_{name}{ext}")

        if self.resize_image(file_path, resized_path, 300, 200):
            self.photo_path_input.setText(resized_path)
            self.update_photo_preview(resized_path)
            QMessageBox.warning(self, "Предупреждение",
                                "Изображение было масштабировано. Ваше изображение не соотвествовало необходимому размеру(300x200).")
        else:
            self.photo_path_input.setText(file_path)
            self.update_photo_preview(file_path)
            QMessageBox.warning(self, "Предупреждение",
                                "Изображение не было масштабировано. Оно будет использовано в исходном размере.")

    def update_photo_preview(self, path):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            pixmap = QPixmap("resources/picture.png")
            if pixmap.isNull():
                self.photo_preview.setText("Нет изображения")
                return
        scaled_pixmap = pixmap.scaled(
            self.photo_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.photo_preview.setPixmap(scaled_pixmap)

    def populate_fields(self):
        if self.product_data:
            self.category_input.setCurrentText(self.product_data.get("category", ""))
            self.name_input.setText(self.product_data.get("name", ""))
            self.description_input.setText(self.product_data.get("description", ""))
            self.manufacturer_input.setCurrentText(self.product_data.get("manufacturer", ""))
            self.supplier_input.setText(self.product_data.get("supplier", ""))
            self.price_input.setText(str(self.product_data.get("price", "")))
            self.unit_input.setText(self.product_data.get("unit", ""))
            self.stock_input.setText(str(self.product_data.get("stock", "")))
            disc = self.product_data.get("discount")
            self.discount_input.setText(str(disc) if disc is not None else "")

            photo_path = self.product_data.get("photo_path", "")
            # ← Скрываем "picture.png" из поля ввода
            if photo_path in ("picture.png", "resources/picture.png"):
                self.photo_path_input.setText("")  # оставляем поле пустым
            else:
                self.photo_path_input.setText(photo_path)

            # Всегда обновляем превью (даже если путь пустой)
            self.update_photo_preview(photo_path)

    def save_product(self):
        try:
            name = self.name_input.text().strip()
            supplier = self.supplier_input.text().strip()

            if not name:
                QMessageBox.critical(self, "Ошибка", "Поле 'Название' обязательно для заполнения.")
                return
            if not supplier:
                QMessageBox.critical(self, "Ошибка", "Поле 'Поставщик' обязательно для заполнения.")
                return

            price = float(self.price_input.text().strip())
            if price < 0:
                QMessageBox.critical(self, "Ошибка", "Цена не может быть отрицательной.")
                return

            stock = int(self.stock_input.text().strip())
            if stock < 0:
                QMessageBox.critical(self, "Ошибка", "Количество на складе не может быть отрицательным.")
                return

            discount = self.discount_input.text().strip()
            if discount:
                discount_val = float(discount)
                if discount_val < 0 or discount_val > 100:
                    QMessageBox.critical(self, "Ошибка", "Скидка должна быть в диапазоне от 0 до 100%.")
                    return
            else:
                discount = None

            photo_path = self.photo_path_input.text().strip()
            if not photo_path:
                photo_path = "resources/picture.png"

            if self.product_data:
                # При редактировании — оставляем старый артикул (он уже есть в product_data)
                article = self.product_data.get("article", generate_unique_product_article())  # <-- Используем .get()
            else:
                # Новый товар — генерируем артикул
                article = generate_unique_product_article()

            data = {
                #"id": self.product_data["id"] if self.product_data else max([p["id"] for p in PRODUCTS], default=0) + 1,
                "article": article,
                "category": self.category_input.currentText(),
                "name": name,
                "description": self.description_input.text().strip(),
                "manufacturer": self.manufacturer_input.currentText().strip(),
                "supplier": supplier,
                "price": price,
                "unit": self.unit_input.text().strip(),
                "stock": stock,
                "discount": discount,
                "photo_path": photo_path
            }

            # ✅ СОХРАНЯЕМ В БАЗУ ЗДЕСЬ!
            saved_data = save_product(data)
            self.product_saved.emit(saved_data)
            self.accept()

        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Проверьте правильность ввода числовых полей (цена, остаток, скидка).")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла непредвиденная ошибка:\n{e}")

    def delete_product_confirm(self):
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить товар «{self.product_data['name']}»?\n"
            "Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            product_id = self.product_data["id"]
            try:
                delete_product(product_id)  # ← ваша функция из database.py
                self.product_deleted.emit(product_id)
                self.accept()
            except Exception as e:
                #QMessageBox.critical(self, "Ошибка", f"Не удалось удалить товар:\n{e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить товар. Товар есть в заказе.")


from PyQt6.QtWidgets import QPushButton  # Добавьте импорт


class ProductCard(QWidget):
    card_clicked = pyqtSignal(dict)

    def __init__(self, product, role="Администратор"):
        super().__init__()
        self.product = product
        self.role = role
        self.is_editable = (self.role == "Администратор")
        self.init_ui()

    def init_ui(self):
        # === Внешний контейнер без рамки ===
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # === Внутренний виджет с рамкой ===
        self.wrapper = QWidget()
        self.wrapper.setObjectName("wrapper")

        wrapper_layout = QHBoxLayout(self.wrapper)
        wrapper_layout.setContentsMargins(10, 10, 10, 10)
        wrapper_layout.setSpacing(30)
        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === Фото ===
        self.photo_label = QLabel()
        pixmap = QPixmap(self.product.get("photo_path", "resources/picture.png"))
        if pixmap.isNull():
            self.photo_label.setText("🖼️ Фото")
            self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            scaled_pixmap = pixmap.scaled(
                120, 120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.photo_label.setPixmap(scaled_pixmap)

        self.photo_label.setFixedSize(120, 120)

        # === Определяем цвет фона для текстовых полей ===
        text_bg_color = "#FFFFFF"  # белый по умолчанию

        # Обработка скидки
        discount_str = self.product.get("discount")
        discount_value = 0
        if discount_str and discount_str != "Нет скидки":
            try:
                discount_value = int(discount_str.replace('%', '').strip())
            except:
                pass

        # Меняем цвет фона текста в зависимости от условий
        if discount_value > 15:
            text_bg_color = "#2E8B57"


        self.photo_label.setStyleSheet(f"background-color: {text_bg_color};")
        wrapper_layout.addWidget(self.photo_label)

        # === Информация ===
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.title_label = QLabel(f"<b>{self.product['category']} | {self.product['name']}</b>")
        self.title_label.setStyleSheet(f"background-color: {text_bg_color};")
        info_layout.addWidget(self.title_label)

        self.desc_label = QLabel(f"<b>Описание товара:</b> {self.product['description']}")
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumHeight(40)
        self.desc_label.setStyleSheet(f"background-color: {text_bg_color};")
        info_layout.addWidget(self.desc_label)

        # Производитель
        self.manufacturer_label = QLabel(f"<b>Производитель:</b> {self.product['manufacturer']}")
        self.manufacturer_label.setStyleSheet(f"background-color: {text_bg_color};")
        info_layout.addWidget(self.manufacturer_label)

        # Поставщик
        self.supplier_label = QLabel(f"<b>Поставщик:</b> {self.product['supplier']}")
        self.supplier_label.setStyleSheet(f"background-color: {text_bg_color};")
        info_layout.addWidget(self.supplier_label)

        # Цена (сразу после поставщика)
        price = self.product["price"]
        discount = self.product.get("discount")
        self.price_label = QLabel()

        if discount and discount.isdigit():
            discount_val = int(discount)
            final_price = round(price * (100 - discount_val) / 100, 2)
            self.price_label.setText(
                f"<b>Цена:</b> "
                f"<span style='color:red; text-decoration: line-through;'>{price} руб.</span> "
                f"<span style='color:black;'> → {final_price} руб.</span>"
            )
        else:
            self.price_label.setText(f"<b>Цена:</b> {price} руб.")

        self.price_label.setStyleSheet(f"background-color: {text_bg_color};")
        info_layout.addWidget(self.price_label)

        # Единица измерения
        self.unit_label = QLabel(f"<b>Единица измерения:</b> {self.product['unit']}")
        self.unit_label.setStyleSheet(f"background-color: {text_bg_color};")
        info_layout.addWidget(self.unit_label)

        # Количество на складе (с особым стилем при нуле или меньше)
        stock = self.product["stock"]
        availability = "много" if stock > 5 else "мало"
        self.stock_label = QLabel(f"<b>Количество на складе:</b> {stock} ({availability})")
        stock_color = "#ADD8E6" if self.product["stock"] <= 0 else text_bg_color
        self.stock_label.setStyleSheet(f"background-color: {stock_color};")
        info_layout.addWidget(self.stock_label)

        wrapper_layout.addLayout(info_layout)

        # === Вертикальная линия ===
        from PyQt6.QtWidgets import QFrame, QSizePolicy

        line = QFrame()
        line.setFrameShape(QFrame.Shape.NoFrame)

        # Явно задаём толщину
        line.setFixedWidth(2)

        # Делаем вертикальную линию
        line.setStyleSheet("background-color: black;")

        # Растягиваем по высоте
        line.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        wrapper_layout.addWidget(line)

        # === Скидка ===
        discount_label = QLabel()
        discount_raw = self.product.get("discount")

        if discount_raw is None or discount_raw == "Нет скидки":
            discount_display = "Нет скидки"
        else:
            # Пытаемся преобразовать в число
            try:
                # Убираем % если есть
                clean_discount = str(discount_raw).replace('%', '').strip()
                discount_value = int(clean_discount)
                discount_display = f"{discount_value}%"
            except (ValueError, TypeError):
                discount_display = str(discount_raw)  # Оставляем как есть

        discount_label.setText(f"<b>Действующая скидка:</b><br>{discount_display}")
        discount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        discount_label.setFixedSize(140, 60)
        discount_label.setStyleSheet("""
            background-color: #FFFFFF;
            padding: 5px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 10pt;
        """)

        discount_str = self.product.get("discount")

        # Преобразуем в число
        discount_value = 0
        if discount_str and discount_str != "Нет скидки":
            try:
                # Удаляем символ % и пробелы, конвертируем в int
                discount_value = int(discount_str.replace('%', '').strip())
            except (ValueError, AttributeError):
                discount_value = 0

        # Теперь можно безопасно сравнивать
        if discount_value > 15:
            discount_label.setStyleSheet("""
                                    background-color: #2E8B57;
                                    padding: 5px;
                                    border-radius: 5px;
                                    font-weight: bold;
                                    font-size: 10pt;
                                """)

        self.discount_label = discount_label
        wrapper_layout.addWidget(discount_label)



        # === Самая важная часть — нормальная рамка ===
        self.wrapper.setStyleSheet("""
            #wrapper {
                border: 1px solid #000000;
                border-radius: 8px;
                background-color: white;
            }
        """)


        discount_str = self.product.get("discount")

        # Преобразуем в число
        discount_value = 0
        if discount_str and discount_str != "Нет скидки":
            try:
                # Удаляем символ % и пробелы, конвертируем в int
                discount_value = int(discount_str.replace('%', '').strip())
            except (ValueError, AttributeError):
                discount_value = 0

        # Теперь можно безопасно сравнивать
        if discount_value > 15:
            self.wrapper.setStyleSheet("""
                #wrapper {
                    border: 1px solid #000000;
                    border-radius: 8px;
                    background-color: #2E8B57;
                }
            """)



        outer_layout.addWidget(self.wrapper)

        if self.is_editable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)


    def mousePressEvent(self, event):
        if self.is_editable and event.button() == Qt.MouseButton.LeftButton:
            self.card_clicked.emit(self.product)
            super().mousePressEvent(event)

    def _get_base_colors(self):
        """Возвращает (фон_обычный, фон_при_наведении)"""
        base_color = "white"
        hover_color = "#f0f0f0"
        discount_str = self.product.get("discount")
        discount_value = 0
        if discount_str and discount_str != "Нет скидки":
            try:
                discount_value = int(discount_str.replace('%', '').strip())
            except:
                pass

        if discount_value > 15:
            base_color = "#2E8B57"
            hover_color = "#226644"  # немного темнее

        return base_color, hover_color

    def _apply_background_color(self, color):
        """Применяет цвет фона ко всем зависимым виджетам"""
        # Оболочка
        self.wrapper.setStyleSheet(f"""
            #wrapper {{
                border: 1px solid #000000;
                border-radius: 8px;
                background-color: {color};
            }}
        """)

        # Фото и текстовые метки
        for label in [
            self.photo_label,
            self.title_label,
            self.desc_label,
            self.manufacturer_label,
            self.supplier_label,
            self.unit_label,
            self.price_label,
        ]:
            label.setStyleSheet(f"background-color: {color};")

        # Специальная обработка остатка
        stock_color = "#ADD8E6" if self.product["stock"] <= 0 else color
        self.stock_label.setStyleSheet(f"background-color: {stock_color};")

        # Скидка — у неё свой стиль, но фон тоже меняем
        self.discount_label.setStyleSheet(f"""
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


class ProductListWidget(QWidget):
    def __init__(self, role, parent=None):
        super().__init__(parent)
        self.role = role
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # === Панель управления ===
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по всем полям...")
        self.search_input.textChanged.connect(self.update_display)
        controls_layout.addWidget(QLabel("Поиск:"))
        controls_layout.addWidget(self.search_input)

        self.supplier_filter = QComboBox()
        self.supplier_filter.addItem("Все поставщики")
        suppliers = sorted({p["supplier"] for p in PRODUCTS})
        self.supplier_filter.addItems(suppliers)
        self.supplier_filter.currentTextChanged.connect(self.update_display)
        controls_layout.addWidget(QLabel("Поставщик:"))
        controls_layout.addWidget(self.supplier_filter)

        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Сортировка по остаткам:"))
        self.sort_asc_radio = QRadioButton("По возрастанию")
        self.sort_desc_radio = QRadioButton("По убыванию")
        self.sort_group = QButtonGroup()
        self.sort_group.addButton(self.sort_asc_radio)
        self.sort_group.addButton(self.sort_desc_radio)
        self.sort_asc_radio.setChecked(True)
        self.sort_asc_radio.toggled.connect(self.update_display)
        sort_layout.addWidget(self.sort_asc_radio)
        sort_layout.addWidget(self.sort_desc_radio)
        controls_layout.addLayout(sort_layout)

        # --- Добавляем кнопку "Добавить товар" ---
        self.add_product_btn = QPushButton("Добавить товар")
        self.add_product_btn.setStyleSheet("background-color: #00FA9A;")
        # Видна только администратору
        self.add_product_btn.setVisible(self.role == "Администратор")
        self.add_product_btn.clicked.connect(self.open_add_dialog)
        controls_layout.addWidget(self.add_product_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: white;")
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(10)
        self.container_layout.addStretch()
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)

        self.update_display()

    def update_display(self):
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        search_text = self.search_input.text().strip().lower()
        selected_supplier = self.supplier_filter.currentText()
        sort_desc = self.sort_desc_radio.isChecked()

        filtered = []
        for p in get_all_products():
            # Фильтр по поставщику
            if selected_supplier != "Все поставщики" and p["supplier"] != selected_supplier:
                continue

            # Поиск: если строка поиска пустая — пропускаем фильтрацию
            if search_text:
                # Собираем все релевантные текстовые поля
                searchable_fields = [
                    str(p.get("name", "")),
                    str(p.get("category", "")),
                    str(p.get("manufacturer", "")),
                    str(p.get("supplier", "")),
                    str(p.get("description", ""))
                ]
                searchable_text = " ".join(searchable_fields).lower()

                # Разбиваем запрос на слова
                search_words = search_text.split()

                # Проверяем, что КАЖДОЕ слово есть в объединённом тексте
                if not all(word in searchable_text for word in search_words):
                    continue

            filtered.append(p)

        filtered.sort(key=lambda x: x["stock"], reverse=sort_desc)

        for product in filtered:
            card = ProductCard(product, role=self.role)
            if self.role == "Администратор":
                card.card_clicked.connect(self.open_edit_dialog)
            self.container_layout.insertWidget(self.container_layout.count() - 1, card)

    # --- Новые методы ---
    def open_add_dialog(self):
        dialog = ProductEditDialog(parent=self)
        dialog.product_saved.connect(self.on_product_saved)
        dialog.exec()

    def open_edit_dialog(self, product):
        dialog = ProductEditDialog(product_data=product, parent=self)
        dialog.product_saved.connect(self.on_product_saved)
        dialog.product_deleted.connect(self.on_product_deleted)
        dialog.exec()

    def on_product_saved(self, saved_product):
        # НЕ вызываем save_product повторно!
        # saved_product уже содержит данные, сохранённые в БД (включая id и article)

        # Обновляем глобальный список
        global PRODUCTS
        existing_index = next((i for i, p in enumerate(PRODUCTS) if p["id"] == saved_product["id"]), None)
        if existing_index is not None:
            PRODUCTS[existing_index] = saved_product
        else:
            PRODUCTS.append(saved_product)

        self.update_display()

    def on_product_deleted(self, product_id):
        global PRODUCTS
        # Удаляем товар из глобального списка
        PRODUCTS = [p for p in PRODUCTS if p["id"] != product_id]
        # Обновляем отображение
        self.update_display()