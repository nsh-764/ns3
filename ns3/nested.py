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

    Keyword Arguments:

        bucketpath {str}  -- bucketpath from which files are to be listed

        inc_pattern {str} -- pattern to be followed while listing files
                            (default: {None})

        exc_pattern {str} -- pattern to be ignored while listing files
                            (default: {None})

        limit {int}      -- number of objects to be listed from the path
                            (default: {200})

        query {str}      -- add custom queries to the function to be used
                            while listing S3 objects
                            (default: {None)
                            (to be added soon)

        dirs_only {bool} -- list only the directories from the bucketpath
                            (default: {False})
                            (to be added soon)

        starting_token {bool} -- s3api token to be used to start the file
                            listing from.
                            (default: {True})

    Returns:

        _df {pandas dataframe} -- dataframe with columns Key (filepaths),
                             last modified time, file size, etag and bucketname

        _next_token {str}   -- s3api token, when listing limited number of
                             files from a path containing large number of files.
                             None if there are no files left to list.

    Examples:

        # list through all S3 objects under some dir with default limit
        >>> df, token = ns3.list_objects('bname/path/to/be/listed/on/bucket')

        # list thorough S3 objects under some directory with an inclusive pattern
        # limit 200
        >>> df, token = ns3.list_objects('bname/path/to/be/listed/on/bucket',
                                         inc_pattern='*india_villages*')
        >>> df, token = ns3.list_objects('bname/path/to/be/listed/on/bucket',
                                         inc_pattern='*villages*|*towns*')

        # list thorough S3 objects under some directory with an exclusive pattern
        # limit 200
        >>> df, token = ns3.list_objects('bname/path/to/be/listed/on/bucket',
                                         exc_pattern='*india_villages*')
        >>> df, token = ns3.list_objects('bname/path/to/be/listed/on/bucket',
                                         exc_pattern='*villages*|*towns*')

        # list through all S3 objects under some dir with specified limit
        >>> df, token = ns3.list_objects('bname/path/to/be/listed/on/bucket',
                                         limit=400)

        # list through all S3 objects under some dir with as starting toke
        >>> df, token = ns3.list_objects(
                'bname/path/to/be/listed/on/bucket',
                starting_token='eyJNYXJrZXIiOiBudWxsLCAiYm....'
            )
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