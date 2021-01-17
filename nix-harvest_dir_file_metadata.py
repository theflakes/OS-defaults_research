#!/usr/bin/python3

import os, sys, stat
import getopt
import json


recurse = False
pretty = False
directory = '/'


def print_log(log):
    if pretty:
        log = json.dumps(log, indent=2)
    else:
        log = json.dumps(log)
    print(log)


def get_metadata(parent_dir, path, item):
    log = {}
    if path is not None and os.path.exists(path):
        if os.path.isfile(path):
            extension = os.path.splitext(path)[1] if os.path.splitext(path)[1] else None
        else:
            extension = None
        md = os.stat(path)
        log['Extension'] = extension
        log['Mode'] = stat.filemode(md.st_mode)
        log['ParentPath'] = parent_dir
        log['BaseName'] = item
        log['Name'] = item
        log['Size'] = md.st_size
        if item[0] == '.':
            log['Hidden'] = True
        else:
            log['Hidden'] = False
        print_log(log)


def walk_tree(dir):
    for root, directories, files in os.walk(dir):
        for d in directories:
            directory_path = os.path.join(root, d)
            get_metadata(root, directory_path, d)
        for f in files:
            file_path = os.path.join(root, f)
            get_metadata(root, file_path, f)


def main(args):
    global recurse
    global pretty
    global directory
    try:
        opts, args = getopt.getopt(args, "hrpd:", ["--help", "--recurse", "--pretty", "--directory"])
    except getopt.GetoptError:
        print("nix-harvest_dir_file_metadata.py -r -p -d '/'")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("nix-harvest_dir_file_metadata.py -r -p -d '/'")
            sys.exit()
        elif opt in ("-r", "--recurse"):
            recurse = True
        elif opt in ("-p", "--pretty"):
            pretty = True
        elif opt in ("-d", "--directory"):
            directory = arg
    walk_tree(directory)


# main
if __name__ == "__main__":
    main(sys.argv[1:])