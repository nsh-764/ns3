#!/usr/bin/python3
"""
title                : Display the objects on S3 bucketpath in a tree-like diagram
author(s)            : Nikhil S Hubballi
last modified on     : 22nd Nov 2019
version              : 0.1.0
verified by          :
verified on          :
description          :
project              : Nested S3
working directory(s) :
remarks              :
"""

import re
import os
import sys
import json
import uuid
import signal
import shutil
import argparse
import subprocess
import pkg_resources
from pathlib import Path
from os.path import expanduser
from argparse import RawTextHelpFormatter as rawtxt

import pandas as pd
from datetime import datetime


def signal_handler(sig, frame):
    """
        Handling keyboard interrupt by user
    """
    sys.exit('Interrupted by user.')

signal.signal(signal.SIGINT, signal_handler)


def str2bool(value, raise_exc=False):
    _true_set = {'yes', 'true', 't', 'y', '1'}
    _false_set = {'no', 'false', 'f', 'n', '0'}
    if isinstance(value, str):
        value = value.lower()
        if value in _true_set:
            return True
        if value in _false_set:
            return False
        else:
            raise ValueError('Expected ("%s")' % '", "'.join(_true_set |
                                                             _false_set))
    else:
        raise Exception("Expected a string input")


def parse_cloudpath(path):
    """
    Parse the cloud path (s3) into bucket name and bucketpath.

    Arguments:

        path {str} -- cloud path with bucketname and path
                        (Examples: s3://bucket/bucketpath/to/file,
                                    bucket/bucketpath/to/file,
                                    arn:aws:s3:::bucket/bucketpath/to/file
                                    for S3)

    Returns:

        {tuple} -- a tuple of bucketname and bucketpath to file/directory
    """

    # clean path
    path = path.replace('s3://', '').replace('arn:aws:s3:::', '')

    bname = path.split('/')[0]
    bpath = '/'.join(path.split('/')[1:])
    bpath = re.sub('/$', '', bpath)

    return bname, bpath


def setup_temp(bucketpath):
    time = datetime.now().strftime('%Y%m%d-%H%M%S')
    folder = f"ns3-{str(uuid.uuid4())[:8]}-{time}"

    home = expanduser('~')
    base = os.path.join(home, folder)
    tempdir = os.path.join(base, bucketpath)
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
        os.chdir(base)
    else:
        sys.exit(
            Bcolors.WARNING
            + f"{tempdir} exists already"
            + Bcolors.ENDC
        )
    return base, tempdir


def query_yes_no(question, default="yes"):
    '''confirm or decline'''
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("\nPlease respond with 'yes' or 'no' (or 'y' or 'n').\n")


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    from shutil import which
    return which(name) is not None


class Bcolors:
    """
    console colors
    """
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    GREY = '\033[90m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_pattern_string(pattern):

    pattern = [x.strip() for x in pattern.split('|')]

    pat_query = []
    for pat in pattern:
        pat = re.sub(r'^\*', '', pat)
        pat = re.sub(r'\*$', '', pat)
        words = [word.strip() for word in pat.split('*')]
        query = ' && '.join([f"contains(Key, '{word}')" for word in words])
        query = f'({query})'
        pat_query.append(query)

    return f'({" || ".join(pat_query)})'


def get_query(iquery, equery):
    if not iquery and not equery:
        return ''
    if not equery:
        return f'''Contents[?{iquery}]'''
    elif not iquery:
        return f'''Contents[?!{equery}]'''
    else:
        return f'''Contents[?({iquery} && !{equery})]'''


def list_objects(cmd, bucketpath):
    # print(cmd)
    objects = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    objects = json.loads(objects)
    if len(objects) == 0:
        sys.exit(
            Bcolors.WARNING 
            + f"no objects in {bucketpath}"
            + Bcolors.ENDC
        )
    next_token = None
    if type(objects) == dict:
        try:
            next_token = objects['NextToken']
        except:
            pass
        objects = objects['Contents']

    return objects, next_token


def touch_files(objects, bpath, tempdir):

    df = pd.DataFrame.from_dict(objects)
    df['out'] = df['Key'].apply(lambda x: x.replace(bpath, tempdir))
    dirs = list(df['out'].apply(lambda x: os.path.dirname(x)).unique())
    _check = [os.makedirs(dr) for dr in dirs if not os.path.exists(dr)]
    _touch = df['out'].apply(lambda x: Path(x).touch())

    return df


def main():
    """
    Display the objects on S3 bucket path in a tree-like diagram
    """
    version = pkg_resources.require("ns3")[0].version
    parser = argparse.ArgumentParser(
        description='Display the objects on S3 bucketpath in a tree-like diagram',
        prog='ns3',
        formatter_class=rawtxt
    )

    #parser.print_help()
    parser.add_argument('bucketpath', type=str,
                        metavar='bucketpath',
                        help='''
Display the objects on S3 bucket path in a tree-like diagram
$ ns3 bucket-name/bucket-path
''')
    parser.add_argument('-Ipattern', type=str,
                        metavar='',
                        default=None,
                        help='''
File name pattern to be used to filter from listing the files
from a bucketpath.
Default: '*' (shows all files in the directory)
Examples:
1. path/file*123*.ext : to list all files with a pattern.
2. *p1* | *p2* : to list files with multiple patterns with an OR function.
''')
    parser.add_argument('-Epattern', type=str,
                        metavar='',
                        default=None,
                        help='''
File name pattern to be excluded from listed files
from a bucketpath.
Default: None (shows all files in the directory)
Examples:
1. path/file*123*.ext : to exclude listing all files with a pattern.
2. *p1* | *p2* : to exclude listing files with multiple patterns with
                 an OR function.
''')
    parser.add_argument('-limit', type=int,
                        metavar='',
                        default=200,
                        help='''
Number to be used to limit the number of files from the
provided bucketpath
Default: 200
''')
    parser.add_argument('-query', type=str,
                        metavar='',
                        default=None,
                        help='''
Any other query to be used in JMESPath format to be used on
the list response.
Default: None
''')
    parser.add_argument('-dirs_only', type=str2bool,
                        metavar='',
                        default='False',
                        help='''
List only the directories inside a provided S3
bucketpath.
Default: False
''')
    parser.add_argument('-listflat', type=str2bool,
                        metavar='',
                        default='False',
                        help='''
List all the files with in regular format with file size,
last modified date and full bucketpath to S3 object.
Default: False
''')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s '+version)
    args = parser.parse_args()

    bucketpath = re.sub('/$', '', args.bucketpath)
    bname, bpath = parse_cloudpath(bucketpath)
    if args.Ipattern:
        iquery = get_pattern_string(args.Ipattern)
    else:
        iquery = ''

    if args.Epattern:
        equery = get_pattern_string(args.Epattern)
    else:
        equery = ''

    # print(iquery, equery)
    query = get_query(iquery, equery)

    try:
        if not is_tool("tree"):
            print(
                Bcolors.WARNING
                + "please install tree to use this program"
                + Bcolors.ENDC
            )
            exit()
        s3cmd = ['aws s3api list-objects',
                 f'--bucket {bname}',
                 f'--prefix {bpath}',
                 f'--max-items {args.limit}',
                 '--output json']
        if query:
            s3cmd += [f'''--query "{query}"''']
        s3cmd = ' '.join(s3cmd)

        # print(tempdir)
        objects = []
        _objs, next_token = list_objects(s3cmd, bucketpath)
        objects += _objs
        while len(_objs) >= args.limit:
            if next_token:
                check = query_yes_no(
                    f'{len(objects)} listed. \n'
                    + 'There seems to be more files on this path, continue listing?'
                )
                if check:
                    s3cmd_tk = s3cmd + f' --starting-token "{next_token}"'
                    _objs, next_token = list_objects(s3cmd_tk, bucketpath)
                    objects += _objs
                else:
                    _objs = []
            else:
                _objs = []

        base, tempdir = setup_temp(bucketpath)

        _df = touch_files(objects, bpath, tempdir)

        if not args.listflat:
            if args.dirs_only:
                os.system(f'tree -d {bucketpath}')
            else:
                os.system(f'tree {bucketpath}')
        else:
            # @TODO: add list flat print method to command line.
            mb = (1024*1024)
            gb = mb * 1024
            _df['Size'] = _df['Size'].apply(
                lambda x: f'{round(x/mb, 3)}M' if x/mb <=1024 else f'{round(x/gb, 3)}G'
            )
            _df['LastModified'] = _df['LastModified'].apply(
                lambda x: datetime.strptime(
                    x, '%Y-%m-%dT%H:%M:%S.%fZ'
                ).strftime('%d %b %H:%M')
            )
            # [print(x) for x in _df[['Size', 'LastModified', 'Key']].values.tolist()]
        shutil.rmtree(base)
    except subprocess.CalledProcessError:
        sys.exit(
            Bcolors.WARNING
            + f"{bucketpath}: could not find objects"
            + Bcolors.ENDC
            )

if __name__ == "__main__":
    main()