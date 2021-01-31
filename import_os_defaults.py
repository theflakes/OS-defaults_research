#!/usr/bin/python3

import sqlite3
import json


def get_os_directory_item_hash_ids(c, os, path, name, sha256):
    c.execute("SELECT id FROM OS WHERE version=?", (os,))
    o_id = c.fetchone()[0]
    c.execute("SELECT id FROM Directory WHERE path=?;", (path,))
    d_id = c.fetchone()[0]
    c.execute("SELECT id FROM Item WHERE name=?;", (name,))
    i_id = c.fetchone()[0]
    c.execute("SELECT id FROM Hash WHERE sha256=?;", (sha256,))
    h_id = c.fetchone()[0]
    return o_id, d_id, i_id, h_id


def get_os_directory_item_hash_id(c, o_id, d_id, i_id, h_id):
    c.execute("SELECT id FROM OS_Directory_Item_Hash WHERE os_id=? AND directory_id=? AND item_id=? AND hash_id=?;", 
                    (
                        o_id, 
                        d_id, 
                        i_id,
                        h_id
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
        c.execute("INSERT OR REPLACE INTO Hash (md5, sha1, sha256) VALUES(?, ?, ?);", 
                    (
                        record['md5'],
                        record["sha1"],
                        record['sha256']
                    )
                )

        o_id, d_id, i_id, h_id = get_os_directory_item_hash_ids(c, record['OS'], record['ParentPath'], record['Name'], record['sha256'])
        c.execute("INSERT OR REPLACE INTO OS_Directory_Item_Hash (" +
                        "os_id,"                    +
                        "directory_id,"             +
                        "item_id,"                  +
                        "hash_id,"                  +
                        "mode,"                     +
                        "size,"                     +
                        "is_link,"                  +
                        "is_hidden,"                +
                        "comments,"                 +
                        "company_name,"             +
                        "file_build_part,"          +
                        "file_description,"         +
                        "file_major_part,"          +
                        "file_minor_part,"          +
                        "filename,"                 +
                        "file_private_part,"        +
                        "file_version,"             +
                        "internal_name,"            +
                        "is_debug,"                 +
                        "is_patched,"               +
                        "is_private_build,"         +
                        "is_prerelease,"            +
                        "is_special_build,"         +
                        "language,"                 +
                        "legal_copyright,"          +
                        "legal_trademarks,"         +
                        "original_filename,"        +
                        "private_build,"            +
                        "product_build_part,"       +
                        "product_major_part,"       +
                        "product_minor_part,"       +
                        "product_name,"             +
                        "product_private_part,"     +
                        "product_version,"          +
                    "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", 
                    (
                        o_id,
                        d_id,
                        i_id,
                        h_id,
                        record["Mode,"],
                        record["Size,"],
                        record["Link,"],
                        record["Hidden,"],
                        record["Comments,"],
                        record["CompanyName,"],
                        record["FileBuildPart,"],
                        record["FileDescription,"],
                        record["FileMajorPart,"],
                        record["FileMinorPart,"],
                        record["FileName,"],
                        record["FilePrivatePart,"],
                        record["FileVersion,"],
                        record["InternalName,"],
                        record["IsDebug,"],
                        record["IsPatched,"],
                        record["IsPrivateBuild,"],
                        record["IsPreRelease,"],
                        record["IsSpecialBuild,"],
                        record["Language,"],
                        record["LegalCopyright,"],
                        record["LegalTrademarks,"],
                        record["OriginalFilename,"],
                        record["PrivateBuild,"],
                        record["ProductBuildPart,"],
                        record["ProductMajorPart,"],
                        record["ProductMinorPart,"],
                        record["ProductName,"],
                        record["ProductPrivatePart,"],
                        record["ProductVersion,"]
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
                o_id, d_id, i_id, h_id = get_os_directory_item_hash_ids(c, record['OS'], record['ParentPath'], record['Name'], record['sha256'])
                link_id = get_os_directory_item_hash_id(o_id, d_id, i_id, h_id)

                # Get the Link's target IDs
                path_item = link.rsplit('\\', 1)
                o_id, d_id, i_id, h_id = get_os_directory_item_hash_ids(c, record['OS'], path_item[0], path_item[1], record['sha256'])
                target_id = get_os_directory_item_hash_id(o_id, d_id, i_id, h_id)

                c.execute("INSERT OR REPLACE INTO Item_ADS (link_id, target_id) VALUES(?, ?);", 
                        (
                            link_id,
                            target_id
                        )
                    )

db.commit()
db.close()