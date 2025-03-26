from datetime import datetime, timedelta


# список на следующие
def get_next_10_days() -> list[str]:
    today = datetime.today()
    return [
        (today + timedelta(days=i)).strftime('%d.%m.%Y')
        for i in range(10)
    ]