import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': int(datetime.datetime.now().strftime('%Y'))
    }
