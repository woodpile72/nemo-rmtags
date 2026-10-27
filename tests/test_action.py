# Copyright (C) 2026 Erick Woods
# SPDX-License-Identifier: GPL-3.0-only
import configparser
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import run as action
import rmtags

ROOT = Path(__file__).resolve().parents[1]


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_media_filter_and_multiple_selection(self):
        config = configparser.ConfigParser(interpolation=None)
        config.read(ROOT / 'remove-id-tag.nemo_action')
        settings = config['Nemo Action']
        self.assertEqual(settings['Selection'], 'notnone')
        self.assertEqual(settings['Quote'], 'single')
        self.assertEqual(settings['Dependencies'], '/usr/bin/python3;')
        self.assertEqual(set(settings['Extensions'].strip(';').split(';')),
                         {ext[1:] for ext in action.EXTENSIONS})
        files = [self.root / ("space 'quote' $name" + ext.upper())
                 for ext in sorted(action.EXTENSIONS)]
        for path in files:
            path.touch()
        self.assertEqual(action.collect_files(files + files), files)
        with self.assertRaises(ValueError):
            action.collect_files([self.root])
        other = self.root / 'other.txt'
        other.touch()
        with self.assertRaises(ValueError):
            action.collect_files([files[0], other])

    def test_dependency_detection(self):
        with patch.object(action.importlib.util, 'find_spec', return_value=None), \
                patch.object(action.shutil, 'which', return_value=None):
            self.assertEqual(action.missing_dependencies(),
                             ['python3-mutagen', 'zenity', 'libnotify-bin'])

    def test_no_installer_when_dependencies_present(self):
        with patch.object(action, 'missing_dependencies', return_value=[]), \
                patch.object(action.subprocess, 'run') as process:
            self.assertTrue(action.ensure_dependencies())
            process.assert_not_called()

    def test_cancel_install(self):
        with patch.object(action, 'missing_dependencies', return_value=['python3-mutagen']), \
                patch.object(action.shutil, 'which', side_effect=lambda cmd: '/usr/bin/' + cmd), \
                patch.object(action.subprocess, 'run',
                             return_value=subprocess.CompletedProcess([], 1)) as process:
            self.assertFalse(action.ensure_dependencies())
            self.assertEqual(process.call_count, 1)
            self.assertEqual(process.call_args.args[0][0], 'zenity')

    def test_install_success_and_bootstrap_without_zenity(self):
        for has_zenity in (True, False):
            with self.subTest(has_zenity=has_zenity):
                packages = ['python3-mutagen'] if has_zenity else ['zenity', 'libnotify-bin']
                def which(cmd):
                    return None if cmd == 'zenity' and not has_zenity else '/usr/bin/' + cmd
                with patch.object(action, 'missing_dependencies', side_effect=[packages, []]), \
                        patch.object(action.shutil, 'which', side_effect=which), \
                        patch.object(action.subprocess, 'run',
                                     return_value=subprocess.CompletedProcess([], 0)) as process:
                    self.assertFalse(action.ensure_dependencies())
                    calls = [call.args[0] for call in process.call_args_list]
                    self.assertIn(['/usr/bin/apturl', 'apt:' + ','.join(packages)], calls)
                    self.assertEqual(calls[-1][0], 'notify-send')

    def test_missing_installer(self):
        with patch.object(action, 'missing_dependencies', return_value=['python3-mutagen']), \
                patch.object(action.shutil, 'which', return_value=None), \
                patch.object(action, 'show_error') as error:
            self.assertFalse(action.ensure_dependencies())
            self.assertIn('sudo apt install python3-mutagen', error.call_args.args[0])

    def test_install_failure(self):
        with patch.object(action, 'missing_dependencies', return_value=['python3-mutagen']), \
                patch.object(action.shutil, 'which', side_effect=lambda cmd: '/usr/bin/' + cmd), \
                patch.object(action.subprocess, 'run',
                             return_value=subprocess.CompletedProcess([], 0)), \
                patch.object(action, 'show_error') as error:
            self.assertFalse(action.ensure_dependencies())
            error.assert_called_once()

    def test_dependency_setup_never_edits_files(self):
        path = self.root / 'test.mp3'
        path.touch()
        with patch.object(sys, 'argv', ['run.py', str(path)]), \
                patch.object(action, 'ensure_dependencies', return_value=False), \
                patch.object(rmtags, 'clean') as clean:
            self.assertEqual(action.main(), 1)
            clean.assert_not_called()

    def test_continue_after_error_without_per_file_processes(self):
        paths = [self.root / 'bad.mp3', self.root / 'good.M4V']
        for path in paths:
            path.touch()
        with patch.object(sys, 'argv', ['run.py', *map(str, paths)]), \
                patch.object(action, 'ensure_dependencies', return_value=True), \
                patch.object(rmtags, 'clean', side_effect=[ValueError('bad file'), None]) as clean, \
                patch.object(action, 'show_error') as error, \
                patch.object(action.subprocess, 'run') as process:
            self.assertEqual(action.main(), 1)
            self.assertEqual(clean.call_count, 2)
            error.assert_called_once()
            process.assert_not_called()

    def test_installer_and_uninstaller(self):
        env = dict(os.environ, XDG_DATA_HOME=str(self.root / 'data with spaces'))
        subprocess.run([str(ROOT / 'install.sh')], env=env, check=True, capture_output=True)
        actions = Path(env['XDG_DATA_HOME']) / 'nemo/actions'
        for source, target in [('run.py', 'rmtags/run.py'), ('rmtags.py', 'rmtags/rmtags.py'),
                               ('remove-id-tag.nemo_action', 'remove-id-tag.nemo_action')]:
            self.assertEqual((ROOT / source).read_bytes(), (actions / target).read_bytes())
        unrelated = actions / 'unrelated.nemo_action'
        unrelated.touch()
        subprocess.run([str(ROOT / 'install.sh'), '--uninstall'], env=env,
                       check=True, capture_output=True)
        self.assertFalse((actions / 'remove-id-tag.nemo_action').exists())
        self.assertFalse((actions / 'rmtags/run.py').exists())
        self.assertTrue(unrelated.exists())
