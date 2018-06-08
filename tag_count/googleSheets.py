import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
class GoogleSheets(object):
	# use creds to create a client to interact with the Google Drive API
	scope = ['https://spreadsheets.google.com/feeds',
      	     'https://www.googleapis.com/auth/drive']

	creds = ServiceAccountCredentials.from_json_keyfile_name('/home/tom/Documents/instgramTagCount/client_secret.json', scope)
	client = gspread.authorize(creds)

	# Find a workbook by name and open the first sheet
	# Make sure you use the right name here.
	sheet = client.open("Instagram Data").sheet1

	# mock_data = [
	# 	['12343548', '', ''],
	# 	['', 'part8', '1'],
	# 	['', 'party7', '2'],
	# 	['', 'party6', '3'],
	# 	['', 'party5', '4'],
	# ]
	def append_data(self, data):
		values = self.sheet.get_all_values()
		self.sheet.add_rows(len(data))
		last_row = len(values) + 1
		for num, row in enumerate(data):
			index = last_row + num
			self.sheet.insert_row(row, index=index)
			time.sleep(5)
