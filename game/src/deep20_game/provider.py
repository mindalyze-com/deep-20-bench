from __future__ import annotations

from typing import Protocol

from .models import GameProviderExchange, GameProviderRequest


class GameModelProvider(Protocol):
    def complete(self, request: GameProviderRequest) -> GameProviderExchange: ...
