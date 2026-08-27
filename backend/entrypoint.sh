#!/bin/bash
set -e

python3 manage.py makemigrations
python3 manage.py migrate

# Executa o comando padrão (Python)
exec "$@"
