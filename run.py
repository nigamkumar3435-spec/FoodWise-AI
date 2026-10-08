"""
run.py — FoodWise AI server launcher.
Forces unbuffered I/O so the background runner sees the startup message.
"""
import os
import sys

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

os.environ.setdefault('SECRET_KEY', 'dev-foodwise-secret-key-2024')
os.environ.setdefault('FLASK_ENV', 'development')

from app import create_app

app = create_app()

if __name__ == '__main__':
    print(" * FoodWise AI starting...", flush=True)
    print(" * Open http://127.0.0.1:5000", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=False,
        threaded=True,
    )
