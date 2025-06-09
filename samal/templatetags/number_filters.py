from django import template

register = template.Library()

@register.filter
def dots_thousands(value):
    """
    Форматирует целое число, вставляя точку между каждыми тремя разрядами.
    Пример: 4000000 → '4.000.000'
    """
    try:
        num = int(value)
    except (ValueError, TypeError):
        return value
    # форматируем через запятую, а потом заменяем запятую на точку
    formatted = f"{num:,}".replace(",", ".")
    return formatted
