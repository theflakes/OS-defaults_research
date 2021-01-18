#!/usr/bin/python3

import os, sys, stat
import getopt
import json


recurse = False
pretty = False
directory = '/'


def init_log():
    log = {
        "Name": None,
        "ParentPath": None,
        "BaseName": None,
        "Extension": None,
        "Mode": None,
        "Size": None,
        "Hidden": False,
        "Link": False,
        "Links": [None]
    }
    return log
    

def print_log(log):
    if pretty:
        log = json.dumps(log, indent=2)
    else:
        log = json.dumps(log)
    print(log)


def get_metadata(parent_dir, path, item):
    if path is not None:
        log = init_log()
        log['ParentPath'] = parent_dir
        log['Name'] = item
        if not os.path.isdir(path):
            nameExt = os.path.splitext(item)
            log['BaseName'] = nameExt[0]
            log['Extension'] = nameExt[1] if nameExt[1] else None
        else:
            log['BaseName'] = item
            log['Extension'] = None
        if not os.path.islink(path):
            md = os.stat(path)
            log['Mode'] = stat.filemode(md.st_mode)
            log['Size'] = md.st_size
        else:
            md = os.lstat(path)
            log['Mode'] = stat.filemode(md.st_mode)
            log['Size'] = md.st_size
            log['Link'] = True
            linkPath = os.readlink(path)
            if linkPath[0] != '/':
                log['Links'] = [parent_dir + os.readlink(path)]
            else:
                log['Links']= [os.readlink(path)]
        if item[0] == '.':
            log['Hidden'] = True
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