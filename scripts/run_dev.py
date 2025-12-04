#!/usr/bin/env python
import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


load_dotenv(PROJECT_ROOT / ".env")


def start_ngrok(port: int):
    try:
        from pyngrok import conf, ngrok
    except ImportError:
        print("⚠ pyngrok not installed")
        return None

    token = os.getenv("NGROK_AUTHTOKEN")
    if token:
        conf.get_default().auth_token = token

    tunnel = ngrok.connect(port, "http")
    url = tunnel.public_url

    print(f"\n🌐 Public URL: {url}")
    print(f"📋 Twilio webhook: {url}/api/incoming-call/ (POST)\n")
    return url


def main():
    parser = argparse.ArgumentParser(description="Run DriveDial dev server")
    parser.add_argument("--port", "-p", type=int, default=8000)
    parser.add_argument("--no-ngrok", action="store_true")
    args = parser.parse_args()

    print("\n🚗 DriveDial - AI Voice Sales Agent\n")

    if not args.no_ngrok:
        start_ngrok(args.port)

    os.chdir(PROJECT_ROOT)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        subprocess.run([
            sys.executable, "-m", "daphne",
            "-b", "0.0.0.0", "-p", str(args.port),
            "config.asgi:application",
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        try:
            from pyngrok import ngrok
            ngrok.kill()
        except:
            pass


if __name__ == "__main__":
    main()
