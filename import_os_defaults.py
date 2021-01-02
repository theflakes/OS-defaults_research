#!/usr/bin/python3

import sqlite3
import json

sqlite3.connect('OS_defaults.db')

# have to specify encoding, may need to handle this more elegantly for other OS'
with open("md.json", 'r', encoding='utf-16') as f:
    for line in f:
        record = json.loads(line)
        

