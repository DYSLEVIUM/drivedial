import os
import sys
from typing import Optional

from django.core.management.base import BaseCommand, CommandError

try:
    from pyngrok import conf, ngrok
    HAS_NGROK = True
except ImportError:
    HAS_NGROK = False


class Command(BaseCommand):
    help = "Start Daphne server with ngrok tunnel"

    def add_arguments(self, parser):
        parser.add_argument("port", nargs="?", default="8000")
        parser.add_argument("--authtoken", type=str)
        parser.add_argument("--no-ngrok", action="store_true")

    def handle(self, *args, **options):
        port = options["port"]
        use_ngrok = not options.get("no_ngrok", False)

        if use_ngrok and not HAS_NGROK:
            raise CommandError("pyngrok not installed: pip install pyngrok")

        self.stdout.write(self.style.SUCCESS(
            "\n🚗 DriveDial Server Starting\n"))

        tunnel = None
        if use_ngrok:
            tunnel = self._start_ngrok(int(port), options.get("authtoken"))

        self._run_daphne(port, tunnel)

    def _start_ngrok(self, port: int, authtoken: Optional[str] = None):
        token = authtoken or os.getenv("NGROK_AUTHTOKEN")
        if token:
            conf.get_default().auth_token = token

        self.stdout.write("Starting ngrok tunnel...")
        tunnel = ngrok.connect(port, "http")
        url = tunnel.public_url

        self.stdout.write(self.style.SUCCESS(f"\n🌐 Public URL: {url}"))
        self.stdout.write(
            f"📋 Twilio webhook: {url}/api/incoming-call/ (POST)\n")
        return tunnel

    def _run_daphne(self, port: str, tunnel):
        from daphne.cli import CommandLineInterface

        try:
            sys.argv = ["daphne", "-b", "0.0.0.0",
                        "-p", port, "config.asgi:application"]
            CommandLineInterface().run(sys.argv[1:])
        except KeyboardInterrupt:
            self.stdout.write("\nShutting down...")
        finally:
            if tunnel:
                ngrok.disconnect(tunnel.public_url)
                ngrok.kill()
