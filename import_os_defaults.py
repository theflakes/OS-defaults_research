#!/usr/bin/python3

import sqlite3
import json

with open("md.json", 'r', encoding='utf-16') as f:
    for line in f:
        record = json.loads(line)
        

