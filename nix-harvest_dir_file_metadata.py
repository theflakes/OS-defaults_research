#!/usr/bin/python3

import os, sys, stat
import getopt
import json
import hashlib
import platform


recurse = False
pretty = False
directory = '/'
hashFile = False
BUF_SIZE = 65536


md5 = hashlib.md5()
sha1 = hashlib.sha1()
sha256 = hashlib.sha256()
arch = platform.architecture()[0][0:2]
version = platform.version()
oper = platform.system()


def init_log():
    log = {
        "Arch": arch,
        "Version": version,
        "OS": oper,
        "Name": None,
        "ParentPath": None,
        "BaseName": None,
        "Extension": None,
        "Mode": None,
        "Size": None,
        "Hidden": False,
        "Link": False,
        "Links": [None],
        "Streams": None,

        "md5": None,
        "sha1": None,
        "sha256": None,

        # including unused fields for parity with Windows PowerShell harvester
        "FileVersionRaw": None,
        "ProductVersionRaw": None,
        "Comments": None,
        "CompanyName": None,
        "FileBuildPart": None,
        "FileDescription": None,
        "FileMajorPart": None,
        "FileMinorPart": None,
        "FileName": None,
        "FilePrivatePart": None,
        "FileVersion": None,
        "InternalName": None,
        "IsDebug": None,
        "IsPatched": None,
        "IsPrivateBuild": None,
        "IsPreRelease": None,
        "IsSpecialBuild": None,
        "Language": None,
        "LegalCopyright": None,
        "LegalTrademarks": None,
        "OriginalFilename": None,
        "PrivateBuild": None,
        "ProductBuildPart": None,
        "ProductMajorPart": None,
        "ProductMinorPart": None,
        "ProductName": None,
        "ProductPrivatePart": None,
        "ProductVersion": None,
    }
    return log
    

def print_log(log):
    if pretty:
        log = json.dumps(log, indent=2)
    else:
        log = json.dumps(log)
    print(log)
    

def hash_file(path):
    with open(path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
            sha1.update(data)
            sha256.update(data)
    return md5.hexdigest(), sha1.hexdigest(), sha256.hexdigest()


def get_metadata(parent_dir, path, item):
    if path is not None:
        log = init_log()
        log['ParentPath'] = parent_dir
        log['Name'] = item
        if not os.path.isdir(path):
            nameExt = os.path.splitext(item)
            log['BaseName'] = nameExt[0]
            log['Extension'] = nameExt[1] if nameExt[1] else None
            if hashFile:
                log['md5'], log['sha1'], log['sha256'] = hash_file(path)
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


def print_help():
    print("\nnix-harvest_dir_file_metadata.py -r -p -d '/' -f")
    print("[*]  Root privileges may be needed to examine all items.\n")


def main(args):
    global recurse, pretty, directory, hashFile
    try:
        opts, args = getopt.getopt(args, "hrpsd:", ["help", "recurse", "pretty", "hashfiles", "directory"])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt in ("-r", "--recurse"):
            recurse = True
        elif opt in ("-p", "--pretty"):
            pretty = True
        elif opt in ("-d", "--directory"):
            directory = arg
        elif opt in ("-s", "--hashfiles"):
            hashFile = True
    if recurse:
        walk_tree_recurse(directory)
    else:
        walk_tree(directory)


# main
if __name__ == "__main__":
    main(sys.argv[1:])