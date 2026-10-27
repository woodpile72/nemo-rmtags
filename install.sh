#!/bin/sh
# Copyright (C) 2026 Erick Woods
# SPDX-License-Identifier: GPL-3.0-only
set -eu

source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
actions="${XDG_DATA_HOME:-$HOME/.local/share}/nemo/actions"

case "${1:-}" in
    --uninstall)
        rm -f -- "$actions/remove-id-tag.nemo_action" "$actions/rmtags/run.py" "$actions/rmtags/rmtags.py"
        rmdir -- "$actions/rmtags" 2>/dev/null || :
        printf '%s\n' 'Remove ID Tag uninstalled.'
        exit 0
        ;;
    '') ;;
    *) printf '%s\n' 'Usage: ./install.sh [--uninstall]' >&2; exit 1 ;;
esac

install -d -- "$actions/rmtags"
install -m 644 -- "$source_dir/rmtags.py" "$actions/rmtags/rmtags.py"
install -m 755 -- "$source_dir/run.py" "$actions/rmtags/run.py"
install -m 644 -- "$source_dir/remove-id-tag.nemo_action" "$actions/remove-id-tag.nemo_action"
printf '%s\n' 'Remove ID Tag installed. Right-click selected media files in Nemo.'
