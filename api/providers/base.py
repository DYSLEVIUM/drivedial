from abc import ABC, abstractmethod
from typing import Callable, Optional


class VoiceProvider(ABC):
    on_audio: Optional[Callable[[str], None]] = None
    on_interrupt: Optional[Callable[[], None]] = None
    on_error: Optional[Callable[[Exception], None]] = None

    def set_callbacks(
        self,
        on_audio: Optional[Callable] = None,
        on_interrupt: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> None:
        self.on_audio = on_audio
        self.on_interrupt = on_interrupt
        self.on_error = on_error

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def send_audio(self, payload: str) -> None:
        pass

    @abstractmethod
    async def listen(self) -> None:
        pass


class TelephonyProvider(ABC):
    @abstractmethod
    def generate_stream_response(self, host: str, ws_path: str) -> str:
        pass

    @abstractmethod
    def generate_say_response(self, message: str) -> str:
        pass

    @abstractmethod
    def generate_hangup_response(self) -> str:
        pass

