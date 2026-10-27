#!/usr/bin/python3
# Copyright (C) 2026 Erick Woods
# SPDX-License-Identifier: GPL-3.0-only
"""Run the tag cleaner from Nemo and report the result on the desktop."""

from pathlib import Path
import importlib.util
import shutil
import subprocess
import sys


EXTENSIONS = {'.mp3', '.mp4', '.m4a', '.m4v', '.m4b'}


def collect_files(paths):
    files = []
    seen = set()
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            raise ValueError(f'Not a supported media file: {path}')
        path = path.absolute()
        if path not in seen:
            seen.add(path)
            files.append(path)
    return files


def show_error(message):
    if shutil.which('zenity'):
        subprocess.run(['zenity', '--error', '--title=Remove ID Tag', '--no-markup',
                        '--width=600', '--text=' + message], check=False)
    elif shutil.which('notify-send'):
        subprocess.run(['notify-send', '--urgency=critical', 'Remove ID Tag', message],
                       check=False)
    else:
        print(message, file=sys.stderr)


def missing_dependencies():
    packages = []
    if importlib.util.find_spec('mutagen') is None:
        packages.append('python3-mutagen')
    for command, package in [('zenity', 'zenity'), ('notify-send', 'libnotify-bin')]:
        if not shutil.which(command):
            packages.append(package)
    return packages


def ensure_dependencies():
    packages = missing_dependencies()
    if not packages:
        return True

    installer = shutil.which('apturl')
    if not installer:
        show_error('Missing packages: ' + ', '.join(packages)
                   + '\nInstall them with Software Manager or run:\n'
                   + 'sudo apt install ' + ' '.join(packages)
                   + '\nThen run Remove ID Tag again. No files have been changed.')
        return False

    if shutil.which('zenity'):
        response = subprocess.run(
            ['zenity', '--question', '--title=Remove ID Tag', '--no-markup',
             '--width=500', '--ok-label=Open Installer', '--cancel-label=Cancel',
             '--text=Missing packages: ' + ', '.join(packages)
             + '\n\nOpen the package installer? After installing, run Remove ID Tag again.'
             + '\nNo files have been changed.'], check=False)
        if response.returncode != 0:
            return False

    # Without Zenity, the package installer's own confirmation is the prompt.
    try:
        result = subprocess.run([installer, 'apt:' + ','.join(packages)], check=False)
    except OSError as exc:
        show_error(f'Could not open the package installer: {exc}')
        return False
    if result.returncode != 0 or missing_dependencies():
        show_error('Required packages are still missing or installation was cancelled.'
                   '\nNo files have been changed. Run Remove ID Tag again after installing them.')
    else:
        subprocess.run(['notify-send', 'Remove ID Tag',
                        'Dependencies installed. Run Remove ID Tag again to process your files.'],
                       check=False)
    return False


def main():
    if not sys.argv[1:]:
        return 0
    try:
        paths = collect_files([Path(arg) for arg in sys.argv[1:]])
    except (OSError, ValueError) as exc:
        show_error(str(exc))
        return 1

    if not ensure_dependencies():
        return 1

    try:
        from rmtags import clean
    except (ImportError, SystemExit) as exc:
        show_error(str(exc))
        return 1

    errors = []
    for path in paths:
        try:
            clean(path)
        except Exception as exc:
            errors.append(f'{path}: {exc}')
    if errors:
        show_error('\n'.join(errors))
    else:
        count = len(paths)
        message = f'Done: {count} file(s). Tags and cover art removed.'
        subprocess.run(
            ['notify-send', '--app-name=Remove ID Tag', 'Remove ID Tag',
             message],
            check=False,
        )
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
