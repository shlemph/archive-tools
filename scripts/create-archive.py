#! /usr/bin/python

import argparse
from pathlib import Path
from archive import Archive

argparser = argparse.ArgumentParser()
argparser.add_argument('--compression',
                       choices=['none', 'gz', 'bz2', 'xz'], default='gz',
                       help=("compression mode"))
argparser.add_argument('--basedir',
                       help=("common base directory in the archive"))
argparser.add_argument('archive',
                       help=("path to the archive file"), type=Path)
argparser.add_argument('files', nargs='+', type=Path,
                       help="files to add to the archive")
args = argparser.parse_args()

if args.compression == 'none':
    args.compression = ''

if not args.basedir:
    if args.files[0].is_absolute():
        args.basedir = Path(args.archive.name.split('.')[0])
    else:
        if args.files[0].is_dir():
            args.basedir = args.files[0]
        else:
            args.basedir = args.files[0].parent

mode = 'x:%s' % args.compression

archive = Archive(args.archive, mode, args.files, args.basedir)