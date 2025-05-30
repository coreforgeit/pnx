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


def test_payment():
    url = 'http://127.0.0.1:8000/api/v1/payment/'
    payload = {
          "store_id": 6,
          "amount": 10000000,
          "invoice_id": "c36ee3551ff84357",
          "invoice_uuid": "e3f5b4db-266d-11f0-b159-005056b4367d",
          "billing_id": None,
          "payment_time": "2025-05-01 14:24:43",
          "phone": "998930601725",
          "card_pan": "860030******5959",
          "card_token": "6225f3c93f7a880142782fa4",
          "ps": "uzcard",
          "uuid": "e3f5b4db-266d-11f0-b159-005056b4367d",
          "receipt_url": "https://dev-checkout.multicard.uz/check/e3f5b4db-266d-11f0-b159-005056b4367d",
          "sign": "b69995f4c1651aa96baf48d01e4b4d3d"
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print("Response:", response.json())
    else:
        print("Response:", response.status_code, response.text)


if __name__ == '__main__':
    # test_edit_book()
    # test_add_ticket_row()
    test_payment()
