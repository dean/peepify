import argparse
import os
import re
import subprocess

import requests


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

        tarball_url = '{0}/archive/{1}.tar.gz'
        packages[package_name] = tarball_url.format(remote, original_hash)
        os.chdir('../')
    return packages


def generate_requirements(packages, target_dir, tarball_dir):
    """Generates a requirement file from a list of packages.

    @arg: packages: Package names and urls.
    @arg: target_dir: Target directory for git submodules.
    @arg: tarball_dir: Directory for downlaoding tar files.
    """
    req_format = '{0}{1}{2}\n\n'
    requirements = open('requirements.txt', 'w')

    if not os.path.exists(tarball_dir):
        os.makedirs(tarball_dir)

    for name, url in packages.items():
        if name in target_dir.split('/'):
            print "Don't download the current project: {0}".format(name)
            continue

        tarball = os.path.join(tarball_dir, name + '.tar.bz')
        if not os.path.exists(tarball):
            print "Downloading {0}...".format(tarball)
            req = requests.get(url, stream=True)
            try:
                with open(tarball, 'w') as f:
                    for chunk in req.iter_content():
                        f.write(chunk)
            except:
                pass
        else:
            print "Package {0} already exists.".format(name)

        peep_hash = subprocess.check_output(['peep', 'hash', tarball])
        egg_ext = '#egg={0}'.format(name)
        install = req_format.format(peep_hash, url, egg_ext)
        requirements.write(install)

    requirements.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='peepify')
    parser.add_argument('--target-dir', required=True,
                        help='Top level directory for git submodules.')
    parser.add_argument('--tarballs-dir', help='Directory to store tarballs.',
                        default='.')
    args = parser.parse_args()

    cwd = os.getcwd()
    packages = get_packages(args.target_dir)

    # Make sure paths line up still.
    os.chdir(cwd)
    generate_requirements(packages, args.target_dir, args.tarballs_dir)
