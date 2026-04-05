import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kvui import GameManager, LogtoUI

if TYPE_CHECKING:
    from .ApClient import AoMContext


class AoMManager(GameManager):
    base_title = "Archipelago Age of Mythology: Retold Client"
    icon = str(Path(__file__).parent.parent / "aom_icon.ico")

    def build(self):
        # Wrap the normal GameManager layout in a FloatLayout so we can
        # freely position a small overlay label in the upper-right corner
        # without affecting the existing layout at all.
        main_content = super().build()

        root = FloatLayout()
        root.add_widget(main_content)  # fills entire window as normal

        # Small black-background container positioned dynamically
        # just below the tab bar (All / Hints), flush to the right edge.
        # We bind to self.tabs.y so it tracks the actual tab bar position
        # rather than relying on hardcoded pixel offsets.
        container = BoxLayout(
            size_hint=(None, None),
            size=(dp(250), dp(26)),
            padding=(dp(6), 0),
        )
        with container.canvas.before:
            Color(0, 0, 0, 1)
            self._label_bg = Rectangle(pos=container.pos, size=container.size)
        container.bind(
            pos=lambda inst, val: setattr(self._label_bg, "pos", val),
            size=lambda inst, val: setattr(self._label_bg, "size", val),
        )

        self._atlantis_label = Label(
            text="",
            markup=True,
            halign="right",
            valign="middle",
            font_size=dp(12),
        )
        self._atlantis_label.bind(size=self._atlantis_label.setter("text_size"))

        container.add_widget(self._atlantis_label)
        root.add_widget(container)

        # Bind position so the label tracks the bottom of the tab bar
        def _reposition(*args):
            container.right = root.right
            container.top   = self.tabs.y
        self.tabs.bind(pos=_reposition, size=_reposition)
        root.bind(size=_reposition)
        Clock.schedule_once(lambda dt: _reposition())

        return root

    def update_atlantis_status(self, text: str, green: bool = False) -> None:
        """
        Update the Atlantis Key status label from any thread.
        Bold yellow on black; green=True switches to bright green when unlocked.
        Uses Clock.schedule_once to safely marshal onto the Kivy main thread.
        """
        def _update(dt):
            if not text:
                self._atlantis_label.text = ""
                return
            color = "44FF44" if green else "FFD700"
            self._atlantis_label.text = f"[b][color={color}]{text}[/b]"
        Clock.schedule_once(_update)

    def on_start(self) -> None:
        logging.getLogger(__name__).addHandler(LogtoUI(self.log_panels["All"].on_log))
        logger = logging.getLogger("Client")
        logger.info("Age of Mythology: Retold client commands:")
        logger.info("  /status    — show connection info and Atlantis Key progress")
        logger.info("  /scenarios — list beaten, in-progress, and untouched scenarios")

    @staticmethod
    def start_ap_ui(ctx: "AoMContext") -> None:
        ctx.ui = AoMManager(ctx)
        ctx.ui_task = asyncio.create_task(ctx.ui.async_run(), name="UI")