from typing import Optional

from api.providers.base import TelephonyProvider


class TwilioProvider(TelephonyProvider):
    def generate_stream_response(
        self, 
        host: str, 
        ws_path: str, 
        protocol: str = "wss",
        from_number: Optional[str] = None,
        call_sid: Optional[str] = None
    ) -> str:
        url = f"{protocol}://{host}/{ws_path}"
        
        # Build parameters for custom data
        params = ""
        if from_number:
            params += f'<Parameter name="from_number" value="{from_number}" />'
        if call_sid:
            params += f'<Parameter name="call_sid" value="{call_sid}" />'
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{url}">
            {params}
        </Stream>
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

