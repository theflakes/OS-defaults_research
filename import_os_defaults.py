#!/usr/bin/python3

import sqlite3
import json


def get_os_directory_item_ids(c, os, path, name):
    c.execute("SELECT id FROM OS WHERE version=?", (os,))
    o_id = c.fetchone()[0]
    c.execute("SELECT id FROM Directory WHERE path=?;", (path,))
    d_id = c.fetchone()[0]
    c.execute("SELECT id FROM Item WHERE name=?;", (name,))
    i_id = c.fetchone()[0]
    return o_id, d_id, i_id


def get_os_directory_item_id(c, o_id, d_id, i_id):
    c.execute("SELECT id FROM OS_Directory_Item WHERE os_id=? AND directory_id=? AND item_id=?;", 
                    (
                        o_id, 
                        d_id, 
                        i_id
                    )
                )
    odi_id = c.fetchone()[0]
    return odi_id


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

        o_id, d_id, i_id = get_os_directory_item_ids(c, '10 Pro N', record['ParentPath'], record['Name'])
        c.execute("INSERT OR REPLACE INTO OS_Directory_Item (os_id, directory_id, item_id, mode, size, link_type, hidden) VALUES(?, ?, ?, ?, ?, ?, ?);", 
                    (
                        o_id,
                        d_id,
                        i_id,
                        record['Mode'],
                        record['Size'],
                        record['LinkType'],
                        record['Hidden']
                    )
                )

        for stream in record['Streams']:
            c.execute("INSERT OR REPLACE INTO ADS (name) VALUES(?);", 
                    (
                        stream['Name'],
                    )
                )
            c.execute("SELECT id FROM OS_Directory_Item WHERE os_id=? AND directory_id=? AND item_id=i_id;", 
                        (
                            o_id, 
                            d_id, 
                            i_id
                        )
                    )
            odi_id = c.fetchone()[0]
            c.execute("SELECT id FROM ADS WHERE name=?;", (record['Name'],))
            a_id = c.fetchone()[0]
            c.execute("INSERT OR REPLACE INTO Item_ADS (os_directory_item_id, ads_id, size) VALUES(?, ?, ?);", 
                        (
                            odi_id,
                            a_id,
                            stream['Size']
                        )
                    )

    db.commit()

    # We need to loop through it all again to add Link info
    for line in f:    
        record = json.loads(line)
        if record['LinkType']:
            for link in record['LinkType']:
                # Get the Link's IDs
                o_id, d_id, i_id = get_os_directory_item_ids(c, '10 Pro N', record['ParentPath'], record['Name'])
                link_id = get_os_directory_item_id(o_id, d_id, i_id)

                # Get the Link's target IDs
                path_item = link.rsplit('\\', 1)
                o_id, d_id, i_id = get_os_directory_item_ids(c, '10 Pro N', path_item[0], path_item[1])
                target_id = get_os_directory_item_id(o_id, d_id, i_id)

                c.execute("INSERT OR REPLACE INTO Item_ADS (link_id, target_id) VALUES(?, ?);", 
                        (
                            link_id,
                            target_id
                        )
                    )

db.commit()
db.close()