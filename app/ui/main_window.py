from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QHBoxLayout, QTabWidget, QHeaderView, QFrame, QInputDialog, QMessageBox
)
import os
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QIcon
from datetime import datetime, timedelta

from app.controllers.expense_controller import ExpenseController
from app.controllers.revenue_controller import RevenueController
from app.utils.formatting import format_currency_brl, format_date_brl
from app.ui.widgets.money_line_edit import MoneyLineEdit
from app.config import ICONS_DIR
from app.services.category_service import CategoryService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mymoney - Controle de Despesas")
        self.expense_controller = ExpenseController()
        self.revenue_controller = RevenueController()
        self.category_service = CategoryService()
        self.expense_edit_index = None
        self.revenue_edit_index = None
        self._setup_ui()
        self._apply_theme()
        self._refresh_tables()

    def _setup_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        central.setLayout(layout)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filtro de mês
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Mês:")
        self.month_filter = QDateEdit(); self.month_filter.setCalendarPopup(True); self.month_filter.setDisplayFormat("MM/yyyy"); self.month_filter.setDate(QDate.currentDate())
        self.month_filter.dateChanged.connect(self._on_month_changed)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.month_filter)
        layout.addLayout(filter_layout)

        # Abas
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Aba Despesas
        expense_tab = QWidget()
        expense_layout = QVBoxLayout(); expense_tab.setLayout(expense_layout)
        self._build_expense_section(expense_layout)
        self.tabs.addTab(expense_tab, "Despesas")
        self.tabs.setTabIcon(0, QIcon(os.path.join(ICONS_DIR, "expense.svg")))

        # Aba Receitas
        revenue_tab = QWidget()
        revenue_layout = QVBoxLayout(); revenue_tab.setLayout(revenue_layout)
        self._build_revenue_section(revenue_layout)
        self.tabs.addTab(revenue_tab, "Receitas")
        self.tabs.setTabIcon(1, QIcon(os.path.join(ICONS_DIR, "revenue.svg")))

        # Totais gerais (cards)
        self.summary_container = QFrame()
        self.summary_container.setProperty('role', 'summary')
        cards_layout = QHBoxLayout(); cards_layout.setSpacing(12)
        self.summary_container.setLayout(cards_layout)

        self.balance_card = QFrame(); self.balance_card.setProperty('role', 'card')
        bl = QVBoxLayout(); self.balance_card.setLayout(bl)
        bl_title = QLabel("Saldo"); bl_title.setObjectName("cardTitle")
        self.balance_value_label = QLabel("R$ 0,00"); self.balance_value_label.setObjectName("cardValue")
        self.balance_sub_label = QLabel("Acumulado"); self.balance_sub_label.setObjectName("cardSub")
        bl.addWidget(bl_title); bl.addWidget(self.balance_value_label); bl.addWidget(self.balance_sub_label)
        cards_layout.addWidget(self.balance_card)

        self.revenues_card = QFrame(); self.revenues_card.setProperty('role', 'card')
        rl = QVBoxLayout(); self.revenues_card.setLayout(rl)
        rl_title = QLabel("Receitas"); rl_title.setObjectName("cardTitle")
        self.revenue_card_value_label = QLabel("R$ 0,00"); self.revenue_card_value_label.setObjectName("cardValue")
        self.revenue_sub_label = QLabel("Mensal"); self.revenue_sub_label.setObjectName("cardSub")
        rl.addWidget(rl_title); rl.addWidget(self.revenue_card_value_label); rl.addWidget(self.revenue_sub_label)
        cards_layout.addWidget(self.revenues_card)

        self.expenses_card = QFrame(); self.expenses_card.setProperty('role', 'card')
        el = QVBoxLayout(); self.expenses_card.setLayout(el)
        el_title = QLabel("Despesas"); el_title.setObjectName("cardTitle")
        self.expense_card_value_label = QLabel("R$ 0,00"); self.expense_card_value_label.setObjectName("cardValue")
        self.expense_sub_label = QLabel("Mensal"); self.expense_sub_label.setObjectName("cardSub")
        el.addWidget(el_title); el.addWidget(self.expense_card_value_label); el.addWidget(self.expense_sub_label)
        cards_layout.addWidget(self.expenses_card)

        layout.addWidget(self.summary_container)

    def _build_expense_section(self, parent_layout: QVBoxLayout):
        form_layout = QFormLayout()
        self.expense_date_edit = QDateEdit(); self.expense_date_edit.setCalendarPopup(True); self.expense_date_edit.setDate(QDate.currentDate())
        self.expense_category_box = QComboBox()
        exp_cat_row = QHBoxLayout()
        exp_cat_row.addWidget(self.expense_category_box)
        self.expense_add_cat_btn = QPushButton(); self.expense_add_cat_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); self.expense_add_cat_btn.setProperty('variant','secondary'); self.expense_add_cat_btn.setToolTip("Nova categoria de despesa")
        self.expense_add_cat_btn.clicked.connect(lambda: self._on_add_category('expense'))
        self.expense_manage_cat_btn = QPushButton(); self.expense_manage_cat_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg"))); self.expense_manage_cat_btn.setProperty('variant','secondary'); self.expense_manage_cat_btn.setToolTip("Gerenciar categorias de despesa")
        self.expense_manage_cat_btn.clicked.connect(lambda: self._on_manage_categories('expense'))
        exp_cat_row.addWidget(self.expense_add_cat_btn)
        exp_cat_row.addWidget(self.expense_manage_cat_btn)
        exp_cat_row_w = QWidget(); exp_cat_row_w.setLayout(exp_cat_row)
        self.expense_description_edit = QLineEdit()
        self.expense_amount_edit = MoneyLineEdit()

        form_layout.addRow("Data:", self.expense_date_edit)
        form_layout.addRow("Categoria:", exp_cat_row_w)
        form_layout.addRow("Descrição:", self.expense_description_edit)
        form_layout.addRow("Valor (R$):", self.expense_amount_edit)
        parent_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Adicionar despesa"); add_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); add_btn.clicked.connect(self._on_add_expense)
        delete_btn = QPushButton("Excluir selecionado(s)"); delete_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "trash.svg"))); delete_btn.setProperty('variant', 'secondary'); delete_btn.clicked.connect(self._on_delete_expense)
        edit_btn = QPushButton("Editar selecionado"); edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg"))); edit_btn.setProperty('variant', 'secondary'); edit_btn.clicked.connect(self._on_edit_expense_prepare)
        self.expense_save_edit_btn = QPushButton("Salvar edição"); self.expense_save_edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "save.svg"))); self.expense_save_edit_btn.setProperty('variant', 'secondary'); self.expense_save_edit_btn.setEnabled(False); self.expense_save_edit_btn.clicked.connect(self._on_save_expense_edit)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(self.expense_save_edit_btn)
        parent_layout.addLayout(btn_layout)

        self.expense_table = QTableWidget(0, 4)
        self.expense_table.setHorizontalHeaderLabels(["Data", "Categoria", "Descrição", "Valor (R$)"])
        self.expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expense_table.setAlternatingRowColors(True)
        self.expense_table.setShowGrid(False)
        # Seleção por linha, múltipla
        self.expense_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.expense_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        parent_layout.addWidget(self.expense_table)

        self.expense_total_label = QLabel("Total de despesas: R$ 0,00")
        parent_layout.addWidget(self.expense_total_label)

    def _build_revenue_section(self, parent_layout: QVBoxLayout):
        form_layout = QFormLayout()
        self.revenue_date_edit = QDateEdit(); self.revenue_date_edit.setCalendarPopup(True); self.revenue_date_edit.setDate(QDate.currentDate())
        self.revenue_category_box = QComboBox()
        rev_cat_row = QHBoxLayout()
        rev_cat_row.addWidget(self.revenue_category_box)
        self.revenue_add_cat_btn = QPushButton(); self.revenue_add_cat_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); self.revenue_add_cat_btn.setProperty('variant','secondary'); self.revenue_add_cat_btn.setToolTip("Nova categoria de receita")
        self.revenue_add_cat_btn.clicked.connect(lambda: self._on_add_category('revenue'))
        self.revenue_manage_cat_btn = QPushButton(); self.revenue_manage_cat_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg"))); self.revenue_manage_cat_btn.setProperty('variant','secondary'); self.revenue_manage_cat_btn.setToolTip("Gerenciar categorias de receita")
        self.revenue_manage_cat_btn.clicked.connect(lambda: self._on_manage_categories('revenue'))
        rev_cat_row.addWidget(self.revenue_add_cat_btn)
        rev_cat_row.addWidget(self.revenue_manage_cat_btn)
        rev_cat_row_w = QWidget(); rev_cat_row_w.setLayout(rev_cat_row)
        self.revenue_description_edit = QLineEdit()
        self.revenue_amount_edit = MoneyLineEdit()

        form_layout.addRow("Data:", self.revenue_date_edit)
        form_layout.addRow("Categoria:", rev_cat_row_w)
        form_layout.addRow("Descrição:", self.revenue_description_edit)
        form_layout.addRow("Valor (R$):", self.revenue_amount_edit)
        parent_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Adicionar receita"); add_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); add_btn.clicked.connect(self._on_add_revenue)
        delete_btn = QPushButton("Excluir selecionado(s)"); delete_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "trash.svg"))); delete_btn.setProperty('variant', 'secondary'); delete_btn.clicked.connect(self._on_delete_revenue)
        edit_btn = QPushButton("Editar selecionado"); edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg"))); edit_btn.setProperty('variant', 'secondary'); edit_btn.clicked.connect(self._on_edit_revenue_prepare)
        self.revenue_save_edit_btn = QPushButton("Salvar edição"); self.revenue_save_edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "save.svg"))); self.revenue_save_edit_btn.setProperty('variant', 'secondary'); self.revenue_save_edit_btn.setEnabled(False); self.revenue_save_edit_btn.clicked.connect(self._on_save_revenue_edit)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(self.revenue_save_edit_btn)
        parent_layout.addLayout(btn_layout)

        self.revenue_table = QTableWidget(0, 4)
        self.revenue_table.setHorizontalHeaderLabels(["Data", "Categoria", "Descrição", "Valor (R$)"])
        self.revenue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.revenue_table.setAlternatingRowColors(True)
        self.revenue_table.setShowGrid(False)
        self.revenue_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.revenue_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        parent_layout.addWidget(self.revenue_table)

        self.revenue_total_label = QLabel("Total de receitas: R$ 0,00")
        parent_layout.addWidget(self.revenue_total_label)

    def _on_add_expense(self):
        date_str = self.expense_date_edit.date().toString("yyyy-MM-dd")
        category = self.expense_category_box.currentText()
        description = self.expense_description_edit.text().strip()

        amount = self.expense_amount_edit.value()

        if amount <= 0.0:
            # Sem diálogo de erro por simplicidade; apenas ignorar
            return

        self.expense_controller.add_expense(date_str, category, description, amount)
        self.expense_description_edit.clear()
        self.expense_amount_edit.clear()
        self._refresh_tables()
        self._load_categories()

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
        self._refresh_tables()

    def _on_delete_expense(self):
        selected = self.expense_table.selectionModel().selectedRows()
        if not selected:
            return
        indices = sorted([idx.row() for idx in selected], reverse=True)
        self.expense_controller.delete_expenses(indices)
        self._refresh_tables()

    def _on_edit_expense_prepare(self):
        selected = self.expense_table.selectionModel().selectedRows()
        if len(selected) != 1:
            return
        row = selected[0].row()
        items = self.expense_controller.list_expenses()
        if row < 0 or row >= len(items):
            return
        item = items[row]
        qdate = QDate.fromString(item.get("date", ""), "yyyy-MM-dd")
        if not qdate.isValid():
            qdate = QDate.currentDate()
        self.expense_date_edit.setDate(qdate)
        # Garante que a categoria exista no combo (sincroniza se necessário)
        self._ensure_category_in_combo(item.get("category", ""), 'expense')
        self.expense_category_box.setCurrentText(item.get("category", ""))
        self.expense_description_edit.setText(item.get("description", ""))
        # Define texto formatado para o campo de valor
        amount = float(item.get("amount", 0.0))
        self.expense_amount_edit.setText(format_currency_brl(amount).replace("R$ ", ""))
        self.expense_edit_index = row
        self.expense_save_edit_btn.setEnabled(True)

    def _on_save_expense_edit(self):
        if self.expense_edit_index is None:
            return
        date_str = self.expense_date_edit.date().toString("yyyy-MM-dd")
        category = self.expense_category_box.currentText()
        description = self.expense_description_edit.text().strip()
        amount = self.expense_amount_edit.value()
        if amount <= 0.0:
            return
        self.expense_controller.update_expense(self.expense_edit_index, date_str, category, description, amount)
        # Reset edição
        self.expense_edit_index = None
        self.expense_save_edit_btn.setEnabled(False)
        self.expense_description_edit.clear()
        self.expense_amount_edit.clear()
        self._refresh_tables()

    def _on_delete_revenue(self):
        selected = self.revenue_table.selectionModel().selectedRows()
        if not selected:
            return
        indices = sorted([idx.row() for idx in selected], reverse=True)
        self.revenue_controller.delete_revenues(indices)
        self._refresh_tables()

    def _on_edit_revenue_prepare(self):
        selected = self.revenue_table.selectionModel().selectedRows()
        if len(selected) != 1:
            return
        row = selected[0].row()
        items = self.revenue_controller.list_revenues()
        if row < 0 or row >= len(items):
            return
        item = items[row]
        qdate = QDate.fromString(item.get("date", ""), "yyyy-MM-dd")
        if not qdate.isValid():
            qdate = QDate.currentDate()
        self.revenue_date_edit.setDate(qdate)
        self._ensure_category_in_combo(item.get("category", ""), 'revenue')
        self.revenue_category_box.setCurrentText(item.get("category", ""))
        self.revenue_description_edit.setText(item.get("description", ""))
        amount = float(item.get("amount", 0.0))
        self.revenue_amount_edit.setText(format_currency_brl(amount).replace("R$ ", ""))
        self.revenue_edit_index = row
        self.revenue_save_edit_btn.setEnabled(True)

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
        self.revenue_description_edit.clear()
        self.revenue_amount_edit.clear()
        self._refresh_tables()
        self._load_categories()

    def _load_categories(self):
        # Carrega categorias do banco para ambos combos
        expense_cats = self.category_service.list_by_type('expense')
        revenue_cats = self.category_service.list_by_type('revenue')
        self.expense_category_box.clear(); self.expense_category_box.addItems(expense_cats)
        self.revenue_category_box.clear(); self.revenue_category_box.addItems(revenue_cats)

    def _on_add_category(self, cat_type: str):
        name, ok = QInputDialog.getText(self, "Nova categoria", "Nome da categoria:")
        if not ok:
            return
        name = name.strip()
        if not name:
            return
        success = self.category_service.add_category(name, cat_type)
        if not success:
            QMessageBox.information(self, "Categorias", "Categoria já existe.")
        self._load_categories()
        # Seleciona a recém criada
        if cat_type == 'expense':
            self.expense_category_box.setCurrentText(name)
        else:
            self.revenue_category_box.setCurrentText(name)

    def _ensure_category_in_combo(self, name: str, cat_type: str):
        name = (name or '').strip()
        if not name:
            return
        # Se a categoria de um item não estiver ainda cadastrada, insere e recarrega
        if cat_type == 'expense':
            items = [self.expense_category_box.itemText(i) for i in range(self.expense_category_box.count())]
        else:
            items = [self.revenue_category_box.itemText(i) for i in range(self.revenue_category_box.count())]
        if name not in items:
            self.category_service.add_category(name, cat_type)
            self._load_categories()

    def _on_manage_categories(self, cat_type: str):
        # Selecionar categoria para gerenciar
        cats = self.category_service.list_by_type(cat_type)
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
            new_name = new_name.strip()
            if not new_name:
                return
            success = self.category_service.rename_category(sel, new_name, cat_type)
            if success:
                QMessageBox.information(self, "Categorias", "Categoria renomeada com sucesso.")
            else:
                QMessageBox.warning(self, "Categorias", "Não foi possível renomear a categoria.")
        else:
            # Exclusão com reatribuição
            # Garantir opção "Outros"
            self.category_service.add_category("Outros", cat_type)
            reassign_options = [c for c in cats if c != sel]
            if "Outros" not in reassign_options:
                reassign_options.append("Outros")
            if not reassign_options:
                QMessageBox.information(self, "Categorias", "Crie outra categoria para reatribuir antes de excluir.")
                return
            reassign_to, ok4 = QInputDialog.getItem(self, "Reatribuir lançamentos", "Mover lançamentos para:", reassign_options, 0, False)
            if not ok4:
                return
            success = self.category_service.delete_category(sel, cat_type, reassign_to=reassign_to)
            if success:
                QMessageBox.information(self, "Categorias", "Categoria excluída e lançamentos reatribuídos.")
            else:
                QMessageBox.warning(self, "Categorias", "Não foi possível excluir a categoria.")
        # Recarregar UI
        self._load_categories()
        self._refresh_tables()
    def _refresh_tables(self):
        # Mês selecionado
        sel_qdate = self.month_filter.date()
        sel_year = sel_qdate.year()
        sel_month = sel_qdate.month()
        month_str = sel_qdate.toString("MM/yyyy")
        # Último dia do mês selecionado
        next_month = 1 if sel_month == 12 else sel_month + 1
        next_year = sel_year + 1 if sel_month == 12 else sel_year
        end_of_month = datetime(next_year, next_month, 1) - timedelta(days=1)

        # Despesas
        expenses = self.expense_controller.list_expenses()
        # Filtrar por mês selecionado
        expenses_month = []
        for item in expenses:
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt.year == sel_year and dt.month == sel_month:
                    expenses_month.append(item)
            except Exception:
                continue
        self.expense_table.setRowCount(0)
        for item in expenses_month:
            row = self.expense_table.rowCount()
            self.expense_table.insertRow(row)
            self.expense_table.setItem(row, 0, QTableWidgetItem(format_date_brl(item.get("date", ""))))
            self.expense_table.setItem(row, 1, QTableWidgetItem(item.get("category", "")))
            self.expense_table.setItem(row, 2, QTableWidgetItem(item.get("description", "")))
            amount_item = QTableWidgetItem(format_currency_brl(item.get("amount", 0.0)))
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.expense_table.setItem(row, 3, amount_item)

        expense_month_total = sum(float(i.get("amount", 0.0)) for i in expenses_month)
        self.expense_total_label.setText(f"Total do mês: {format_currency_brl(expense_month_total)}")

        # Receitas
        revenues = self.revenue_controller.list_revenues()
        revenues_month = []
        for item in revenues:
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt.year == sel_year and dt.month == sel_month:
                    revenues_month.append(item)
            except Exception:
                continue
        self.revenue_table.setRowCount(0)
        for item in revenues_month:
            row = self.revenue_table.rowCount()
            self.revenue_table.insertRow(row)
            self.revenue_table.setItem(row, 0, QTableWidgetItem(format_date_brl(item.get("date", ""))))
            self.revenue_table.setItem(row, 1, QTableWidgetItem(item.get("category", "")))
            self.revenue_table.setItem(row, 2, QTableWidgetItem(item.get("description", "")))
            amount_item = QTableWidgetItem(format_currency_brl(item.get("amount", 0.0)))
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.revenue_table.setItem(row, 3, amount_item)

        revenue_month_total = sum(float(i.get("amount", 0.0)) for i in revenues_month)
        self.revenue_total_label.setText(f"Total do mês: {format_currency_brl(revenue_month_total)}")

        # Totais acumulados até o fim do mês selecionado
        expenses_cum = 0.0
        for item in expenses:
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt <= end_of_month:
                    expenses_cum += float(item.get("amount", 0.0))
            except Exception:
                continue
        revenues_cum = 0.0
        for item in revenues:
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt <= end_of_month:
                    revenues_cum += float(item.get("amount", 0.0))
            except Exception:
                continue

        # Atualizar cartões: receitas/despesas do mês; saldo acumulado
        self.revenue_card_value_label.setText(format_currency_brl(revenue_month_total))
        self.expense_card_value_label.setText(format_currency_brl(expense_month_total))
        balance = revenues_cum - expenses_cum
        self.balance_value_label.setText(format_currency_brl(balance))
        # Subtextos dos cards
        if hasattr(self, 'revenue_sub_label'):
            self.revenue_sub_label.setText(f"Mensal ({month_str})")
        if hasattr(self, 'expense_sub_label'):
            self.expense_sub_label.setText(f"Mensal ({month_str})")
        if hasattr(self, 'balance_sub_label'):
            self.balance_sub_label.setText(f"Acumulado até {month_str}")
        if balance >= 0:
            self.balance_value_label.setStyleSheet("color:#15803d;")
        else:
            self.balance_value_label.setStyleSheet("color:#b91c1c;")

    def _on_month_changed(self, *_):
        self._refresh_tables()

    def _apply_theme(self):
        # Tema leve com acentos modernos
        self.setStyleSheet(
            """
            QMainWindow { background: #f8fafc; }
            QLabel { font-size: 12px; }
            QTabWidget::pane { border: 1px solid #e5e7eb; border-radius: 8px; padding: 4px; }
            QTabBar::tab { background: #e5e7eb; padding: 8px 12px; border-radius: 6px; margin: 2px; }
            QTabBar::tab:selected { background: #dbeafe; color: #1e40af; }
            QHeaderView::section { background: #eef2ff; padding: 6px; border: none; font-weight: 600; }
            QTableWidget { alternate-background-color: #ffffff; background: #f8fafc; }
            QTableWidget::item:selected { background: #bfdbfe; color: #111827; }
            QTableWidget::item:hover { background: #e0f2fe; }
            QPushButton { background: #1d4ed8; color: white; border: none; padding: 8px 12px; border-radius: 6px; }
            QPushButton:hover { background: #2563eb; }
            QPushButton:disabled { background: #9ca3af; color: #f3f4f6; }
            QPushButton[variant="secondary"] { background: transparent; color: #1d4ed8; border: 1px solid #93c5fd; }
            QPushButton[variant="secondary"]:hover { background: #eff6ff; }
            QLineEdit, QComboBox, QDateEdit { background: white; border: 1px solid #e5e7eb; border-radius: 6px; padding: 6px; }
            QFrame[role="card"] { background: #F0F4FF; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; }
            QLabel#cardTitle { color: #1F3B73; font-weight: 600; }
            QLabel#cardValue { font-size: 16px; font-weight: 700; }
            QLabel#cardSub { color: #64748b; font-size: 11px; }
            """
        )