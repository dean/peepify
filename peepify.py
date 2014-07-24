import argparse
import os
import re
import subprocess
import sys

import requests
from OpenSSL.SSL import ZeroReturnError


def bin_exists(binary):
    """Determine whether a specified binary exists on PATH"""
    try:
        subprocess.check_output(['which', binary])
        return True
    except subprocess.CalledProcessError:
        return False


USE_CURL = bin_exists('curl')


def download(target_fn, url):
    if os.path.exists(target_fn):
        print '{0} already downloaded.'.format(url)
        return

    print "Downloading {0}...".format(target_fn)

    # Use curl if it exists. Otherwise use requests.
    if USE_CURL:
        subprocess.check_output(['curl', '--silent', '-o', target_fn, url])
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


def get_packages(target_dir):
    """Generate package names and github urls from git submodules.

    @arg: target_dir: Directory with submodules.
    """
    os.chdir(target_dir)
    all_paths = [o for o in os.listdir('.')
                 if os.path.isdir(o)]
    packages = {}
    for directory in all_paths:
        os.chdir(directory)
        remotes = subprocess.check_output(['git', 'remote', '-v'])
        full_remote = remotes.split('\n')[0]

        # Example full_remote: origin\tgit@github.com/dean/peepify.git (fetch)
        remote_re = re.compile('^.*\\t(.+?)(?:\.git)? \((?:fetch|push)\)$')
        match = remote_re.match(full_remote)
        if not match:
            print "Fetch url mal-formated: {0}".format(full_remote)
            continue

        remote = match.group(1)
        if remote.startswith('git://'):
            remote = remote.replace('git://', 'https://', 1)

        package_name = remote.split('/')[-1]
        original_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'])
        original_hash = original_hash.rstrip()

        revname = subprocess.check_output(['git', 'name-rev', '--name-only', 'HEAD'])

        packages[package_name] = (
            revname,
            '{0}/archive/{1}.tar.gz'.format(remote, original_hash))

        os.chdir('../')
    return packages


def generate_requirements(packages, target_dir, tarball_dir):
    """Generates a requirement file from a list of packages.

    @arg: packages: Package names and urls.
    @arg: target_dir: Target directory for git submodules.
    @arg: tarball_dir: Directory for downlaoding tar files.
    """
    req_format = '{0}{1}{2}\n\n'
    req_fn = os.path.abspath('requirements.txt')

    if not os.path.exists(tarball_dir):
        os.makedirs(tarball_dir)

    with open(req_fn, 'w') as requirements:
        for name, data in packages.items():
            revname, url = data

            if name in target_dir.split('/'):
                print "Don't download the current project: {0}".format(name)
                continue

            tarball = os.path.join(tarball_dir, name + '.tar.bz')
            download(tarball, url)

            print 'Hashing....'
            peep_hash = subprocess.check_output(['peep', 'hash', tarball])
            egg_ext = '#egg={0}'.format(name)

            requirements.write('# {0}: {1}'.format(name, revname))
            requirements.write(req_format.format(peep_hash, url, egg_ext))

    print 'Requirements file generated.'
    print 'You can find it at {0}.'.format(req_fn)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='peepify')
    parser.add_argument('--target-dir', required=True,
                        help='Top level directory for git submodules.')
    parser.add_argument('--tarballs-dir', help='Directory to store tarballs.',
                        default='.')
    args = parser.parse_args()

    # Verify peep is installed. Otherwise bail.
    if not bin_exists('peep'):
        print '"peep" is not in your PATH. Please install it.'
        sys.exit(1)

    cwd = os.getcwd()
    packages = get_packages(args.target_dir)

    # Make sure paths line up still.
    os.chdir(cwd)
    generate_requirements(packages, args.target_dir, args.tarballs_dir)
