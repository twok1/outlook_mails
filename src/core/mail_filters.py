from exchangelib import Q


def get_trip_query() -> Q:
    """
    Запрос для фильтрации писем о командировке
    """
    return Q(
        Q(sender='iasup_notify@greenatom.ru') &
        (
            Q(subject__contains='Информирование о направлении в командировку') |
            Q(subject__contains='Информирование об изменении данных командировки')
        )
    )
