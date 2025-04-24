import requests


def test_edit_book():
    url = "http://127.0.0.1:8000/api/v1/edit-book/"
    payload = {
        "spreadsheet_id": "1RVcxIFP0K6U45gBwxSnBSvHAs0ORV0CvnU0jqKvufC4",
        "sheet_id": 811514896,
        "sheet_name": "29.04.2025",
        "row_number": 3,
        "data": {
            "name": "Анна",
            "time": "1899-12-30T15:00:49.000Z",
            "person": 1,
            "comment": "Убара",
            "status": "Подтверждена"
        }
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(response.status_code, response.json())
    else:
        print(response.status_code, response.text)


if __name__ == '__main__':
    test_edit_book()
