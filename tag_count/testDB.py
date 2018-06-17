
import requests
import re
import json
import copy
import datetime
import calendar
import sqlite3
import copy
from collections import OrderedDict

conn = sqlite3.connect('instagram.db')


found_parties = []
print('DUMPING TAG_REF TABLE')
for row in conn.execute("SELECT * FROM tag_refs"):
    print("here")
    temp = row[2]+row[3]
    if temp in found_parties:
        print(temp)
    else:
        found_parties.append(temp)
