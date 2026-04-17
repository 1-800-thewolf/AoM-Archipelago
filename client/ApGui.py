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
        main_content = super().build()

        root = FloatLayout()
        root.add_widget(main_content)

        # Single container — 5 rows stacked vertically, same as original.
        # Two canvas rectangles are drawn: a wide one behind row 1 (Atlantis Key)
        # and a narrower one behind rows 2-5 (Gems / Shops / Traps).
        container = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(260), dp(100)),
            padding=(dp(6), 0),
        )

        with container.canvas.before:
            Color(0, 0, 0, 1)
            # Wide rectangle behind the Atlantis Key row (full width)
            self._bg_top = Rectangle()
            # Narrower rectangle behind the remaining rows
            self._bg_bot = Rectangle()

        def _update_rects(*args):
            row_h  = dp(20)
            top_w  = container.width * 0.9     # 10% narrower than container
            bot_w  = dp(142)                   # bottom rect width
            cx, cy = container.x, container.y
            ch     = container.height
            # Top rect: rightmost top_w pixels, top row only
            self._bg_top.pos  = (cx + container.width - top_w, cy + ch - row_h)
            self._bg_top.size = (top_w, row_h)
            # Bot rect: rightmost bot_w pixels, rows 2-5
            self._bg_bot.pos  = (cx + container.width - bot_w, cy)
            self._bg_bot.size = (bot_w, ch - row_h)

        container.bind(pos=_update_rects, size=_update_rects)

        def _make_label():
            lbl = Label(
                text="", markup=True, halign="right", valign="middle",
                font_size=dp(12), size_hint_y=None, height=dp(20),
            )
            lbl.bind(size=lbl.setter("text_size"))
            return lbl

        self._atlantis_label    = _make_label()
        self._gems_label        = _make_label()
        self._shops_label       = _make_label()
        self._trap_count_label  = _make_label()
        self._trap_next_label   = _make_label()

        container.add_widget(self._atlantis_label)
        container.add_widget(self._gems_label)
        container.add_widget(self._shops_label)
        container.add_widget(self._trap_count_label)
        container.add_widget(self._trap_next_label)
        root.add_widget(container)

        def _reposition(*args):
            container.right = root.right
            container.top   = self.tabs.y
        self.tabs.bind(pos=_reposition, size=_reposition)
        root.bind(size=_reposition)
        Clock.schedule_once(lambda dt: _reposition())

        return root

    def update_atlantis_status(self, text: str, green: bool = False) -> None:
        def _update(dt):
            if not text:
                self._atlantis_label.text = ""
                return
            color = "44FF44" if green else "FFD700"
            self._atlantis_label.text = f"[b][color={color}]{text}[/b]"
        Clock.schedule_once(_update)

    def update_shop_status(self, gems, shops_open) -> None:
        def _update(dt):
            if gems is None:
                self._gems_label.text  = ""
                self._shops_label.text = ""
            else:
                self._gems_label.text  = f"[b][color=44FF44]Gems: {gems}[/color][/b]"
                self._shops_label.text = f"[b][color=AAAAFF]Shops open: {shops_open}[/color][/b]"
        Clock.schedule_once(_update)

    def update_trap_status(self, queue_size: int, next_trap_name: str) -> None:
        def _update(dt):
            if queue_size <= 0:
                self._trap_count_label.text = ""
                self._trap_next_label.text  = ""
            else:
                c = "C9695F"
                self._trap_count_label.text = f"[b][color={c}]Traps in Queue: {queue_size}[/color][/b]"
                self._trap_next_label.text  = f"[b][color={c}]Next Trap: {next_trap_name}[/color][/b]"
        Clock.schedule_once(_update)

    def on_start(self) -> None:
        logging.getLogger(__name__).addHandler(LogtoUI(self.log_panels["All"].on_log))
        logger = logging.getLogger("Client")
        logger.info("Age of Mythology: Retold client commands:")
        logger.info("  /status              - show connection info and Atlantis Key progress")
        logger.info("  /scenarios (/progress) - list beaten, in-progress, and untouched scenarios")

    @staticmethod
    def start_ap_ui(ctx: "AoMContext") -> None:
        ctx.ui = AoMManager(ctx)
        ctx.ui_task = asyncio.create_task(ctx.ui.async_run(), name="UI")
