# -*- coding: utf-8 -*-
# tree.py
"""
 Written by Doug Dahms, modified by luckydonald 2016

 Prints the tree structure for the path specified on the command line

 http://code.activestate.com/recipes/217212-treepy-graphically-displays-the-directory-structur/
"""
# import os
from os import listdir, sep
from os.path import abspath, basename, isdir


def tree_linux(directory, padding="", print_files=False):
    """
    Not confirmed to work...
    """
    from os import popen
    return_string = ""
    cmd = "find '%s'" % dir
    files = popen(cmd).read().strip().split('\n')
    padding = '|  '
    for file in files:
        level = file.count(sep)
        pieces = file.split(sep)
        symbol = {0: '', 1: '/'}[isdir(file)]
        if not print_files and symbol != '/':
            continue
        return_string += padding * level + pieces[-1] + symbol
        print(padding * level + pieces[-1] + symbol)
        # end for


# end def


def tree(directory, padding="", print_files=False, level=-1, print_it=True):
    return_string = ""
    string = padding[:-1] + '+-' + basename(abspath(directory)) + '/'
    if print_it:
        print(string)
    # end if
    return_string += string + "\n"
    if level != -1:
        if level == 0:
            return return_string
        level -= 1
    # end if
    padding += ' '
    files = []
    if print_files:
        try:
            files = listdir(directory)
        except PermissionError:
            files = PermissionError
    else:
        files = [x for x in listdir(directory) if isdir(directory + sep + x)]
    count = 0
    if files == PermissionError:
        string = padding + '|' + '\n'
        string += padding + 'X- PERMISSION DENIED'
        if print_it:
            print(string)
        # end if
        return_string += string + "\n"
        files = []
    for file in files:
        count += 1
        string = padding + '|'
        if print_it:
            print(string)
        # end if
        return_string += string + "\n"
        path = directory + sep + file
        if isdir(path):
            if count == len(files):  # last one
                return_string += tree(path, padding + ' ', print_files, level=level)
            else:
                return_string += tree(path, padding + '|', print_files, level=level)
        else:
            string = padding + '+-' + file
            if print_it:
                print(string)
            # end if
            return_string += string + "\n"
    return return_string


# end def


def usage():
    from sys import argv
    return '''Usage: %s [-f] [<LEVELS>] <PATH>
Print tree structure of path specified.
Options:
-f      Print files as well as directories
LEVELS  How many levels to print. -1 means unlimited
PATH    Path to process''' % basename(argv[0])


# end def


def main(*args):
    if not args:
        from sys import argv as args
    if len(args) == 1:
        print(usage())
    elif len(args) == 2:
        # print just directories
        path = args[1]
        if isdir(path):
            tree(path, ' ')
        else:
            print('ERROR: \'' + path + '\' is not a directory')
    elif len(args) == 3:
        # 2 params
        if args[1] == '-f':
            # print directories and files
            path = args[2]
            if isdir(path):
                tree(path, ' ', True)
            else:
                print('ERROR: \'' + path + '\' is not a directory')
                # end if
        else:
            # print directories up to level
            try:
                levels = int(args[1])
            except Exception:
                print("ERROR: could not parse level '" + args[1] + " as integer")
            else:  # no Exception
                path = args[2]
                if isdir(path):
                    tree(path, ' ', True, level=levels)
                else:
                    print('ERROR: \'' + path + '\' is not a directory')
                    # end if
                    # end try
                    # end if
    elif len(args) == 4 and args[1] == '-f':
        # 3 params.
        # print directories and files up to level
        try:
            levels = int(args[2])
        except Exception:
            print("ERROR: could not parse level '" + args[1] + " as integer")
        else:  # no Exception
            path = args[3]
            if isdir(path):
                tree(path, ' ', True, level=levels)
            else:
                print('ERROR: \'' + path + '\' is not a directory')
                # end if
                # end try
    else:
        print(usage())


if __name__ == '__main__':
    main()
