import re
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt


class MoneyLineEdit(QLineEdit):
    """Campo de entrada de moeda BRL com máscara automática.

    - Aceita apenas dígitos durante a edição.
    - Formata como 1.234,56 enquanto digita (últimos 2 dígitos são centavos).
    - Fornece método value() para obter float.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("0,00")
        self.setAlignment(Qt.AlignRight)
        self.textEdited.connect(self._apply_mask)

    def _apply_mask(self, text: str):
        digits = re.sub(r"\D", "", text)

        if not digits:
            formatted = "0,00"
        else:
            # Garante pelo menos 3 dígitos (00 centavos + inteiro)
            if len(digits) < 3:
                digits = digits.zfill(3)
            int_part = digits[:-2]
            dec_part = digits[-2:]
            int_part_formatted = f"{int(int_part):,}".replace(",", ".")
            formatted = f"{int_part_formatted},{dec_part}"

        # Preserva posição do cursor relativa ao fim
        prev_text = self.text()
        cursor_from_end = len(prev_text) - self.cursorPosition()

        self.blockSignals(True)
        self.setText(formatted)
        self.blockSignals(False)

        new_pos = len(formatted) - cursor_from_end
        new_pos = max(0, min(new_pos, len(formatted)))
        self.setCursorPosition(new_pos)

    def value(self) -> float:
        raw = self.text().strip().replace(".", "").replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            return 0.0