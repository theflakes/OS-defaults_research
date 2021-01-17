#!/usr/bin/python

import os
import sys
import getopt
import json


recurse = False
pretty = False
directory = '/'

# reference: https://gist.github.com/beugley/47b4812df0837fc90e783347faee2432
def perm_to_text(octal):
    result =  ''
    first = 0
    octal = str(octal)
    
    #if there are more than 4 digits, just take the last 4
    if len(octal)>4:
        #separate initial digit
        octal = octal [-4:]
    #if there are 4 digits, deal with first (setuid, setgid, and sticky flags) separately
    if len(octal)==4:
        if octal[0]!='0': 
            first = int(octal [:1])
        octal = octal [-3:]
    value_letters = [(4, 'r'), (2, 'w'), (1, 'x')]
    # Iterate over each of the digits in octal
    for permission in [int(n) for n in octal]:
        # Check for each of the permissions values
        for value, letter in value_letters:
            if permission >= value:
                result += letter
                permission -= value
            else:
                result += '-'
    if first!=0:
        for value in [4,2,1]:
            if first >= value:
                if value==4:
                    if result[2] == 'x':
                        result = result[:2]+'s'+result[3:]
                    elif result[2] == '-':
                        result = result[:2]+'S'+result[3:]
                if value==2:
                    if result[5] == 'x':
                        result = result[:5]+'s'+result[6:]
                    elif result[5] == '-':
                        result = result[:5]+'S'+result[6:]            
                if value==1:
                    if result[8] == 'x':
                        result = result[:8]+'t'+result[9:]
                    elif result[8] == '-':
                        result = result[:8]+'T'+result[9:]             
                first -= value   
    return result


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
        mode = perm_to_text(md.st_mode)
        log['Extension'] = extension
        log['Mode'] = mode
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