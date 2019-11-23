# ns3
Nested S3 - Display the objects on S3 bucket path in a tree-like diagram

## How?
It uses the tree command to display the objects in an s3 bucketpath in a tree-like diagram.

## Dependencies
```bash
tree        : $ sudo apt-get install tree | brew install tree
python3     : $ sudo apt-get install python3 python3-dev pip
aws cli     : $ pip3 install awscli
```

## Installation
```bash
$ python3 setup.py install
```

## Usage
```bash
$ ns3 bucket-name/bucket-path -option value

usage: ns3 [-h] [-Ipattern] [-Epattern] [-limit] [-query] [-dirs_only]
           [-listflat] [-v]
           bucketpath

Display the objects on S3 bucketpath in a tree-like diagram

positional arguments:
  bucketpath
                 Display the objects on S3 bucket path in a tree-like diagram
                 $ ns3 bucket-name/bucket-path

optional arguments:
  -h, --help     show this help message and exit
  -Ipattern
                 File name pattern to be used to filter from listing the files
                 from a bucketpath.
                 Default: '*' (shows all files in the directory)
                 Examples:
                 1. path/file*123*.ext : to list all files with a pattern.
                 2. *p1* | *p2* : to list files with multiple patterns with an OR function.
  -Epattern
                 File name pattern to be excluded from listed files
                 from a bucketpath.
                 Default: None (shows all files in the directory)
                 Examples:
                 1. path/file*123*.ext : to exclude listing all files with a pattern.
                 2. *p1* | *p2* : to exclude listing files with multiple patterns with
                                  an OR function.
  -limit
                 Number to be used to limit the number of files from the
                 provided bucketpath
                 Default: 200
  -query        (To be added soon)
                 Any other query to be used in JMESPath format to be used on
                 the list response.
                 Default: None
  -dirs_only
                 List only the directories inside a provided S3
                 bucketpath.
                 Default: False
  -listflat     (To be added soon)
                 List all the files with in regular format with file size,
                 last modified date and full bucketpath to S3 object.
                 Default: False
  -v, --version  show program's version number and exit
```

## Example
```bash
$ ns3 bucket/insight/path/clean

bucket/insight/path/clean
├── test_example_1_dissolved.cpg
├── test_example_1_dissolved.dbf
├── test_example_1_dissolved.prj
├── test_example_1_dissolved.qpj
├── test_example_1_dissolved.shp
├── test_example_1_dissolved.shx
├── india
│   ├── grid_e8
│   │   └── yearly
│   │       ├── example_ds_Y2014_india_aggregated.csv
│   │       ├── example_ds_Y2015_india_aggregated.csv
│   │       ├── example_ds_Y2016_india_aggregated.csv
│   │       ├── example_ds_Y2017_india_aggregated.csv
│   │       └── example_ds_Y2018_india_aggregated.csv
│   └── raster500m
│       └── yearly
│           ├── example_ds_Y2014_india_ub.tif
│           ├── example_ds_Y2015_india_ub.tif
│           ├── example_ds_Y2016_india_ub.tif
│           ├── example_ds_Y2017_india_ub.tif
│           └── example_ds_Y2018_india_ub.tif
└── towns
    └── dissolved_towns
        ├── polygon_boundaries_2014.geojson
        └── polygon_boundaries_2014_dissolved.geojson

7 directories, 18 files
```
