import argparse
import os


def get_python_packages(packages_dir):
    os.chdir(packages_dir)
    paths = [path for path in os.listdir('.') if os.path.isdir(path)]

    packages = {}
    for package_name in paths:
        print 'Working on {0}'.format(package_name)
        version = ''
        try:
            with open(os.path.join(package_name, 'PKG-INFO'), 'rb') as fp:
                version = [line for line in fp.readlines() if line.startswith('Version: ')]
                if version:
                    # Grab the first line and nix the Version: label
                    version = version[0].replace('Version: ', '').strip()
        except Exception as exc:
            print package_name, exc

        packages[package_name] = version

    return packages


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='poopify')
    parser.add_argument('--packages-dir', required=True,
                        help='Top level directory for python packages.')

    args = parser.parse_args()

    cwd = os.getcwd()
    packages = get_python_packages(args.packages_dir)

    missing_versions = []
    for name, version in packages.items():
        if not version:
            missing_versions.append(name)
            continue

        print '{0}=={1}'.format(name, version)
        print ''

    if missing_versions:
        print 'These are missing version information:'
        for name in missing_versions:
            print name
