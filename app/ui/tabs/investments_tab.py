from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout, QTabWidget, QHeaderView, QInputDialog, QMessageBox
)
from PyQt5.QtCore import QDate, Qt, QSize, QLocale
from PyQt5.QtGui import QIcon
import os

from app.controllers.investment_controller import InvestmentController
from app.ui.widgets.money_line_edit import MoneyLineEdit
from app.utils.formatting import format_currency_brl, format_date_brl
from app.config import ICONS_DIR
from app.services.broker_service import BrokerService


class InvestmentsTab(QWidget):
    """Aba de Investimentos dividida em sub-abas: Investimento e Aportes."""

    def __init__(self, investment_controller: InvestmentController, broker_service: BrokerService):
        super().__init__()
        self.investment_controller = investment_controller
        self.broker_service = broker_service
        self.investment_edit_index = None
        self.current_investment_index = None

        layout = QVBoxLayout(self)

        # Sub-abas
        investments_tabs = QTabWidget()
        investments_tabs.setElideMode(Qt.ElideNone)
        investments_tabs.setIconSize(QSize(16, 16))
        try:
            investments_tabs.tabBar().setExpanding(True)
        except Exception:
            pass
        investments_tabs.setStyleSheet(
            """
            QTabWidget::pane { border: none; }
            QTabBar::tab { padding: 10px 16px; padding-left: 18px; padding-right: 18px; min-width: 140px; margin: 2px; border-radius: 6px; }
            QTabBar::tab:selected { background: #eaf1fb; color: #1f2937; font-weight: 600; border: 1px solid #c7d2fe; padding: 10px 16px; padding-left: 18px; padding-right: 18px; }
            QTabBar::tab:hover { background: #f3f6fc; }
            """
        )

        # Aba Investimento
        inv_tab = QWidget()
        inv_layout = QVBoxLayout(inv_tab)

        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.investment_name_edit = QLineEdit()

        # Corretora: combo + botões
        self.investment_broker_box = QComboBox()
        broker_row = QHBoxLayout()
        broker_row.addWidget(self.investment_broker_box)
        self.broker_add_btn = QPushButton(); self.broker_add_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); self.broker_add_btn.setProperty('variant','secondary'); self.broker_add_btn.setToolTip("Nova corretora")
        self.broker_add_btn.clicked.connect(self._on_add_broker)
        self.broker_manage_btn = QPushButton(); self.broker_manage_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg"))); self.broker_manage_btn.setProperty('variant','secondary'); self.broker_manage_btn.setToolTip("Gerenciar corretoras")
        self.broker_manage_btn.clicked.connect(self._on_manage_brokers)
        broker_row.addWidget(self.broker_add_btn)
        broker_row.addWidget(self.broker_manage_btn)
        broker_row_w = QWidget(); broker_row_w.setLayout(broker_row)

        self.investment_start_date_edit = QDateEdit(); self.investment_start_date_edit.setCalendarPopup(True); self.investment_start_date_edit.setDisplayFormat("dd/MM/yyyy"); self.investment_start_date_edit.setDate(QDate.currentDate())
        self.investment_description_edit = QLineEdit()
        self.investment_initial_amount_edit = MoneyLineEdit()

        form_layout.addRow("Investimento:", self.investment_name_edit)
        form_layout.addRow("Corretora:", broker_row_w)
        form_layout.addRow("Data inicial:", self.investment_start_date_edit)
        form_layout.addRow("Descrição:", self.investment_description_edit)
        form_layout.addRow("Valor inicial (R$):", self.investment_initial_amount_edit)
        inv_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.investment_add_btn = QPushButton("Adicionar investimento"); self.investment_add_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); self.investment_add_btn.clicked.connect(self._on_add_investment)
        self.investment_delete_btn = QPushButton("Excluir selecionado(s)"); self.investment_delete_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "trash.svg"))); self.investment_delete_btn.setProperty('variant', 'secondary'); self.investment_delete_btn.clicked.connect(self._on_delete_investment)
        inv_edit_btn = QPushButton("Editar selecionado"); inv_edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg"))); inv_edit_btn.setProperty('variant', 'secondary'); inv_edit_btn.clicked.connect(self._on_edit_investment_prepare)
        self.investment_save_edit_btn = QPushButton("Salvar edição"); self.investment_save_edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "save.svg"))); self.investment_save_edit_btn.setProperty('variant', 'secondary'); self.investment_save_edit_btn.setEnabled(False); self.investment_save_edit_btn.clicked.connect(self._on_save_investment_edit)
        btn_layout.addWidget(self.investment_add_btn)
        btn_layout.addWidget(self.investment_delete_btn)
        btn_layout.addWidget(inv_edit_btn)
        btn_layout.addWidget(self.investment_save_edit_btn)
        inv_layout.addLayout(btn_layout)

        self.investment_table = QTableWidget(0, 6)
        self.investment_table.setHorizontalHeaderLabels(["Investimento", "Corretora", "Data", "Valor inicial (R$)", "Aportes (R$)", "Total investido (R$)"])
        self.investment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.investment_table.setAlternatingRowColors(True)
        self.investment_table.setShowGrid(False)
        self.investment_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.investment_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.investment_table.itemSelectionChanged.connect(self._on_investment_selection_changed)
        inv_layout.addWidget(self.investment_table)

        self.investment_total_label = QLabel("Total investido: R$ 0,00")
        self.investment_total_label.setObjectName("cardTitle")
        inv_layout.addWidget(self.investment_total_label)

        # Aba Aportes
        aport_tab = QWidget()
        aport_layout = QVBoxLayout(aport_tab)

        aporte_form = QFormLayout()
        aporte_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.aporte_investment_box = QComboBox()
        aporte_form.addRow("Investimento:", self.aporte_investment_box)
        self.aporte_date_edit = QDateEdit(); self.aporte_date_edit.setCalendarPopup(True); self.aporte_date_edit.setDisplayFormat("dd/MM/yyyy"); self.aporte_date_edit.setDate(QDate.currentDate())
        self.aporte_description_edit = QLineEdit()
        self.aporte_amount_edit = MoneyLineEdit()
        aporte_form.addRow("Data:", self.aporte_date_edit)
        aporte_form.addRow("Descrição:", self.aporte_description_edit)
        aporte_form.addRow("Valor (R$):", self.aporte_amount_edit)
        aport_layout.addLayout(aporte_form)

        aporte_btns = QHBoxLayout()
        self.aporte_add_btn = QPushButton("Adicionar aporte"); self.aporte_add_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); self.aporte_add_btn.clicked.connect(self._on_add_aporte)
        self.aporte_delete_btn = QPushButton("Excluir aporte(s)"); self.aporte_delete_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "trash.svg"))); self.aporte_delete_btn.setProperty('variant','secondary'); self.aporte_delete_btn.clicked.connect(self._on_delete_aporte)
        aporte_btns.addWidget(self.aporte_add_btn)
        aporte_btns.addWidget(self.aporte_delete_btn)
        aport_layout.addLayout(aporte_btns)

        self.contributions_table = QTableWidget(0, 3)
        self.contributions_table.setHorizontalHeaderLabels(["Data", "Descrição", "Valor (R$)"])
        self.contributions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.contributions_table.setAlternatingRowColors(True)
        self.contributions_table.setShowGrid(False)
        self.contributions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.contributions_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        aport_layout.addWidget(self.contributions_table)

        investments_tabs.addTab(inv_tab, "Investimento")
        investments_tabs.addTab(aport_tab, "Aportes")
        layout.addWidget(investments_tabs)

        # Inicializações
        self._load_brokers()
        self._refresh_investments()

    # ---- API pública ----
    def apply_locale(self, locale: QLocale):
        if isinstance(self.investment_start_date_edit, QDateEdit):
            self.investment_start_date_edit.setLocale(locale)
            self.investment_start_date_edit.setDisplayFormat("dd/MM/yyyy")
            try:
                self.investment_start_date_edit.calendarWidget().setFirstDayOfWeek(Qt.Monday)
            except Exception:
                pass
        if isinstance(self.aporte_date_edit, QDateEdit):
            self.aporte_date_edit.setLocale(locale)
            self.aporte_date_edit.setDisplayFormat("dd/MM/yyyy")
            try:
                self.aporte_date_edit.calendarWidget().setFirstDayOfWeek(Qt.Monday)
            except Exception:
                pass

    def refresh(self):
        self._refresh_investments()

    # ---- Implementação ----
    def _load_brokers(self):
        brokers = self.broker_service.list_all()
        self.investment_broker_box.clear(); self.investment_broker_box.addItems(brokers)
        self.aporte_investment_box.clear()
        invs = self.investment_controller.list_investments()
        self.aporte_investment_box.addItems([f"{i.get('name','')} ({i.get('broker','')})" for i in invs])

    def _on_add_broker(self):
        name, ok = QInputDialog.getText(self, "Nova corretora", "Nome:")
        if not ok:
            return
        name = (name or '').strip()
        if not name:
            return
        success = self.broker_service.add_broker(name)
        if not success:
            QMessageBox.information(self, "Corretoras", "Corretora já existe.")
        self._load_brokers()
        self.investment_broker_box.setCurrentText(name)

    def _on_manage_brokers(self):
        brokers = self.broker_service.list_all()
        if not brokers:
            QMessageBox.information(self, "Corretoras", "Nenhuma corretora encontrada.")
            return
        sel, ok = QInputDialog.getItem(self, "Gerenciar corretoras", "Selecione a corretora:", brokers, 0, False)
        if not ok:
            return
        action, ok2 = QInputDialog.getItem(self, "Ação", "Escolha a ação:", ["Renomear", "Excluir"], 0, False)
        if not ok2:
            return
        if action == "Renomear":
            new_name, ok3 = QInputDialog.getText(self, "Renomear corretora", "Novo nome:", text=sel)
            if not ok3:
                return
            new_name = (new_name or '').strip()
            if not new_name:
                return
            success = self.broker_service.rename_broker(sel, new_name)
            QMessageBox.information(self, "Corretoras", "Corretora renomeada." if success else "Não foi possível renomear.")
        else:
            reassign_options = [b for b in brokers if b != sel]
            if not reassign_options:
                QMessageBox.information(self, "Corretoras", "Crie outra corretora para reatribuir antes de excluir.")
                return
            reassign_to, ok4 = QInputDialog.getItem(self, "Reatribuir investimentos", "Mover para:", reassign_options, 0, False)
            if not ok4:
                return
            success = self.broker_service.delete_broker(sel, reassign_to=reassign_to)
            QMessageBox.information(self, "Corretoras", "Corretora excluída e investimentos reatribuídos." if success else "Não foi possível excluir.")
        self._load_brokers()
        self._refresh_investments()

    def _on_add_investment(self):
        name = self.investment_name_edit.text().strip()
        broker = self.investment_broker_box.currentText().strip()
        start_date = self.investment_start_date_edit.date().toString("yyyy-MM-dd")
        description = self.investment_description_edit.text().strip()
        initial_amount = self.investment_initial_amount_edit.value()
        if not name or not broker:
            return
        self.investment_controller.add_investment(name, broker, start_date, description, initial_amount)
        self.investment_name_edit.clear(); self.investment_description_edit.clear(); self.investment_initial_amount_edit.clear()
        self._load_brokers()
        self._refresh_investments()

    def _refresh_investments(self):
        items = self.investment_controller.list_investments()
        self.investment_row_to_index = list(range(len(items)))
        self.investment_table.setRowCount(0)
        for idx, item in enumerate(items):
            row = self.investment_table.rowCount()
            self.investment_table.insertRow(row)
            self.investment_table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
            self.investment_table.setItem(row, 1, QTableWidgetItem(item.get("broker", "")))
            self.investment_table.setItem(row, 2, QTableWidgetItem(format_date_brl(item.get("start_date", ""))))
            init_item = QTableWidgetItem(format_currency_brl(item.get("initial_amount", 0.0)))
            init_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.investment_table.setItem(row, 3, init_item)
            contrib_sum = self.investment_controller.contributions_sum(idx)
            contrib_item = QTableWidgetItem(format_currency_brl(contrib_sum))
            contrib_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.investment_table.setItem(row, 4, contrib_item)
            total_item = QTableWidgetItem(format_currency_brl(float(item.get("initial_amount", 0.0)) + contrib_sum))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.investment_table.setItem(row, 5, total_item)
        total = self.investment_controller.total_invested()
        self.investment_total_label.setText(f"Total investido: {format_currency_brl(total)}")
        self._load_brokers()
        self._refresh_contributions_table()

    def _on_delete_investment(self):
        selected = self.investment_table.selectionModel().selectedRows()
        if not selected:
            return
        indices = []
        for s in selected:
            row = s.row()
            if row < 0 or row >= len(self.investment_row_to_index):
                continue
            indices.append(self.investment_row_to_index[row])
        if indices:
            self.investment_controller.delete_investments(indices)
            self._refresh_investments()

    def _on_edit_investment_prepare(self):
        selected = self.investment_table.selectionModel().selectedRows()
        if len(selected) != 1:
            return
        row = selected[0].row()
        if not hasattr(self, 'investment_row_to_index') or row < 0 or row >= len(self.investment_row_to_index):
            return
        full_idx = self.investment_row_to_index[row]
        items = self.investment_controller.list_investments()
        if full_idx < 0 or full_idx >= len(items):
            return
        item = items[full_idx]
        self.investment_name_edit.setText(item.get("name", ""))
        broker = item.get("broker", "")
        if broker and broker not in [self.investment_broker_box.itemText(i) for i in range(self.investment_broker_box.count())]:
            self.broker_service.add_broker(broker)
            self._load_brokers()
        self.investment_broker_box.setCurrentText(broker)
        qdate = QDate.fromString(item.get("start_date", ""), "yyyy-MM-dd")
        if not qdate.isValid():
            qdate = QDate.currentDate()
        self.investment_start_date_edit.setDate(qdate)
        self.investment_description_edit.setText(item.get("description", ""))
        self.investment_initial_amount_edit.setText(format_currency_brl(float(item.get("initial_amount", 0.0))).replace("R$ ", ""))
        self.investment_edit_index = full_idx
        self.investment_save_edit_btn.setEnabled(True)
        if hasattr(self, 'investment_add_btn'):
            self.investment_add_btn.setEnabled(False)
        if hasattr(self, 'investment_delete_btn'):
            self.investment_delete_btn.setEnabled(False)

    def _on_save_investment_edit(self):
        if self.investment_edit_index is None:
            return
        name = self.investment_name_edit.text().strip()
        broker = self.investment_broker_box.currentText().strip()
        start_date = self.investment_start_date_edit.date().toString("yyyy-MM-dd")
        description = self.investment_description_edit.text().strip()
        initial_amount = self.investment_initial_amount_edit.value()
        if not name or not broker:
            return
        self.investment_controller.update_investment(self.investment_edit_index, name, broker, start_date, description, initial_amount)
        self.investment_edit_index = None
        self.investment_save_edit_btn.setEnabled(False)
        if hasattr(self, 'investment_add_btn'):
            self.investment_add_btn.setEnabled(True)
        if hasattr(self, 'investment_delete_btn'):
            self.investment_delete_btn.setEnabled(True)
        self.investment_name_edit.clear(); self.investment_description_edit.clear(); self.investment_initial_amount_edit.clear()
        self._refresh_investments()

    def _on_investment_selection_changed(self):
        selected = self.investment_table.selectionModel().selectedRows()
        if len(selected) == 1:
            row = selected[0].row()
            if hasattr(self, 'investment_row_to_index') and 0 <= row < len(self.investment_row_to_index):
                self.current_investment_index = self.investment_row_to_index[row]
                items = self.investment_controller.list_investments()
                if 0 <= self.current_investment_index < len(items):
                    label = f"{items[self.current_investment_index].get('name','')} ({items[self.current_investment_index].get('broker','')})"
                    idx = self.aporte_investment_box.findText(label)
                    if idx >= 0:
                        self.aporte_investment_box.setCurrentIndex(idx)
        self._refresh_contributions_table()

    def _investment_index_for_aporte(self) -> int | None:
        labels = [f"{i.get('name','')} ({i.get('broker','')})" for i in self.investment_controller.list_investments()]
        cur = self.aporte_investment_box.currentText()
        try:
            return labels.index(cur)
        except ValueError:
            return self.current_investment_index

    def _refresh_contributions_table(self):
        inv_idx = self._investment_index_for_aporte()
        if inv_idx is None:
            self.contributions_table.setRowCount(0)
            self.contribution_row_to_index = []
            return
        contribs = self.investment_controller.list_contributions(inv_idx)
        self.contribution_row_to_index = list(range(len(contribs)))
        self.contributions_table.setRowCount(0)
        for item in contribs:
            row = self.contributions_table.rowCount()
            self.contributions_table.insertRow(row)
            self.contributions_table.setItem(row, 0, QTableWidgetItem(format_date_brl(item.get('date',''))))
            self.contributions_table.setItem(row, 1, QTableWidgetItem(item.get('description','')))
            amt_item = QTableWidgetItem(format_currency_brl(item.get('amount',0.0)))
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.contributions_table.setItem(row, 2, amt_item)

    def _on_add_aporte(self):
        inv_idx = self._investment_index_for_aporte()
        if inv_idx is None:
            return
        date_str = self.aporte_date_edit.date().toString("yyyy-MM-dd")
        description = self.aporte_description_edit.text().strip()
        amount = self.aporte_amount_edit.value()
        if amount <= 0.0:
            return
        self.investment_controller.add_contribution(inv_idx, date_str, description, amount)
        self.aporte_description_edit.clear(); self.aporte_amount_edit.clear()
        self._refresh_investments()

    def _on_delete_aporte(self):
        inv_idx = self._investment_index_for_aporte()
        if inv_idx is None:
            return
        selected = self.contributions_table.selectionModel().selectedRows()
        if not selected:
            return
        indices = []
        for s in selected:
            row = s.row()
            if row < 0 or row >= len(self.contribution_row_to_index):
                continue
            indices.append(self.contribution_row_to_index[row])
        if indices:
            self.investment_controller.delete_contributions(inv_idx, indices)
            self._refresh_contributions_table()