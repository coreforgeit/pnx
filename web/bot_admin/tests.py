import requests


def test_edit_book():
    url = "http://127.0.0.1:8000/api/v1/edit-book/"
    payload = {
        "spreadsheetId": "1RVcxIFP0K6U45gBwxSnBSvHAs0ORV0CvnU0jqKvufC4",
        "sheetId": 811514896,
        "sheetName": "29.04.2025",
        "rowNumber": 3,
        "name": "Анна",
        "time": "1899-12-30T15:00:49.000Z",
        "person": 1,
        "comment": "Убара",
        "status": "Подтверждена",
        "bookId": 12
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(response.status_code, response.json())
    else:
        print(response.status_code, response.text)


def test_add_ticket_row():
    url = "http://127.0.0.1:8000/api/v1/edit-ticket/"

    payload = {
        "spreadsheetId": "1RVcxIFP0K6U45gBwxSnBSvHAs0ORV0CvnU0jqKvufC4",
        "sheetId": 1711029444,
        "sheetName": "HHHH",
        "rowNumber": 54,
        "ticketId": 54,
        "option": "Стоя",
        "name": "2",
        "status": "Пришёл",
    }

    response = requests.post(url, json=payload)
    print(response.status_code)
    print(response.json())


if __name__ == '__main__':
    test_edit_book()
    test_add_ticket_row()
