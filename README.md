# Remove ID Tag for Nemo

Adds **Remove ID Tag** to Nemo's right-click menu for MP3, MP4, M4A, M4V,
and M4B files. Select one file or several. The action does not appear for
folders or selections containing unsupported file types.

Removes ID3v1, ID3v2, and APEv2 tags from MP3 files, and iTunes-style metadata
from MP4-family files, including embedded cover art. Audio and video are not
re-encoded. MP4 structural information and chapters are retained; this is not
a tool for removing every possible piece of container metadata.

Files are edited **in place, without backups or an undo operation**. Avoid
interrupting an edit. MP4 tag space is reused as empty padding to avoid moving
the media data, so file size generally will not decrease. The selection runs
in one Python process without making whole-file temporary copies.

## Installation

For Linux Mint with Nemo, or another Linux desktop using Nemo:

```sh
git clone https://github.com/woodpile72/nemo-rmtags.git
cd nemo-rmtags
./install.sh
```

Run the installer as your normal user, not with sudo. It installs into
`${XDG_DATA_HOME:-~/.local/share}/nemo/actions`. Nemo normally detects the
action automatically. Right-click selected media files and choose
**Remove ID Tag**. A notification reports completion; errors appear in a dialog.
If a file fails, the action continues processing the other selected files.

## Dependencies

- Nemo
- Python 3.8 or newer, available at `/usr/bin/python3`
- Mutagen (`python3-mutagen` on Mint/Debian/Ubuntu)
- Zenity (`zenity`) for dialogs
- `notify-send` (`libnotify-bin`) for notifications

Install these packages manually if needed:

```sh
sudo apt install python3 python3-mutagen zenity libnotify-bin
```

When Mutagen, Zenity, or notify-send is missing, the action can open the
system's `apturl` package installer (Captain on current Linux Mint). The
installer handles confirmation and authentication. If Zenity is available,
the action asks before opening the installer; otherwise the installer's own
confirmation is used. No media files are changed during dependency setup.
Run the action again after installation.

Without `apturl`, the action reports the missing packages and an installation
command. If neither dialog nor notification tools are available, that message
can only go to standard error. Without Python, Nemo hides the action.

## Updating or Removing

To update an existing installation:

```sh
git pull --ff-only
./install.sh
```

To remove the action and its helper scripts:

```sh
./install.sh --uninstall
```

## Tests

```sh
/usr/bin/python3 -m unittest discover -s tests -v
```

Media integration tests additionally require `ffmpeg`, which is not needed
to use the action. Tests create temporary media fixtures, verify stream hashes,
and mock installer and notification calls. They do not modify your media or
install packages.

## License

Copyright (C) 2026 Erick Woods.

Licensed under the GNU General Public License, version 3 only (GPL-3.0-only).
See [LICENSE](LICENSE) for the full license text.
