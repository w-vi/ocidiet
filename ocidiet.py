#!/usr/bin/env python2
import argparse
import logging
import os
import shutil
import subprocess
import tempfile
import textwrap
from distutils import dir_util


image_dir = None


def make_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_base_dir():
    global image_dir
    if os.path.exists(image_dir):
        shutil.rmtree(image_dir, True)
    make_dir(image_dir)
    for d in ['dev', 'proc', 'sysfs']:
        make_dir("%s/%s" % (image_dir, d))


def add_to_image(path):
    global image_dir
    src = os.path.abspath(path)
    dst = os.path.join(image_dir, src[1:])
    logging.info("Copying %s to %s" % (src, dst))
    make_dir(os.path.dirname(dst))
    shutil.copy2(src, dst)


def copy_binary_and_libs(binary):

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
    Minimize docker image '''),
        epilog=textwrap.dedent('''\
    Example:
        minimizer.py  path/to/binary'''),
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
    if args.verbose:
        loglevel = logging.DEBUG

    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',
                        datefmt='%I:%M:%S', level=loglevel)

    logging.info(args.extra)
    logging.info(args.binary)
    logging.info("Creating the image base directory structure.")

    global image_dir
    image_dir = tempfile.mkdtemp()
    create_base_dir()

    logging.info("Copy binary and needed libs")
    for b in args.binary:
        copy_binary_and_libs(b)

    logging.info("Copying extras")
    for i in args.extra:
        p = os.path.abspath(i)
        if os.path.isdir(p):
            logging.info("Copying directory %s" % (p))
            dir_util.copy_tree(p, "%s/%s" % (image_dir, p))
        else:
            logging.info("Copying file %s" % (p))
            add_to_image(p)

    os.system('tar cf %s -C %s .' % (args.tarname, image_dir))

if __name__ == '__main__':
    main()
