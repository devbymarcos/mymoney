from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QHBoxLayout, QTabWidget, QHeaderView, QFrame, QInputDialog, QMessageBox
)
import os
from PyQt5.QtCore import QDate, Qt, QSize, QLocale
from PyQt5.QtGui import QIcon
from datetime import datetime, timedelta

from app.controllers.expense_controller import ExpenseController
from app.controllers.revenue_controller import RevenueController
from app.controllers.investment_controller import InvestmentController
from app.utils.formatting import format_currency_brl, format_date_brl
from app.ui.widgets.money_line_edit import MoneyLineEdit
from app.config import ICONS_DIR
from app.services.category_service import CategoryService
from app.services.broker_service import BrokerService


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

        # Aba Investimentos
        investments_tab = QWidget()
        investments_layout = QVBoxLayout(); investments_tab.setLayout(investments_layout)
        self._build_investments_section(investments_layout)
        self.tabs.addTab(investments_tab, "Investimentos")
        # Ícone será adicionado ao assets; se não existir, usa report.svg como fallback
        inv_icon_path = os.path.join(ICONS_DIR, "investment.svg")
        self.tabs.setTabIcon(2, QIcon(inv_icon_path if os.path.exists(inv_icon_path) else os.path.join(ICONS_DIR, "report.svg")))

        # Aba Relatórios
        reports_tab = QWidget()
        reports_layout = QVBoxLayout(); reports_tab.setLayout(reports_layout)
        self._build_reports_section(reports_layout)
        self.tabs.addTab(reports_tab, "Relatórios")
        self.tabs.setTabIcon(3, QIcon(os.path.join(ICONS_DIR, "report.svg")))

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
        self.expense_date_edit = QDateEdit(); self.expense_date_edit.setCalendarPopup(True); self.expense_date_edit.setDisplayFormat("dd/MM/yyyy"); self.expense_date_edit.setDate(QDate.currentDate())
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
        self.expense_add_btn = QPushButton("Adicionar despesa"); self.expense_add_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); self.expense_add_btn.clicked.connect(self._on_add_expense)
        self.expense_delete_btn = QPushButton("Excluir selecionado(s)"); self.expense_delete_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "trash.svg"))); self.expense_delete_btn.setProperty('variant', 'secondary'); self.expense_delete_btn.clicked.connect(self._on_delete_expense)
        edit_btn = QPushButton("Editar selecionado"); edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg"))); edit_btn.setProperty('variant', 'secondary'); edit_btn.clicked.connect(self._on_edit_expense_prepare)
        self.expense_save_edit_btn = QPushButton("Salvar edição"); self.expense_save_edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "save.svg"))); self.expense_save_edit_btn.setProperty('variant', 'secondary'); self.expense_save_edit_btn.setEnabled(False); self.expense_save_edit_btn.clicked.connect(self._on_save_expense_edit)
        btn_layout.addWidget(self.expense_add_btn)
        btn_layout.addWidget(self.expense_delete_btn)
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
        self.revenue_date_edit = QDateEdit(); self.revenue_date_edit.setCalendarPopup(True); self.revenue_date_edit.setDisplayFormat("dd/MM/yyyy"); self.revenue_date_edit.setDate(QDate.currentDate())
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
        self.revenue_add_btn = QPushButton("Adicionar receita"); self.revenue_add_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "plus.svg"))); self.revenue_add_btn.clicked.connect(self._on_add_revenue)
        self.revenue_delete_btn = QPushButton("Excluir selecionado(s)"); self.revenue_delete_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "trash.svg"))); self.revenue_delete_btn.setProperty('variant', 'secondary'); self.revenue_delete_btn.clicked.connect(self._on_delete_revenue)
        edit_btn = QPushButton("Editar selecionado"); edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "edit.svg"))); edit_btn.setProperty('variant', 'secondary'); edit_btn.clicked.connect(self._on_edit_revenue_prepare)
        self.revenue_save_edit_btn = QPushButton("Salvar edição"); self.revenue_save_edit_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "save.svg"))); self.revenue_save_edit_btn.setProperty('variant', 'secondary'); self.revenue_save_edit_btn.setEnabled(False); self.revenue_save_edit_btn.clicked.connect(self._on_save_revenue_edit)
        btn_layout.addWidget(self.revenue_add_btn)
        btn_layout.addWidget(self.revenue_delete_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(self.revenue_save_edit_btn)
        parent_layout.addLayout(btn_layout)

        # Tabela de receitas
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

    def _build_investments_section(self, parent_layout: QVBoxLayout):
        # Sub-abas: Investimento e Aportes
        investments_tabs = QTabWidget()
        investments_tabs.setElideMode(Qt.ElideNone)
        investments_tabs.setIconSize(QSize(16, 16))
        # Expandir sub-abas para evitar corte do texto
        try:
            investments_tabs.tabBar().setExpanding(True)
        except Exception:
            pass
        # Estilo mais suave para aba selecionada e padding adequado para não cortar texto
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
        # Corretora: combo + botões de cadastro/gerenciamento
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
        parent_layout.addWidget(investments_tabs)

        # Carregar corretoras e investimentos
        self._load_brokers()
        self._refresh_investments()

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
        # Atualiza relatórios após inserção
        if hasattr(self, '_refresh_reports'):
            self._refresh_reports()

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
        # Atualiza relatórios após inserção
        if hasattr(self, '_refresh_reports'):
            self._refresh_reports()

    def _on_delete_expense(self):
        selected = self.expense_table.selectionModel().selectedRows()
        if not selected:
            return
        rows = sorted([idx.row() for idx in selected], reverse=True)
        if not hasattr(self, 'expense_row_to_index'):
            return
        indices = []
        for r in rows:
            if 0 <= r < len(self.expense_row_to_index):
                indices.append(self.expense_row_to_index[r])
        self.expense_controller.delete_expenses(indices)
        self._refresh_tables()
        if hasattr(self, '_refresh_reports'):
            self._refresh_reports()

    def _on_edit_expense_prepare(self):
        selected = self.expense_table.selectionModel().selectedRows()
        if len(selected) != 1:
            return
        row = selected[0].row()
        # Mapeia a linha visível para o índice real no armazenamento
        if not hasattr(self, 'expense_row_to_index') or row < 0 or row >= len(self.expense_row_to_index):
            return
        full_idx = self.expense_row_to_index[row]
        items = self.expense_controller.list_expenses()
        if full_idx < 0 or full_idx >= len(items):
            return
        item = items[full_idx]
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
        self.expense_edit_index = full_idx
        self.expense_save_edit_btn.setEnabled(True)
        # Desativa ações de adicionar e excluir enquanto edita
        if hasattr(self, 'expense_add_btn'):
            self.expense_add_btn.setEnabled(False)
        if hasattr(self, 'expense_delete_btn'):
            self.expense_delete_btn.setEnabled(False)

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
        # Reativa ações de adicionar e excluir
        if hasattr(self, 'expense_add_btn'):
            self.expense_add_btn.setEnabled(True)
        if hasattr(self, 'expense_delete_btn'):
            self.expense_delete_btn.setEnabled(True)
        self.expense_description_edit.clear()
        self.expense_amount_edit.clear()
        self._refresh_tables()
        if hasattr(self, '_refresh_reports'):
            self._refresh_reports()

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
        self._refresh_tables()
        if hasattr(self, '_refresh_reports'):
            self._refresh_reports()

    def _on_edit_revenue_prepare(self):
        selected = self.revenue_table.selectionModel().selectedRows()
        if len(selected) != 1:
            return
        row = selected[0].row()
        # Mapeia a linha visível para o índice real no armazenamento
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
        self._ensure_category_in_combo(item.get("category", ""), 'revenue')
        self.revenue_category_box.setCurrentText(item.get("category", ""))
        self.revenue_description_edit.setText(item.get("description", ""))
        amount = float(item.get("amount", 0.0))
        self.revenue_amount_edit.setText(format_currency_brl(amount).replace("R$ ", ""))
        self.revenue_edit_index = full_idx
        self.revenue_save_edit_btn.setEnabled(True)
        # Desativa ações de adicionar e excluir enquanto edita
        if hasattr(self, 'revenue_add_btn'):
            self.revenue_add_btn.setEnabled(False)
        if hasattr(self, 'revenue_delete_btn'):
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
        # Reativa ações de adicionar e excluir
        if hasattr(self, 'revenue_add_btn'):
            self.revenue_add_btn.setEnabled(True)
        if hasattr(self, 'revenue_delete_btn'):
            self.revenue_delete_btn.setEnabled(True)
        self.revenue_description_edit.clear()
        self.revenue_amount_edit.clear()
        self._refresh_tables()
        self._load_categories()
        if hasattr(self, '_refresh_reports'):
            self._refresh_reports()

    # ---------- Investimentos ----------
    def _load_brokers(self):
        brokers = self.broker_service.list_all()
        self.investment_broker_box.clear(); self.investment_broker_box.addItems(brokers)
        self.aporte_investment_box.clear()
        # Also refresh aportes combo with investment names
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
            # Excluir com reatribuição
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
            # Aportes e total
            contrib_sum = self.investment_controller.contributions_sum(idx)
            contrib_item = QTableWidgetItem(format_currency_brl(contrib_sum))
            contrib_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.investment_table.setItem(row, 4, contrib_item)
            total_item = QTableWidgetItem(format_currency_brl(float(item.get("initial_amount", 0.0)) + contrib_sum))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.investment_table.setItem(row, 5, total_item)
        # Total investido geral
        total = self.investment_controller.total_invested()
        self.investment_total_label.setText(f"Total investido: {format_currency_brl(total)}")
        # Atualiza combo de aportes
        self._load_brokers()
        # Atualiza tabela de aportes para o investimento selecionado
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
        # Garante corretora no combo
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
                # Atualiza combo de aportes para refletir seleção
                items = self.investment_controller.list_investments()
                if 0 <= self.current_investment_index < len(items):
                    label = f"{items[self.current_investment_index].get('name','')} ({items[self.current_investment_index].get('broker','')})"
                    idx = self.aporte_investment_box.findText(label)
                    if idx >= 0:
                        self.aporte_investment_box.setCurrentIndex(idx)
        self._refresh_contributions_table()

    def _investment_index_for_aporte(self) -> int | None:
        # Mapeia seleção do combo de aportes para índice de investimento
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
            self._refresh_investments()

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
        if hasattr(self, '_refresh_reports'):
            self._refresh_reports()
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
        self.expense_row_to_index = []
        expenses_month = []
        for idx, item in enumerate(expenses):
            try:
                dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if dt.year == sel_year and dt.month == sel_month:
                    expenses_month.append(item)
                    self.expense_row_to_index.append(idx)
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
        if hasattr(self, 'expense_date_edit') and isinstance(self.expense_date_edit, QDateEdit):
            self.expense_date_edit.setLocale(br)
            self.expense_date_edit.setDisplayFormat("dd/MM/yyyy")
            try:
                self.expense_date_edit.calendarWidget().setFirstDayOfWeek(Qt.Monday)
            except Exception:
                pass
        if hasattr(self, 'revenue_date_edit') and isinstance(self.revenue_date_edit, QDateEdit):
            self.revenue_date_edit.setLocale(br)
            self.revenue_date_edit.setDisplayFormat("dd/MM/yyyy")
            try:
                self.revenue_date_edit.calendarWidget().setFirstDayOfWeek(Qt.Monday)
            except Exception:
                pass
        # Investimentos
        if hasattr(self, 'investment_start_date_edit') and isinstance(self.investment_start_date_edit, QDateEdit):
            self.investment_start_date_edit.setLocale(br)
            self.investment_start_date_edit.setDisplayFormat("dd/MM/yyyy")
            try:
                self.investment_start_date_edit.calendarWidget().setFirstDayOfWeek(Qt.Monday)
            except Exception:
                pass
        if hasattr(self, 'aporte_date_edit') and isinstance(self.aporte_date_edit, QDateEdit):
            self.aporte_date_edit.setLocale(br)
            self.aporte_date_edit.setDisplayFormat("dd/MM/yyyy")
            try:
                self.aporte_date_edit.calendarWidget().setFirstDayOfWeek(Qt.Monday)
            except Exception:
                pass