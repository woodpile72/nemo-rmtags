# Copyright (C) 2026 Erick Woods
# SPDX-License-Identifier: GPL-3.0-only
"""Internal tag-editing helper for the Remove ID Tag Nemo action."""

from mutagen.apev2 import APEv2, APENoHeaderError, delete as delete_ape
from mutagen.id3 import delete as delete_id3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Tags


def has_tags(path):
    if path.suffix.lower() != '.mp3':
        return bool(MP4(path).tags)
    audio = MP3(path)
    try:
        APEv2(path)
        return True
    except APENoHeaderError:
        return audio.tags is not None


def clean(path):
    if path.is_symlink():
        raise ValueError('symbolic links are skipped; specify the real file')
    if not has_tags(path):
        return
    if path.suffix.lower() == '.mp3':
        delete_ape(path)
        delete_id3(path, delete_v1=True, delete_v2=True)
    else:
        media = MP4(path)
        # Reuse the old tag space as zero-filled padding, avoiding a media-data move.
        # A fresh tag object also discards atoms Mutagen could not decode.
        media.tags = MP4Tags()
        media.save(padding=lambda info: max(0, info.padding))
    if has_tags(path):
        raise ValueError('tag verification failed after in-place editing')
