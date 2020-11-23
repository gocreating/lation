#!/bin/bash
set -e

case "$@" in
*)
    exec gunicorn --config gunicorn_config.py lation.modules.$APP.app:app
    ;;
esac
