"""Styled dialogs for NeuroCore."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QTextEdit,
                                QVBoxLayout)

from .icons import make_icon
from .theme import C, QSS


def _style_dialog(dlg):
    dlg.setStyleSheet(QSS + "QDialog { background: " + C["bg"] + "; }")


class PresetDialog(QDialog):
    def __init__(self, parent, preset=None):
        super().__init__(parent)
        self.setWindowTitle("Пресет")
        self.resize(620, 540)
        _style_dialog(self)

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(8)

        title = QLabel("Пресет агента")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        v.addWidget(title)
        v.addSpacing(6)

        def field(label, widget):
            l = QLabel(label)
            l.setStyleSheet("color: " + C["text_dim"] + "; font-size: 12px;")
            v.addWidget(l)
            v.addWidget(widget)

        self.name_e = QLineEdit()
        self.name_e.setStyleSheet(
            "background: " + C["card"] + "; border: 1px solid " + C["border"] +
            "; border-radius: 8px; padding: 8px 10px; color: " + C["text"] + ";")
        field("Имя", self.name_e)

        self.desc_e = QLineEdit()
        self.desc_e.setStyleSheet(self.name_e.styleSheet())
        field("Описание", self.desc_e)

        self.model_c = QComboBox()
        self.model_c.setStyleSheet(
            "QComboBox { background: " + C["card"] + "; border: 1px solid " +
            C["border"] + "; border-radius: 8px; padding: 8px 10px; "
            "color: " + C["text"] + "; } "
            "QComboBox QAbstractItemView { background: " + C["card"] +
            "; color: " + C["text"] + "; selection-background-color: " +
            C["accent"] + "; }")
        self.model_c.addItems(["deepseek-v4-pro", "deepseek-v4-flash",
                                "deepseek-chat", "deepseek-reasoner",
                                "gpt-4o", "gpt-4o-mini"])
        field("Модель", self.model_c)

        self.prompt_e = QTextEdit()
        self.prompt_e.setStyleSheet(
            "background: " + C["card"] + "; border: 1px solid " + C["border"] +
            "; border-radius: 8px; padding: 8px; color: " + C["text"] +
            "; font-family: Consolas; font-size: 12px;")
        field("Системный промпт", self.prompt_e)

        v.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)

        cancel = QPushButton("Отмена")
        cancel.setStyleSheet(
            "QPushButton { background: " + C["card"] + "; border: none; "
            "color: " + C["text"] + "; padding: 10px 20px; border-radius: 8px; }"
            "QPushButton:hover { background: " + C["card_hover"] + "; }")
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)

        save = QPushButton("Сохранить")
        save.setStyleSheet(
            "QPushButton { background: " + C["accent"] + "; border: none; "
            "color: white; padding: 10px 20px; border-radius: 8px; "
            "font-weight: 600; }"
            "QPushButton:hover { background: " + C["accent_hover"] + "; }")
        save.clicked.connect(self.accept)
        row.addWidget(save)
        v.addLayout(row)

        if preset:
            self.name_e.setText(preset.name)
            self.desc_e.setText(preset.description or "")
            self.prompt_e.setPlainText(preset.system_prompt or "")
            if preset.model:
                idx = self.model_c.findText(preset.model)
                if idx >= 0:
                    self.model_c.setCurrentIndex(idx)

    def values(self):
        return {
            "name": self.name_e.text().strip(),
            "description": self.desc_e.text().strip(),
            "model": self.model_c.currentText(),
            "system_prompt": self.prompt_e.toPlainText().strip(),
        }


class ProviderDialog(QDialog):
    def __init__(self, parent, provider=None):
        super().__init__(parent)
        self.setWindowTitle("Провайдер")
        self.resize(560, 460)
        _style_dialog(self)

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(8)

        title = QLabel("Провайдер AI")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        v.addWidget(title)
        v.addSpacing(6)

        def field(label, widget):
            l = QLabel(label)
            l.setStyleSheet("color: " + C["text_dim"] + "; font-size: 12px;")
            v.addWidget(l)
            v.addWidget(widget)

        style = ("background: " + C["card"] + "; border: 1px solid " +
                 C["border"] + "; border-radius: 8px; padding: 8px 10px; "
                 "color: " + C["text"] + ";")

        self.name_e = QLineEdit()
        self.name_e.setStyleSheet(style)
        field("Имя", self.name_e)

        self.kind_c = QComboBox()
        self.kind_c.addItems(["opendeep", "openai_compat"])
        self.kind_c.setStyleSheet(style)
        field("Тип", self.kind_c)

        self.base_e = QLineEdit()
        self.base_e.setStyleSheet(style)
        self.base_e.setPlaceholderText("https://api.example.com/v1")
        field("Base URL (только для openai_compat)", self.base_e)

        self.key_e = QLineEdit()
        self.key_e.setStyleSheet(style)
        self.key_e.setEchoMode(QLineEdit.Password)
        field("API-ключ", self.key_e)

        self.models_e = QTextEdit()
        self.models_e.setFixedHeight(80)
        self.models_e.setStyleSheet(style + "font-family: Consolas;")
        self.models_e.setPlaceholderText("gpt-4o\ngpt-4o-mini\n…")
        field("Модели (по одной на строку)", self.models_e)

        v.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton("Отмена")
        cancel.setStyleSheet(
            "QPushButton { background: " + C["card"] + "; border: none; "
            "color: " + C["text"] + "; padding: 10px 20px; border-radius: 8px; }")
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)

        save = QPushButton("Сохранить")
        save.setStyleSheet(
            "QPushButton { background: " + C["accent"] + "; border: none; "
            "color: white; padding: 10px 20px; border-radius: 8px; }")
        save.clicked.connect(self.accept)
        row.addWidget(save)
        v.addLayout(row)

        if provider:
            self.name_e.setText(provider["name"])
            idx = self.kind_c.findText(provider["kind"])
            if idx >= 0:
                self.kind_c.setCurrentIndex(idx)
            self.base_e.setText(provider.get("base_url", ""))
            self.key_e.setText(provider.get("api_key", ""))
            self.models_e.setPlainText("\n".join(provider.get("models", [])))

    def values(self):
        return {
            "name": self.name_e.text().strip() or "Provider",
            "kind": self.kind_c.currentText(),
            "base_url": self.base_e.text().strip(),
            "api_key": self.key_e.text().strip(),
            "models": [m.strip() for m in
                        self.models_e.toPlainText().split("\n") if m.strip()],
        }
