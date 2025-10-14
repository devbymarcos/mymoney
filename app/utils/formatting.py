from datetime import datetime


def format_currency_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_date_brl(date_str: str) -> str:
    """Converte 'YYYY-MM-DD' para 'DD/MM/YYYY'. Mantém original em caso de erro."""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return date_str