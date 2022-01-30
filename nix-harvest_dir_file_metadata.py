#!/usr/bin/python3


import os, sys, stat
import getopt
import json
import hashlib
import platform
from grp import getgrgid
from pwd import getpwuid

class Utilities(object):
    def __init__(self):
        self.md5 = hashlib.md5()
        self.sha1 = hashlib.sha1()
        self.sha256 = hashlib.sha256()
        self.BUF_SIZE = 65536

    def print_log(self, log):
        if self.pretty:
            log = json.dumps(log, indent=2)
        else:
            log = json.dumps(log)
        print(log)

    def ConvertTo_BinaryBool(bool):
        if bool is not None:
            if bool == True:
                return 1
            else:
                return 0
        else:
            return None
        
    def hash_file(self, path):
        try:
            with open(path, 'rb') as f:
                while True:
                    data = f.read(self.BUF_SIZE)
                    if not data:
                        break
                    self.md5.update(data)
                    self.sha1.update(data)
                    self.sha256.update(data)
            return self.md5.hexdigest(), self.sha1.hexdigest(), self.sha256.hexdigest()
        except:
            return None, None, None

class Harvest(Utilities):
    def __init__(self, directory, recurse, pretty, hash_files):
        super().__init__()
        self.directory = directory
        self.recurse = recurse
        self.pretty = pretty
        self.hash_files = hash_files
        self.ARCH = platform.architecture()[0][0:2]
        self.VERSION = platform.version()
        self.OPER = platform.system()

    def init_log(self):
        log = {
            "DataType": "FileSystem",
            "OS_Arch": self.ARCH,
            "Version": self.VERSION,
            "OS": self.OPER,
            
            "Name": None,
            "ParentPath": None,
            "BaseName": None,
            "Extension": None,
            "Mode": None,
            "Size": None,
            "Hidden": 0,
            "Link": 0,
            "Links": [None],
            "Streams": None,

            "md5": None,
            "sha1": None,
            "sha256": None,

            "BinArch": None,
            "IsDLL": None,
            "IsDriver": None,
            "IsEXE": None,
            "IsSigned": None,
            "IsSignatureValid": None,
            "Authenticode": None,
            "Magic": None,
            "NumberOfSections": None,
            
            # including unused fields for parity with Windows PowerShell harvester
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

            "Group": None,
            "User": None,
        }
        return log

    def get_metadata(self, parent_dir, path, item):
        if path is not None:
            log = self.init_log()
            log['ParentPath'] = parent_dir
            log['Name'] = item
            if not os.path.isdir(path):
                nameExt = os.path.splitext(item)
                log['BaseName'] = nameExt[0]
                log['Extension'] = nameExt[1] if nameExt[1] else None
                if self.hash_files:
                    log['md5'], log['sha1'], log['sha256'] = self.hash_file(path)
            else:
                log['BaseName'] = item
                log['Extension'] = None
            if not os.path.islink(path):
                md = os.stat(path)
                log['Mode'] = stat.filemode(md.st_mode)
                log['Size'] = md.st_size
                log['Group'] = getgrgid(md.st_gid).gr_name
                log['User'] = getpwuid(md.st_uid).pw_name
            else:
                md = os.lstat(path)
                log['Mode'] = stat.filemode(md.st_mode)
                log['Size'] = md.st_size
                log['Link'] = True
                log['Group'] = getgrgid(md.st_gid).gr_name
                log['User'] = getpwuid(md.st_uid).pw_name
                linkPath = os.readlink(path)
                if linkPath[0] != '/':
                    log['Links'] = [parent_dir + os.readlink(path)]
                else:
                    log['Links']= [os.readlink(path)]
            if item[0] == '.':
                log['Hidden'] = 1
            self.print_log(log)

    def walk_tree(self):
        for root, directories, files in os.walk(self.directory, followlinks=False):
            for d in directories:
                directory_path = os.path.join(root, d)
                self.get_metadata(root, directory_path, d)
            for f in files:
                file_path = os.path.join(root, f)
                self.get_metadata(root, file_path, f)
            if not self.recurse:
                return


def print_help():
    print("\nnix-harvest_dir_file_metadata.py -r -p -d '/' -f")
    print("[*]  Root privileges may be needed to examine all items.\n")


def main(args):
    recurse = False
    pretty = False
    directory = '/'
    hash_files = False
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
            hash_files = True
    harvest = Harvest(directory, recurse, pretty, hash_files)
    harvest.walk_tree()


# main
if __name__ == "__main__":
    main(sys.argv[1:])