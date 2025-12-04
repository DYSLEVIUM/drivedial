from api.providers.base import TelephonyProvider


class TwilioProvider(TelephonyProvider):
    def generate_stream_response(self, host: str, ws_path: str, protocol: str = "wss") -> str:
        url = f"{protocol}://{host}/{ws_path}"
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{url}" />
    </Connect>
</Response>'''

    def generate_say_response(self, message: str, voice: str = "Polly.Aditi") -> str:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}">{message}</Say>
</Response>'''

    def generate_hangup_response(self) -> str:
        return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Hangup />
</Response>'''

