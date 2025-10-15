from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QDateEdit, QTableWidget, QTableWidgetItem,
    QLabel, QHBoxLayout, QTabWidget, QHeaderView, QFrame
)
import os
from PyQt5.QtCore import QDate, Qt, QSize, QLocale
from PyQt5.QtGui import QIcon
from datetime import datetime, timedelta

from app.controllers.expense_controller import ExpenseController
from app.controllers.revenue_controller import RevenueController
from app.controllers.investment_controller import InvestmentController
from app.utils.formatting import format_currency_brl, format_date_brl
from app.config import ICONS_DIR
from app.services.category_service import CategoryService
from app.services.broker_service import BrokerService
from app.ui.tabs.investments_tab import InvestmentsTab
from app.ui.tabs.expenses_tab import ExpensesTab
from app.ui.tabs.revenues_tab import RevenuesTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mymoney - Controle de Despesas")
        self.expense_controller = ExpenseController()
        self.revenue_controller = RevenueController()
        self.investment_controller = InvestmentController()
        self.category_service = CategoryService()
        self.broker_service = BrokerService()
        self.expense_edit_index = None
        self.revenue_edit_index = None
        self.investment_edit_index = None
        self.current_investment_index = None
        self._setup_ui()
        # Locale pt-BR para calendários e datas
        self._apply_locale()
        self.setMinimumSize(1024, 700)
        self.resize(1280, 800)
        self._apply_theme()
        # Garantir que os combos de categoria sejam preenchidos na inicialização
        self._load_categories()
        self._refresh_tables()
        # Inicializa relatórios na carga
        if hasattr(self, '_refresh_reports'):
            self._refresh_reports()

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
        # Evita elipse/truncamento de texto nos títulos das abas
        self.tabs.setElideMode(Qt.ElideNone)
        # Evitar corte: desabilita expansão e usa botões de scroll
        try:
            tb = self.tabs.tabBar()
            tb.setExpanding(False)
            tb.setUsesScrollButtons(True)
        except Exception:
            pass
        layout.addWidget(self.tabs)

        # Aba Despesas (extraída para classe dedicada)
        self.expenses_tab = ExpensesTab(self.expense_controller, self.category_service, self._refresh_tables, getattr(self, '_refresh_reports', None))
        self.tabs.addTab(self.expenses_tab, "Despesas")
        self.tabs.setTabIcon(self.tabs.indexOf(self.expenses_tab), QIcon(os.path.join(ICONS_DIR, "expense.svg")))

        # Aba Receitas (extraída para classe dedicada)
        self.revenues_tab = RevenuesTab(self.revenue_controller, self.category_service, self._refresh_tables, getattr(self, '_refresh_reports', None))
        self.tabs.addTab(self.revenues_tab, "Receitas")
        self.tabs.setTabIcon(self.tabs.indexOf(self.revenues_tab), QIcon(os.path.join(ICONS_DIR, "revenue.svg")))

        # Aba Investimentos (extraída para classe dedicada)
        self.investments_tab = InvestmentsTab(self.investment_controller, self.broker_service)
        self.tabs.addTab(self.investments_tab, "Investimentos")
        # Ícone será adicionado ao assets; se não existir, usa report.svg como fallback
        inv_icon_path = os.path.join(ICONS_DIR, "investment.svg")
        self.tabs.setTabIcon(self.tabs.indexOf(self.investments_tab), QIcon(inv_icon_path if os.path.exists(inv_icon_path) else os.path.join(ICONS_DIR, "report.svg")))

        # Aba Relatórios
        reports_tab = QWidget()
        reports_layout = QVBoxLayout(); reports_tab.setLayout(reports_layout)
        self._build_reports_section(reports_layout)
        self.tabs.addTab(reports_tab, "Relatórios")
        self.tabs.setTabIcon(self.tabs.indexOf(reports_tab), QIcon(os.path.join(ICONS_DIR, "report.svg")))

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

    

    def _build_reports_section(self, parent_layout: QVBoxLayout):
        # Título da seção
        title = QLabel("Relatórios por categoria")
        title.setObjectName("cardTitle")
        parent_layout.addWidget(title)

        # Sub-abas dentro de Relatórios: Mensal e Anual
        reports_tabs = QTabWidget()
        reports_tabs.setElideMode(Qt.ElideNone)
        # Tamanho dos ícones das sub-abas
        reports_tabs.setIconSize(QSize(16, 16))

        monthly_tab = QWidget(); monthly_layout = QVBoxLayout(); monthly_tab.setLayout(monthly_layout)
        annual_tab = QWidget(); annual_layout = QVBoxLayout(); annual_tab.setLayout(annual_layout)

        # Relatório de despesas por categoria
        exp_label = QLabel("Despesas por categoria")
        monthly_layout.addWidget(exp_label)
        self.expense_report_table = QTableWidget(0, 3)
        self.expense_report_table.setHorizontalHeaderLabels(["Categoria", "Total (R$)", "Percentual"])
        self.expense_report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expense_report_table.setAlternatingRowColors(True)
        self.expense_report_table.setShowGrid(False)
        monthly_layout.addWidget(self.expense_report_table)

        # Relatório de receitas por categoria
        rev_label = QLabel("Receitas por categoria")
        monthly_layout.addWidget(rev_label)
        self.revenue_report_table = QTableWidget(0, 3)
        self.revenue_report_table.setHorizontalHeaderLabels(["Categoria", "Total (R$)", "Percentual"])
        self.revenue_report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.revenue_report_table.setAlternatingRowColors(True)
        self.revenue_report_table.setShowGrid(False)
        monthly_layout.addWidget(self.revenue_report_table)

        # Adiciona aba Mensal com ícone
        reports_tabs.addTab(monthly_tab, "Mensal")
        reports_tabs.setTabIcon(reports_tabs.indexOf(monthly_tab), QIcon(os.path.join(ICONS_DIR, "monthly.svg")))

        # Seção: Relatório anual por categoria
        annual_title = QLabel("Relatório anual por categoria (usa ano do filtro)")
        annual_title.setObjectName("cardTitle")
        annual_layout.addWidget(annual_title)

        # Despesas por mês no ano
        exp_year_label = QLabel("Despesas por mês (ano)")
        annual_layout.addWidget(exp_year_label)
        self.expense_annual_table = QTableWidget(0, 13)
        self.expense_annual_table.setHorizontalHeaderLabels([
            "Categoria", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"
        ])
        self.expense_annual_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expense_annual_table.setAlternatingRowColors(True)
        self.expense_annual_table.setShowGrid(False)
        annual_layout.addWidget(self.expense_annual_table)

        # Receitas por mês no ano
        rev_year_label = QLabel("Receitas por mês (ano)")
        annual_layout.addWidget(rev_year_label)
        self.revenue_annual_table = QTableWidget(0, 13)
        self.revenue_annual_table.setHorizontalHeaderLabels([
            "Categoria", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"
        ])
        self.revenue_annual_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.revenue_annual_table.setAlternatingRowColors(True)
        self.revenue_annual_table.setShowGrid(False)
        annual_layout.addWidget(self.revenue_annual_table)

        # Adiciona aba Anual com ícone e insere as sub-abas no layout principal
        reports_tabs.addTab(annual_tab, "Anual")
        reports_tabs.setTabIcon(reports_tabs.indexOf(annual_tab), QIcon(os.path.join(ICONS_DIR, "annual.svg")))
        parent_layout.addWidget(reports_tabs)

    

    def _load_categories(self):
        # Delegar recarga de categorias às abas dedicadas
        if hasattr(self, 'expenses_tab'):
            try:
                self.expenses_tab.reload_categories()
            except Exception:
                pass
        if hasattr(self, 'revenues_tab'):
            try:
                self.revenues_tab.reload_categories()
            except Exception:
                pass

    
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
        # Filtrar por mês selecionado e mapear linha→índice real
        expense_row_to_index = []
        expenses_month = []
        for idx, item in enumerate(expenses):
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt.year == sel_year and dt.month == sel_month:
                    expenses_month.append(item)
                    expense_row_to_index.append(idx)
            except Exception:
                continue
        if hasattr(self, 'expenses_tab'):
            self.expenses_tab.expense_row_to_index = expense_row_to_index
            table = self.expenses_tab.expense_table
            total_label = self.expenses_tab.expense_total_label
        else:
            self.expense_row_to_index = expense_row_to_index
            table = self.expense_table
            total_label = self.expense_total_label
        table.setRowCount(0)
        for item in expenses_month:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(format_date_brl(item.get("date", ""))))
            table.setItem(row, 1, QTableWidgetItem(item.get("category", "")))
            table.setItem(row, 2, QTableWidgetItem(item.get("description", "")))
            amount_item = QTableWidgetItem(format_currency_brl(item.get("amount", 0.0)))
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 3, amount_item)

        expense_month_total = sum(float(i.get("amount", 0.0)) for i in expenses_month)
        total_label.setText(f"Total do mês: {format_currency_brl(expense_month_total)}")

        # Receitas
        revenues = self.revenue_controller.list_revenues()
        # Filtrar por mês selecionado e mapear linha→índice real
        self.revenue_row_to_index = []
        revenues_month = []
        for idx, item in enumerate(revenues):
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt.year == sel_year and dt.month == sel_month:
                    revenues_month.append(item)
                    self.revenue_row_to_index.append(idx)
            except Exception:
                continue
        if hasattr(self, 'revenues_tab'):
            self.revenues_tab.revenue_row_to_index = self.revenue_row_to_index
            rtable = self.revenues_tab.revenue_table
            rtotal_label = self.revenues_tab.revenue_total_label
        else:
            rtable = self.revenue_table
            rtotal_label = self.revenue_total_label
        rtable.setRowCount(0)
        for item in revenues_month:
            row = rtable.rowCount()
            rtable.insertRow(row)
            rtable.setItem(row, 0, QTableWidgetItem(format_date_brl(item.get("date", ""))))
            rtable.setItem(row, 1, QTableWidgetItem(item.get("category", "")))
            rtable.setItem(row, 2, QTableWidgetItem(item.get("description", "")))
            amount_item = QTableWidgetItem(format_currency_brl(item.get("amount", 0.0)))
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            rtable.setItem(row, 3, amount_item)

        revenue_month_total = sum(float(i.get("amount", 0.0)) for i in revenues_month)
        rtotal_label.setText(f"Total do mês: {format_currency_brl(revenue_month_total)}")

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

    def _refresh_reports(self):
        # Mês selecionado
        sel_qdate = self.month_filter.date()
        sel_year = sel_qdate.year()
        sel_month = sel_qdate.month()

        # Agregação de despesas por categoria
        exp_sums = {}
        for item in self.expense_controller.list_expenses():
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt.year == sel_year and dt.month == sel_month:
                    cat = (item.get("category", "") or "").strip() or "(Sem categoria)"
                    exp_sums[cat] = exp_sums.get(cat, 0.0) + float(item.get("amount", 0.0))
            except Exception:
                continue
        # Preencher tabela de despesas
        self.expense_report_table.setRowCount(0)
        exp_total_month = sum(exp_sums.values()) if exp_sums else 0.0
        for cat in sorted(exp_sums.keys()):
            row = self.expense_report_table.rowCount()
            self.expense_report_table.insertRow(row)
            self.expense_report_table.setItem(row, 0, QTableWidgetItem(cat))
            amt_item = QTableWidgetItem(format_currency_brl(exp_sums[cat]))
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.expense_report_table.setItem(row, 1, amt_item)
            # Percentual da categoria em relação ao total do mês
            pct = (exp_sums[cat] / exp_total_month * 100.0) if exp_total_month > 0 else 0.0
            pct_str = f"{pct:.1f}%".replace('.', ',')
            pct_item = QTableWidgetItem(pct_str)
            pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.expense_report_table.setItem(row, 2, pct_item)

        # Agregação de receitas por categoria
        rev_sums = {}
        for item in self.revenue_controller.list_revenues():
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt.year == sel_year and dt.month == sel_month:
                    cat = (item.get("category", "") or "").strip() or "(Sem categoria)"
                    rev_sums[cat] = rev_sums.get(cat, 0.0) + float(item.get("amount", 0.0))
            except Exception:
                continue
        # Preencher tabela de receitas
        self.revenue_report_table.setRowCount(0)
        rev_total_month = sum(rev_sums.values()) if rev_sums else 0.0
        for cat in sorted(rev_sums.keys()):
            row = self.revenue_report_table.rowCount()
            self.revenue_report_table.insertRow(row)
            self.revenue_report_table.setItem(row, 0, QTableWidgetItem(cat))
            amt_item = QTableWidgetItem(format_currency_brl(rev_sums[cat]))
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.revenue_report_table.setItem(row, 1, amt_item)
            # Percentual da categoria em relação ao total do mês
            pct = (rev_sums[cat] / rev_total_month * 100.0) if rev_total_month > 0 else 0.0
            pct_str = f"{pct:.1f}%".replace('.', ',')
            pct_item = QTableWidgetItem(pct_str)
            pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.revenue_report_table.setItem(row, 2, pct_item)

        # Relatório anual: despesas por mês e categoria
        exp_year_sums = {}
        for item in self.expense_controller.list_expenses():
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt.year == sel_year:
                    cat = (item.get("category", "") or "").strip() or "(Sem categoria)"
                    arr = exp_year_sums.get(cat)
                    if arr is None:
                        arr = [0.0] * 12
                        exp_year_sums[cat] = arr
                    arr[dt.month - 1] += float(item.get("amount", 0.0))
            except Exception:
                continue
        self.expense_annual_table.setRowCount(0)
        for cat in sorted(exp_year_sums.keys()):
            row = self.expense_annual_table.rowCount()
            self.expense_annual_table.insertRow(row)
            self.expense_annual_table.setItem(row, 0, QTableWidgetItem(cat))
            for m in range(12):
                amt_item = QTableWidgetItem(format_currency_brl(exp_year_sums[cat][m]))
                amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.expense_annual_table.setItem(row, 1 + m, amt_item)

        # Relatório anual: receitas por mês e categoria
        rev_year_sums = {}
        for item in self.revenue_controller.list_revenues():
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt.year == sel_year:
                    cat = (item.get("category", "") or "").strip() or "(Sem categoria)"
                    arr = rev_year_sums.get(cat)
                    if arr is None:
                        arr = [0.0] * 12
                        rev_year_sums[cat] = arr
                    arr[dt.month - 1] += float(item.get("amount", 0.0))
            except Exception:
                continue
        self.revenue_annual_table.setRowCount(0)
        for cat in sorted(rev_year_sums.keys()):
            row = self.revenue_annual_table.rowCount()
            self.revenue_annual_table.insertRow(row)
            self.revenue_annual_table.setItem(row, 0, QTableWidgetItem(cat))
            for m in range(12):
                amt_item = QTableWidgetItem(format_currency_brl(rev_year_sums[cat][m]))
                amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.revenue_annual_table.setItem(row, 1 + m, amt_item)

    def _on_month_changed(self, *_):
        self._refresh_tables()
        if hasattr(self, '_refresh_reports'):
            self._refresh_reports()

    def _apply_theme(self):
        # Tema leve com acentos modernos
        self.setStyleSheet(
            """
            QMainWindow { background: #f8fafc; }
            QLabel { font-size: 12px; }
            QTabWidget::pane { border: 1px solid #e5e7eb; border-radius: 8px; padding: 4px; }
            /* Mantém padding e borda consistente para evitar corte do primeiro caractere */
            QTabBar::tab { background: #e5e7eb; color: #334155; padding: 10px 16px; padding-left: 18px; padding-right: 18px; min-width: 130px; border-radius: 6px; margin: 2px; border: 2px solid transparent; }
            QTabBar::tab:hover { background: #f1f5f9; color: #1f2937; }
            QTabBar::tab:selected { background: #1d4ed8; color: #ffffff; font-weight: 700; padding: 10px 16px; padding-left: 18px; padding-right: 18px; min-width: 130px; border: 2px solid #1d4ed8; }
            QHeaderView::section { background: #eef2ff; padding: 6px; border: none; font-weight: 600; }
            QTableWidget { alternate-background-color: #ffffff; background: #f8fafc; }
            QTableWidget::item:selected { background: #bfdbfe; color: #111827; }
            QTableWidget::item:hover { background: #e0f2fe; }
            QPushButton { background: #60a5fa; color: white; border: none; padding: 8px 12px; border-radius: 6px; }
            QPushButton:hover { background: #3b82f6; }
            QPushButton:pressed { background: #2563eb; }
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

    def _apply_locale(self):
        # Define locale padrão da aplicação para pt-BR
        br = QLocale(QLocale.Portuguese, QLocale.Brazil)
        QLocale.setDefault(br)
        # Aplica locale aos QDateEdit existentes
        if hasattr(self, 'month_filter') and isinstance(self.month_filter, QDateEdit):
            self.month_filter.setLocale(br)
            # Mantém formato MM/yyyy para filtro de mês
            self.month_filter.setDisplayFormat("MM/yyyy")
            try:
                self.month_filter.calendarWidget().setFirstDayOfWeek(Qt.Monday)
            except Exception:
                pass
        # Delegar locale da aba de despesas para a classe dedicada
        if hasattr(self, 'expenses_tab'):
            try:
                self.expenses_tab.apply_locale(br)
            except Exception:
                pass
        # Delegar locale da aba de receitas para a classe dedicada
        if hasattr(self, 'revenues_tab'):
            try:
                self.revenues_tab.apply_locale(br)
            except Exception:
                pass
        # Delegar locale da aba de investimentos para a classe dedicada
        if hasattr(self, 'investments_tab'):
            try:
                self.investments_tab.apply_locale(br)
            except Exception:
                pass
        # Investimentos: locale agora é aplicado pela InvestmentsTab