#!/usr/bin/env bash
aria2_sync_fn() {
    rsync -rlptv --exclude '.git' --exclude '.idea' --exclude '*.iml' --exclude '*.pyc' . $1:~/devel/aria2-static
}

alias aria2.sync=aria2_sync_fn
