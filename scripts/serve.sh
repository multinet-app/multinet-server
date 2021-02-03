#!/bin/sh

python migrate.py
gunicorn multinet.app:app -t 120
