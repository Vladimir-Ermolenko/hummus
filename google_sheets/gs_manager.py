import gspread
from oauth2client.service_account import ServiceAccountCredentials


class GoogleSheetsManager:
    def __init__(self, credentials_path, spreadsheet_id, sheet_name):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.scope = ['https://www.googleapis.com/auth/spreadsheets']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.credentials_path, self.scope)
        self.client = gspread.authorize(self.creds)
        self.worksheet = self.client.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)

    def save_data(self, data):
        self.worksheet.append_row(data)

    def query_data(self, query):
        result = self.worksheet.get_all_values()
        header = result[0]
        records = result[1:]
        index = header.index(query[0])
        return [record for record in records if record[index] == query[1]]

    def get_data_by_id(self, id_value, id_column):
        filtered_data = []
        data = self.worksheet.get_all_values()
        headers = data[0]
        index = headers.index(id_column)

        for row in data[1:]:
            # print(row[index], id_value)
            if int(row[index]) == id_value:
                filtered_data.append(row)

        return filtered_data

    def is_duplicate(self, timestamp, timestamp_column):
        sheet = self.client.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)
        column = sheet.col_values(sheet.find(timestamp_column).col)

        return timestamp in column


if __name__ == '__main__':
    gs = GoogleSheetsManager('1nz00ZhBI9R4hmPDETIePvYkBs55LZsmiFyodP70Ne1w',
                             '/Users/voverm/PycharmProjects/ai_sales/resources/creds.json',
                             'Sheet1')
    gs.save_data([['1', 2342342, 'Hummus']])
    print(gs.query_data('Sheet1!A2:C2'))
