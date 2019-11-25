import os
import sys
import json
import subprocess

import pandas as pd
from datetime import datetime

from ns3.main import get_pattern_string, get_query, parse_cloudpath


def list_objects(bucketpath, inc_pattern=None, exc_pattern=None, limit=200,
                 query=None, dirs_only=False, starting_token=None):
    """
    List the files in supplied bucketpath from s3 cloud storage

    If recursive is True, then list recursively all objects (no dirs).

    Keyword Arguments:

        path {str}     -- path name (bucketpath)
                            (default: {''}, searches in working directory)

        use_cwd {bool} -- Whether to use the set working dir for bucket
                            if false, full path is to be provided in
                            [path] arg
                            (default: {True})

        filename_pattern {str} -- pattern to be followed in listing files
                            (default: {None})

        recursive {bool} -- Should you list sub-directories as well?
                            (default: {False})

        full_name {bool} -- whether to return full path to the files
                            (default: {True})

        list_dirs {bool} -- list the directories as well if true
                            lists only when recursive is False
                            (default: {False})

        list_objs {bool} -- list the objects as well when if true,
                            when recursive is False
                            (default: {True})

        limit {int}      -- number of objects to be listed from the path
                            (default: {None})

        obj {bool}       -- return the listed paths as S3Obj if true else
                            list of filenames
                            (default: {False})

    """
    bname, bpath = parse_cloudpath(bucketpath)

    iquery = get_pattern_string(inc_pattern) if inc_pattern else ''
    equery = get_pattern_string(exc_pattern) if exc_pattern else ''

    query = get_query(iquery, equery)

    s3cmd = ['aws s3api list-objects',
             f'--bucket {bname}',
             f'--prefix {bpath}',
             f'--max-items {limit}',
             '--output json']
    if query:
        s3cmd += [f'''--query "{query}"''']

    if starting_token:
        s3cmd += [f'''--starting-token "{starting_token}"''']

    s3cmd = ' '.join(s3cmd)

    objects = subprocess.check_output(
        s3cmd, shell=True
        ).decode("utf-8").strip()
    objects = json.loads(objects)

    _next_token = None
    if type(objects) == dict:
        try:
            _next_token = objects['NextToken']
        except:
            pass
        objects = objects['Contents']

    _df = pd.DataFrame.from_dict(objects)

    _df['LastModified'] = _df['LastModified'].apply(
        lambda x: datetime.strptime(
            x, '%Y-%m-%dT%H:%M:%S.%fZ'
        ).strftime('%d %b %H:%M')
    )
    _MB = (1024*1024)
    _GB = _MB * 1024
    _df['Size'] = _df['Size'].apply(
        lambda x: f'{round(x/_MB, 3)}M' if x/_MB <=1024 else f'{round(x/_GB, 3)}G'
    )
    _df.drop('StorageClass', 1, inplace=True)
    _df['bucket'] = bname

    return _df, _next_token