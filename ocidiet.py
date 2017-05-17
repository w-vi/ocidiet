#!/usr/bin/env python

from __future__ import print_function  # Only needed for Python 2
import argparse
import logging
import os
import shutil
import subprocess
import tempfile
import textwrap
from distutils import dir_util


img_dir = None


def make_dir(directory):
    """mkdir -p like helper"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_base_dir():
    """Creates basic image directory structure in temp dir."""
    global img_dir
    if os.path.exists(img_dir):
        shutil.rmtree(img_dir, True)
    make_dir(img_dir)
    for d in ['dev', 'proc', 'sysfs']:
        make_dir("%s/%s" % (img_dir, d))


def add_to_image(path):
    """Add file on PATH to the image."""
    global img_dir
    src = os.path.abspath(path)
    dst = os.path.join(img_dir, src[1:])
    logging.info("Copy %s to %s" % (src, dst))
    make_dir(os.path.dirname(dst))
    shutil.copy2(src, dst)


def copy_binary_and_libs(binary):
    """Copy the binary and libs discovered by ldd."""
    if os.path.exists(binary) and os.path.isfile(binary):
        add_to_image(binary)

    proc = subprocess.Popen(['ldd', binary], bufsize=1,
                            universal_newlines=True, stdout=subprocess.PIPE)
    for l in proc.stdout:
        line = l.strip()
        if line != '' and '=>' in line:
            lib = line.split('=>')[1].strip().split(' ')[0]
            add_to_image(lib)
        elif line.startswith('/lib'):
            lib = line.split(' ')[0]
            add_to_image(lib)


def main():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent('''\
    Minimize docker images '''),
        epilog=textwrap.dedent('''\
    Example:
        ocidiet.py  -t my.tar -b `which mybinary` -e /etc/nsswitch.conf'''),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--verbose', help='verbose (print file names)',
                        action='store_true', default=False)
    parser.add_argument('-t', '--tarname', help='name of the final tar',
                        type=str, default='image.tar')
    parser.add_argument('-e', '--extra', help='extra files/dirs to package',
                        type=str, nargs='+')
    parser.add_argument('-b', '--binary', type=str, nargs='+')

    args = parser.parse_args()

    loglevel = logging.INFO

    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',
                        datefmt='%I:%M:%S', level=loglevel)

    logging.info("Create the image base directory structure.")

    global img_dir
    img_dir = tempfile.mkdtemp()
    create_base_dir()

    logging.info("Copy binary and needed libs")
    for b in args.binary:
        copy_binary_and_libs(b)

    if args.extra is not None:
        logging.info("Copy extra files and directories")
        for i in args.extra:
            p = os.path.abspath(i)
            if os.path.isdir(p):
                logging.info("Copy directory %s" % (p))
                dir_util.copy_tree(p,
                                   "%s/%s" % (img_dir, p),
                                   preserve_symlinks=1,
                                   verbose=args.verbose)
            else:
                add_to_image(p)

    os.system('tar cf %s -C %s .' % (args.tarname, img_dir))


if __name__ == '__main__':
    main()
