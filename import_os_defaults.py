#!/usr/bin/python3

import sqlite3
import json

db = sqlite3.connect('OS_defaults.db')
c = db.cursor()

# have to specify encoding, may need to handle this more elegantly for other OS'
with open('md.json', 'r', encoding='utf-16') as f:
    for line in f:
        record = json.loads(line)
        c.execute("INSERT OR IGNORE INTO Directory (path) VALUES(?)", 
                    (
                        record['ParentPath'],)
                    )
        c.execute("INSERT OR IGNORE INTO Item (name, base_name, extension) VALUES(?, ?, ?)", 
                    (
                        record['Name'],
                        record["BaseName"],
                        record['Extension'])
                    )

db.commit()
db.close()