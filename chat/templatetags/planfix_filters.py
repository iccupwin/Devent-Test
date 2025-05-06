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