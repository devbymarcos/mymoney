from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QComboBox, QLineEdit, QDateEdit, QHeaderView
)
from PyQt5.QtCore import QDate, Qt, QLocale
from PyQt5.QtGui import QIcon
import os

from app.utils.formatting import format_currency_brl, format_date_brl
from app.ui.widgets.money_line_edit import MoneyLineEdit
from app.config import ICONS_DIR


class RevenuesTab(QWidget):
    def __init__(self, revenue_controller, category_service, on_refresh_tables, on_refresh_reports=None):
        super().__init__()
        self.revenue_controller = revenue_controller
        self.category_service = category_service
        self.on_refresh_tables = on_refresh_tables
        self.on_refresh_reports = on_refresh_reports

        self.revenue_edit_index = None
        self.revenue_row_to_index = []

        self._build_ui()
        self.reload_categories()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        form_layout = QFormLayout()
        self.revenue_date_edit = QDateEdit(); self.revenue_date_edit.setCalendarPopup(True); self.revenue_date_edit.setDisplayFormat("dd/MM/yyyy"); self.revenue_date_edit.setDate(QDate.currentDate())
        self.revenue_category_box = QComboBox()

        cat_row = QHBoxLayout()
        cat_row.addWidget(self.revenue_category_box)
        self.revenue_add_cat_btn = QPushButton(); self.revenue_add_cat_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); self.revenue_add_cat_btn.setProperty('variant','secondary'); self.revenue_add_cat_btn.setToolTip("Nova categoria de receita")
        self.revenue_add_cat_btn.clicked.connect(self._on_add_category)
        self.revenue_manage_cat_btn = QPushButton(); self.revenue_manage_cat_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg"))); self.revenue_manage_cat_btn.setProperty('variant','secondary'); self.revenue_manage_cat_btn.setToolTip("Gerenciar categorias de receita")
        self.revenue_manage_cat_btn.clicked.connect(self._on_manage_categories)
        cat_row.addWidget(self.revenue_add_cat_btn)
        cat_row.addWidget(self.revenue_manage_cat_btn)
        cat_row_w = QWidget(); cat_row_w.setLayout(cat_row)

        self.revenue_description_edit = QLineEdit()
        self.revenue_amount_edit = MoneyLineEdit()

        form_layout.addRow("Data:", self.revenue_date_edit)
        form_layout.addRow("Categoria:", cat_row_w)
        form_layout.addRow("Descrição:", self.revenue_description_edit)
        form_layout.addRow("Valor (R$):", self.revenue_amount_edit)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.revenue_add_btn = QPushButton("Adicionar receita"); self.revenue_add_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); self.revenue_add_btn.clicked.connect(self._on_add_revenue)
        self.revenue_delete_btn = QPushButton("Excluir selecionado(s)"); self.revenue_delete_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "trash.svg"))); self.revenue_delete_btn.setProperty('variant','secondary'); self.revenue_delete_btn.clicked.connect(self._on_delete_revenue)
        self.revenue_edit_btn = QPushButton("Editar selecionado"); self.revenue_edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg"))); self.revenue_edit_btn.setProperty('variant','secondary'); self.revenue_edit_btn.clicked.connect(self._on_edit_revenue_prepare)
        self.revenue_save_edit_btn = QPushButton("Salvar edição"); self.revenue_save_edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "save.svg"))); self.revenue_save_edit_btn.setProperty('variant','secondary'); self.revenue_save_edit_btn.setEnabled(False); self.revenue_save_edit_btn.clicked.connect(self._on_save_revenue_edit)
        btn_layout.addWidget(self.revenue_add_btn)
        btn_layout.addWidget(self.revenue_delete_btn)
        btn_layout.addWidget(self.revenue_edit_btn)
        btn_layout.addWidget(self.revenue_save_edit_btn)
        layout.addLayout(btn_layout)

        self.revenue_table = QTableWidget(0, 4)
        self.revenue_table.setHorizontalHeaderLabels(["Data", "Categoria", "Descrição", "Valor (R$)"])
        self.revenue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.revenue_table.setAlternatingRowColors(True)
        self.revenue_table.setShowGrid(False)
        self.revenue_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.revenue_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.revenue_table)

        self.revenue_total_label = QLabel("Total de receitas: R$ 0,00")
        layout.addWidget(self.revenue_total_label)

    def apply_locale(self, locale: QLocale):
        if isinstance(self.revenue_date_edit, QDateEdit):
            self.revenue_date_edit.setLocale(locale)
            self.revenue_date_edit.setDisplayFormat("dd/MM/yyyy")
            try:
                self.revenue_date_edit.calendarWidget().setFirstDayOfWeek(Qt.Monday)
            except Exception:
                pass

    def reload_categories(self):
        try:
            cats = self.category_service.list_by_type('revenue')
            self.revenue_category_box.clear(); self.revenue_category_box.addItems(cats)
        except Exception:
            pass

    def _on_add_revenue(self):
        date_str = self.revenue_date_edit.date().toString("yyyy-MM-dd")
        category = self.revenue_category_box.currentText()
        description = self.revenue_description_edit.text().strip()
        amount = self.revenue_amount_edit.value()
        if amount <= 0.0:
            return
        self.revenue_controller.add_revenue(date_str, category, description, amount)
        self.revenue_description_edit.clear()
        self.revenue_amount_edit.clear()
        if callable(self.on_refresh_tables):
            self.on_refresh_tables()
        if callable(self.on_refresh_reports):
            try:
                self.on_refresh_reports()
            except Exception:
                pass

    def _on_delete_revenue(self):
        selected = self.revenue_table.selectionModel().selectedRows()
        if not selected:
            return
        rows = sorted([idx.row() for idx in selected], reverse=True)
        if not hasattr(self, 'revenue_row_to_index'):
            return
        indices = []
        for r in rows:
            if 0 <= r < len(self.revenue_row_to_index):
                indices.append(self.revenue_row_to_index[r])
        self.revenue_controller.delete_revenues(indices)
        if callable(self.on_refresh_tables):
            self.on_refresh_tables()
        if callable(self.on_refresh_reports):
            try:
                self.on_refresh_reports()
            except Exception:
                pass

    def _on_edit_revenue_prepare(self):
        selected = self.revenue_table.selectionModel().selectedRows()
        if len(selected) != 1:
            return
        row = selected[0].row()
        if not hasattr(self, 'revenue_row_to_index') or row < 0 or row >= len(self.revenue_row_to_index):
            return
        full_idx = self.revenue_row_to_index[row]
        items = self.revenue_controller.list_revenues()
        if full_idx < 0 or full_idx >= len(items):
            return
        item = items[full_idx]
        qdate = QDate.fromString(item.get("date", ""), "yyyy-MM-dd")
        if not qdate.isValid():
            qdate = QDate.currentDate()
        self.revenue_date_edit.setDate(qdate)
        # garantir que a categoria exista
        name = (item.get("category", "") or '').strip()
        if name:
            cats = [self.revenue_category_box.itemText(i) for i in range(self.revenue_category_box.count())]
            if name not in cats:
                try:
                    self.category_service.add_category(name, 'revenue')
                    self.reload_categories()
                except Exception:
                    pass
        self.revenue_category_box.setCurrentText(item.get("category", ""))
        self.revenue_description_edit.setText(item.get("description", ""))
        amount = float(item.get("amount", 0.0))
        self.revenue_amount_edit.setText(format_currency_brl(amount).replace("R$ ", ""))
        self.revenue_edit_index = full_idx
        self.revenue_save_edit_btn.setEnabled(True)
        self.revenue_add_btn.setEnabled(False)
        self.revenue_delete_btn.setEnabled(False)

    def _on_save_revenue_edit(self):
        if self.revenue_edit_index is None:
            return
        date_str = self.revenue_date_edit.date().toString("yyyy-MM-dd")
        category = self.revenue_category_box.currentText()
        description = self.revenue_description_edit.text().strip()
        amount = self.revenue_amount_edit.value()
        if amount <= 0.0:
            return
        self.revenue_controller.update_revenue(self.revenue_edit_index, date_str, category, description, amount)
        self.revenue_edit_index = None
        self.revenue_save_edit_btn.setEnabled(False)
        self.revenue_add_btn.setEnabled(True)
        self.revenue_delete_btn.setEnabled(True)
        self.revenue_description_edit.clear()
        self.revenue_amount_edit.clear()
        if callable(self.on_refresh_tables):
            self.on_refresh_tables()
        if callable(self.on_refresh_reports):
            try:
                self.on_refresh_reports()
            except Exception:
                pass

    # Categorias (escopo de receitas)
    def _on_add_category(self):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        name, ok = QInputDialog.getText(self, "Nova categoria", "Nome da categoria:")
        if not ok:
            return
        name = (name or '').strip()
        if not name:
            return
        success = self.category_service.add_category(name, 'revenue')
        if not success:
            QMessageBox.information(self, "Categorias", "Categoria já existe.")
        self.reload_categories()
        self.revenue_category_box.setCurrentText(name)

    def _on_manage_categories(self):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        cats = self.category_service.list_by_type('revenue')
        if not cats:
            QMessageBox.information(self, "Categorias", "Nenhuma categoria encontrada.")
            return
        sel, ok = QInputDialog.getItem(self, "Gerenciar categorias", "Selecione a categoria:", cats, 0, False)
        if not ok:
            return
        action, ok2 = QInputDialog.getItem(self, "Ação", "Escolha a ação:", ["Renomear", "Excluir"], 0, False)
        if not ok2:
            return
        if action == "Renomear":
            new_name, ok3 = QInputDialog.getText(self, "Renomear categoria", "Novo nome:", text=sel)
            if not ok3:
                return
            new_name = (new_name or '').strip()
            if not new_name:
                return
            success = self.category_service.rename_category(sel, new_name, 'revenue')
            if success:
                QMessageBox.information(self, "Categorias", "Categoria renomeada com sucesso.")
            else:
                QMessageBox.warning(self, "Categorias", "Não foi possível renomear a categoria.")
        else:
            # Exclusão com reatribuição
            self.category_service.add_category("Outros", 'revenue')
            reassign_options = [c for c in cats if c != sel]
            if "Outros" not in reassign_options:
                reassign_options.append("Outros")
            if not reassign_options:
                QMessageBox.information(self, "Categorias", "Crie outra categoria para reatribuir antes de excluir.")
                return
            reassign_to, ok4 = QInputDialog.getItem(self, "Reatribuir lançamentos", "Mover lançamentos para:", reassign_options, 0, False)
            if not ok4:
                return
            success = self.category_service.delete_category(sel, 'revenue', reassign_to=reassign_to)
            if success:
                QMessageBox.information(self, "Categorias", "Categoria excluída e lançamentos reatribuídos.")
            else:
                QMessageBox.warning(self, "Categorias", "Não foi possível excluir a categoria.")
        self.reload_categories()