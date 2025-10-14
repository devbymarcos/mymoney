# Mymoney

Aplicativo desktop em Python (PyQt5) para controle básico de despesas.
Agora também suporta receitas (incomes) com saldo consolidado.
Persistência migrada para SQLite (arquivo `data/mymoney.db`).

## Pré-requisitos
- Python 3.11+ (funciona com 3.13)
- Windows (PowerShell)

## Configuração

1. Criar ambiente virtual:
```
python -m venv .venv
```
2. Atualizar `pip` e instalar dependências:
```
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Ajustar variáveis no `.env` (opcional):
```
APP_NAME=Mymoney
DATA_DIR=data
```

## Executar
```
.venv\Scripts\python.exe -m app.main
```

## Estrutura
```
app/
  main.py
  config.py
  controllers/expense_controller.py
  controllers/revenue_controller.py
  models/expense.py
  models/revenue.py
  services/storage_service.py  (SQLite)
  services/revenue_storage_service.py  (SQLite)
  ui/main_window.py
  utils/formatting.py
.data/
  mymoney.db
.env
requirements.txt
README.md
```

- Dados são persistidos em SQLite: `data/mymoney.db`.
- Na primeira execução após a migração, dados existentes dos JSON (`data/expenses.json` e `data/revenues.json`) são importados automaticamente caso as tabelas estejam vazias.
- Categorias padrão: Alimentação, Transporte, Moradia, Lazer, Saúde, Outros.
 - Categorias de receitas: Salário, Freelance, Vendas, Investimentos, Outros.
 - A UI possui duas abas: Despesas e Receitas; o rodapé mostra saldo (Receitas - Despesas).