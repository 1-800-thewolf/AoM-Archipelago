import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from kvui import GameManager, LogtoUI

if TYPE_CHECKING:
    from .ApClient import AoMContext


class AoMManager(GameManager):
    base_title = "Archipelago Age of Mythology: Retold Client"
    icon = str(Path(__file__).parent / "aom_icon.ico")

    def on_start(self) -> None:
        logging.getLogger(__name__).addHandler(LogtoUI(self.log_panels["All"].on_log))

    def build(self):
        return super().build()

    @staticmethod
    def start_ap_ui(ctx: "AoMContext") -> None:
        ctx.ui = AoMManager(ctx)
        ctx.ui_task = asyncio.create_task(ctx.ui.async_run(), name="UI")