from django import template

register = template.Library()

@register.filter
def modulo(value, arg):
    """
    Возвращает остаток от деления value на arg
    """
    try:
        return int(value) % int(arg)
    except (ValueError, TypeError):
        return 0
        
@register.filter
def index(list_data, index):
    """
    Возвращает элемент списка по индексу
    """
    try:
        return list_data[int(index)]
    except (IndexError, ValueError, TypeError):
        return ''

@register.filter
def ord(value):
    """
    Возвращает Unicode-код первого символа строки
    """
    try:
        return ord(str(value)[0])
    except Exception:
        return 0