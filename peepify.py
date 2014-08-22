import argparse
import os
import re
import subprocess
import sys
from OpenSSL.SSL import ZeroReturnError

import requests


def bin_exists(binary):
    """Determine whether a specified binary exists on PATH"""
    try:
        subprocess.check_output(['which', binary])
        return True
    except subprocess.CalledProcessError:
        return False


USE_CURL = bin_exists('curl')


def download(target_fn, url):
    """Puts the downloaded file from `url` at `target_fn`."""
    if os.path.exists(target_fn):
        print '{0} already downloaded.'.format(url)
        return

    print "Downloading {0}...".format(target_fn)

    # Use curl if it exists. Otherwise use requests.
    if USE_CURL:
        subprocess.check_output(
            ['curl', '--silent', '-L', '-o', target_fn, url])
        return

    req = requests.get(url, stream=True)
    with open(target_fn + '.tmp', 'w') as f:
        try:
            for chunk in req.iter_content():
                f.write(chunk)
        except ZeroReturnError:
            # Get this when there's no more data to
            # retrieve and for some reason this gets
            # kicked up as an exception rather than
            # handled appropriately. Regardless, it means
            # we have the whole file.
            pass
    os.rename(target_fn + '.tmp', target_fn)


def get_packages(project_dir):
    """Generate package names and github urls from git submodules.

    @arg: project_dir: Project directory.
    """
    os.chdir(project_dir)
    project_cwd = os.getcwd()

    if not os.path.exists('.gitmodules'):
        raise Exception(".gitmodules not found!")

    submodules = {}
    with open('.gitmodules') as gitmodules:
        lines = [line.rstrip() for line in gitmodules]
        for i in xrange(0, len(lines), 3):
            path = lines[i+1].split(' = ')[1]
            # Ignore js submodules.
            if '/js/' in path:
                continue

            url = lines[i+2].split(' = ')[1]

            os.chdir(path)

            # Revision name
            revname = subprocess.check_output(
                ['git', 'name-rev', '--name-only', 'HEAD']).rstrip()

            # Current commit hash
            commit_hash = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD']).rstrip()

            # Fix url if it's broken.
            if url.startswith('git://'):
                url = url.replace('git://', 'https://', 1)
            if url.endswith('.git'):
                url = url[:-4]

            package_name = path.split('/')[-1]
            submodules[package_name] = (
                revname,
                '{0}/archive/{1}.tar.gz'.format(url, commit_hash))

            os.chdir(project_cwd)

    return submodules


def generate_requirements(packages, project_dir, tarball_dir):
    """Generates a requirement file from a list of packages.

    @arg: packages: Package names and urls.
    @arg: project_dir: Project directory.
    @arg: tarball_dir: Directory for downlaoding tar files.
    """
    req_format = '{0}{1}{2}\n\n'
    req_fn = os.path.abspath('peep_requirements.txt')

    if not os.path.exists(tarball_dir):
        os.makedirs(tarball_dir)

    with open(req_fn, 'w') as requirements:
        for name, data in packages.items():
            revname, url = data

            tarball = os.path.join(tarball_dir, name + '.tar.gz')
            download(tarball, url)

            print 'Hashing....'
            peep_hash = subprocess.check_output(['peep', 'hash', tarball])
            egg_ext = '#egg={0}'.format(name)

            requirements.write('# {0}: {1}\n'.format(name, revname))
            requirements.write(req_format.format(peep_hash, url, egg_ext))

    print 'Requirements file generated.'
    print 'You can find it at {0}.'.format(req_fn)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='peepify')
    parser.add_argument('--project-dir', required=True,
                        help='Project directory.')
    parser.add_argument('--tarballs-dir', help='Directory to store tarballs.',
                        default='/tmp')
    args = parser.parse_args()

    # Verify peep is installed. Otherwise bail.
    if not bin_exists('peep'):
        print '"peep" is not in your PATH. Please install it.'
        sys.exit(1)

    cwd = os.getcwd()
    packages = get_packages(args.project_dir)

    # Make sure paths line up still.
    os.chdir(cwd)
    generate_requirements(packages, args.project_dir, args.tarballs_dir)
