# Copyright (C) 2026 Erick Woods
# SPDX-License-Identifier: GPL-3.0-only
import base64
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from mutagen.apev2 import APEv2
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4, MP4Cover

import rmtags

COVER = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII=')


@unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg is needed for media fixtures')
class TagTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def ffmpeg(self, *args):
        return subprocess.run(['ffmpeg', '-v', 'error', *map(str, args)],
                              check=True, capture_output=True).stdout

    def digest(self, path):
        return self.ffmpeg('-i', path, '-map', '0:a?', '-map', '0:V?',
                           '-c', 'copy', '-f', 'streamhash', '-')

    def test_mp3_id3_ape_and_cover(self):
        path = self.root / 'test.mp3'
        self.ffmpeg('-f', 'lavfi', '-i', 'sine=duration=0.2',
                    '-metadata', 'title=Test title', path)
        tags = ID3(path)
        tags.add(APIC(mime='image/png', type=3, data=COVER))
        tags.save(path, v1=2)
        ape = APEv2()
        ape['Comment'] = 'Test APE comment'
        ape.save(path)
        before = self.digest(path)
        inode = path.stat().st_ino
        rmtags.clean(path)
        self.assertFalse(rmtags.has_tags(path))
        self.assertEqual(self.digest(path), before)
        self.assertEqual(path.stat().st_ino, inode)
        self.assertNotIn(COVER, path.read_bytes())
        self.assertEqual(list(self.root.iterdir()), [path])

    def test_mp4_family_tags_covers_chapters_and_streams(self):
        metadata = self.root / 'chapters.txt'
        metadata.write_text(';FFMETADATA1\n[CHAPTER]\nTIMEBASE=1/1000\n'
                            'START=0\nEND=200\ntitle=Chapter one\n')
        source = self.root / 'source.mp4'
        self.ffmpeg('-f', 'lavfi', '-i', 'color=size=64x64:duration=0.2',
                    '-f', 'lavfi', '-i', 'sine=duration=0.2', '-i', metadata,
                    '-map_metadata', '2', '-c:v', 'mpeg4', '-c:a', 'aac',
                    '-movflags', '+faststart', '-metadata', 'title=Test title', source)
        media = MP4(source)
        media['covr'] = [MP4Cover(COVER, imageformat=MP4Cover.FORMAT_PNG)]
        media.save()
        chapters = [(chapter.start, chapter.title) for chapter in MP4(source).chapters]
        self.assertTrue(chapters)
        for suffix in ('.mp4', '.m4a', '.m4v', '.m4b'):
            with self.subTest(suffix=suffix):
                path = self.root / ('test' + suffix)
                shutil.copy2(source, path)
                before = self.digest(path)
                size = path.stat().st_size
                rmtags.clean(path)
                self.assertFalse(rmtags.has_tags(path))
                self.assertEqual(self.digest(path), before)
                self.assertEqual(path.stat().st_size, size)
                self.assertNotIn(COVER, path.read_bytes())
                self.assertNotIn(b'Test title', path.read_bytes())
                self.assertEqual([(c.start, c.title) for c in MP4(path).chapters], chapters)
                cleaned = path.read_bytes()
                rmtags.clean(path)
                self.assertEqual(path.read_bytes(), cleaned)

    def test_symlink_is_rejected(self):
        target = self.root / 'target.mp3'
        target.touch()
        link = self.root / 'link.mp3'
        link.symlink_to(target)
        with self.assertRaises(ValueError):
            rmtags.clean(link)
