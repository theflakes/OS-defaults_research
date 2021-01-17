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
        if os.path.islink(path):
            linkPath = os.readlink(path)
            if linkPath[0] != '/':
                log['Links'] = parent_dir + os.readlink(path)
            else:
                log['Links'] = os.readlink(path)
        else:
            log['Links'] = None
        print_log(log)


def walk_tree_recurse(dir):
    for root, directories, files in os.walk(dir, followlinks=False):
        for d in directories:
            directory_path = os.path.join(root, d)
            get_metadata(root, directory_path, d)
        for f in files:
            file_path = os.path.join(root, f)
            get_metadata(root, file_path, f)


def walk_tree(dir):
    level = 0
    for root, directories, files in os.walk(dir, followlinks=False):
        if level == 1:
            return
        for d in directories:
            directory_path = os.path.join(root, d)
            get_metadata(root, directory_path, d)
        for f in files:
            file_path = os.path.join(root, f)
            get_metadata(root, file_path, f)
        level += 1


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
    if recurse:
        walk_tree_recurse(directory)
    else:
        walk_tree(directory)


# main
if __name__ == "__main__":
    main(sys.argv[1:])