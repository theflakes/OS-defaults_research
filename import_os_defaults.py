#!/usr/bin/python3

import sqlite3
import json

db = sqlite3.connect('OS_defaults.db')
c = db.cursor()

# have to specify encoding, may need to handle this more elegantly for other OS'
with open('md.json', 'r', encoding='utf-16') as f:
    for line in f:
        record = json.loads(line)
        c.execute("INSERT OR REPLACE INTO Directory (path) VALUES(?);", 
                    (
                        record['ParentPath'],
                    )
                )
        c.execute("INSERT OR REPLACE INTO Item (name, base_name, extension) VALUES(?, ?, ?);", 
                    (
                        record['Name'],
                        record["BaseName"],
                        record['Extension']
                    )
                )

        c.execute("SELECT id FROM OS WHERE version='10 Pro N'")
        o_id = c.fetchone()[0]
        c.execute("SELECT id FROM Directory WHERE path=?;", (record['ParentPath'],))
        d_id = c.fetchone()[0]
        c.execute("SELECT id FROM Item WHERE name=?;", (record['Name'],))
        i_id = c.fetchone()[0]
        c.execute("INSERT OR REPLACE INTO OS_Directory_Item (os_id, directory_id, item_id, mode, size, link_type) VALUES(?, ?, ?, ?, ?, ?);", 
                    (
                        o_id,
                        d_id,
                        i_id,
                        record['Mode'],
                        record['Size'],
                        record['LinkType']
                    )
                )

db.commit()
db.close()