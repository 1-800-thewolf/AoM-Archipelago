# =============================================================================
# Age of Mythology Retold — Kivy GUI overlay (kvui)
# =============================================================================
#
# Augments Archipelago's standard `GameManager` window (kvui) with a 5-row
# status panel that pins to the top-right of the client view:
#   row 1: Atlantis Key / Final-section status
#   row 2: gem balance
#   row 3: shops open count
#   row 4: traps queued
#   row 5: next-trap name
#
# All updates flow through `update_atlantis_status`, `update_shop_status`,
# `update_trap_status`.  Callers (ApClient.py + GameClient.py) marshal onto
# the Kivy main thread via `Clock.schedule_once`.
#
# This file is purely cosmetic — disabling it does not break gameplay; the
# CLI client mode would still function.
# =============================================================================

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kvui import GameManager, LogtoUI


def _hex_rgba(h: str, a: float = 1.0) -> tuple:
    """Convert '#RRGGBB' / 'RRGGBB' to a Kivy (r,g,b,a) tuple in 0..1."""
    h = h.lstrip("#")
    return (int(h[0:2], 16)/255.0, int(h[2:4], 16)/255.0, int(h[4:6], 16)/255.0, a)


# =============================================================================
# Tab system — Civilizations / Scenarios / Relics all share the same
# `_WrapTabBar` widget below.  Each tab bar holds an arbitrary number of
# `_BeveledToggleButton`s laid out in a wrapping GridLayout (cols=4 by default)
# so adding more civilizations or campaigns just means adding more tabs — the
# layout grows down rather than overflowing the available width.
#
# Adding a NEW CIVILIZATION (e.g. Japanese):
#   1. Add a "Japanese" entry to `_CIV_HEADER_HEX` below with the civ's color.
#   2. Add "Japanese" to the `_CIV_ORDER` list inside `update_civs_view`.
#   3. Add "Japanese" to `_GOD_TO_CIV` / civ-id sets in rules/Rules.py and
#      __init__.py so the world-side data agrees.
#   4. (Optional) Add age-tech mapping and per-god minor-god list in
#      __init__.py + archipelago.xs so the new civ plays correctly in-game.
#   No client GUI changes beyond steps 1-2 are needed; the tab bar auto-builds
#   one sub-tab per active civ, Summary auto-includes a strength row, and
#   `_civ_items_all()` auto-collects items tagged with the new culture.
#
# Adding a NEW CAMPAIGN (e.g. Aztec):
#   1. Add the Campaign enum entry to locations/Campaigns.py with a unique
#      campaign_name and stable `id`.
#   2. Add per-campaign scenarios to locations/Scenarios.py + Locations.py.
#   3. Add the campaign.name -> RGB triple to `_CAMPAIGN_TILE_COLORS` and
#      `_RELIC_CAMPAIGN_HEX` at module / class scope.
#   4. (Optional) Add a YAML option to enable/disable the campaign.
#   The Scenarios + Relics tabs both auto-pick up the new campaign as a new
#   sub-tab; the Overview/Summary rows auto-include it.
# =============================================================================


class _BeveledToggleButton(ToggleButton):
    """ToggleButton with painted top/left highlights and bottom/right shadows
    so unpressed state looks raised and pressed state looks recessed.  Also
    supports a `locked` overlay (muted background + diagonal black slashes)
    used for campaign tabs whose section isn't yet unlocked in the seed."""

    def __init__(self, **kw):
        kw.setdefault("bold", True)
        super().__init__(**kw)
        self._base_bg = tuple(kw.get("background_color", (1, 1, 1, 1)))
        self._locked  = False
        # Suppress Kivy's built-in Button background so we can layer:
        #   canvas.before  -> our own bg rect, then slashes (stencil-clipped)
        #   canvas (main)  -> Kivy renders the text texture on top
        #   canvas.after   -> bevel highlights/shadows
        # This puts the diagonal slashes IN FRONT of the bg but BEHIND the text.
        self.background_normal = ""
        self.background_down   = ""
        self.background_disabled_normal = ""
        self.background_disabled_down   = ""
        self.background_color = (0, 0, 0, 0)
        with self.canvas.before:
            self._own_bg_col  = Color(*self._base_bg)
            self._own_bg_rect = Rectangle(pos=(0, 0), size=(0, 0))
        # Two-layer bevel: outer thick highlight/shadow + inner thin pair for depth.
        with self.canvas.after:
            self._hi_col    = Color(1, 1, 1, 0.55)
            self._hi_top    = Line(points=[0, 0, 0, 0], width=2.4)
            self._hi_left   = Line(points=[0, 0, 0, 0], width=2.4)
            self._hi2_col   = Color(1, 1, 1, 0.18)
            self._hi2_top   = Line(points=[0, 0, 0, 0], width=1.2)
            self._hi2_left  = Line(points=[0, 0, 0, 0], width=1.2)
            self._sh_col    = Color(0, 0, 0, 0.65)
            self._sh_bot    = Line(points=[0, 0, 0, 0], width=2.4)
            self._sh_right  = Line(points=[0, 0, 0, 0], width=2.4)
            self._sh2_col   = Color(0, 0, 0, 0.30)
            self._sh2_bot   = Line(points=[0, 0, 0, 0], width=1.2)
            self._sh2_right = Line(points=[0, 0, 0, 0], width=1.2)
        # Slashes go on canvas.before so the button's text texture (rendered
        # by Kivy on the default canvas) sits *above* them and stays legible.
        with self.canvas.before:
            from kivy.graphics import StencilPush, StencilUse, StencilUnUse, StencilPop
            StencilPush()
            self._slash_clip1 = Rectangle(pos=(0, 0), size=(0, 0))
            StencilUse()
            self._slash_col = Color(0, 0, 0, 0.0)  # alpha 0 = hidden by default
            self._slash_lines = [Line(points=[0, 0, 0, 0], width=dp(2.5)) for _ in range(_SLASH_COUNT)]
            StencilUnUse()
            self._slash_clip2 = Rectangle(pos=(0, 0), size=(0, 0))
            StencilPop()
        self.bind(pos=self._update_edges, size=self._update_edges, state=self._update_edges)
        self._update_edges()

    def set_locked(self, locked: bool) -> None:
        """Toggle the locked overlay: desaturate the background to grayscale
        and draw diagonal black slashes across the face."""
        self._locked = bool(locked)
        if self._locked:
            r, g, b, a = self._base_bg
            lum = 0.30 * r + 0.59 * g + 0.11 * b
            gray = lum * 0.55
            self._own_bg_col.rgba = (gray, gray, gray, a)
            self._slash_col.rgba  = (0, 0, 0, 0.9)
        else:
            self._own_bg_col.rgba = self._base_bg
            self._slash_col.rgba  = (0, 0, 0, 0.0)
        self._update_edges()

    def _update_edges(self, *_):
        x, y, w, h = self.x, self.y, self.width, self.height
        if self.state == "down":
            # Pressed/selected: invert — dark on top/left, light on bottom/right.
            self._hi_col.rgba   = (0, 0, 0, 0.65)
            self._hi2_col.rgba  = (0, 0, 0, 0.30)
            self._sh_col.rgba   = (1, 1, 1, 0.35)
            self._sh2_col.rgba  = (1, 1, 1, 0.15)
        else:
            self._hi_col.rgba   = (1, 1, 1, 0.55)
            self._hi2_col.rgba  = (1, 1, 1, 0.18)
            self._sh_col.rgba   = (0, 0, 0, 0.65)
            self._sh2_col.rgba  = (0, 0, 0, 0.30)
        # Outer edges (1 px from outside).
        self._hi_top.points    = [x,         y + h - 1.5, x + w,       y + h - 1.5]
        self._hi_left.points   = [x + 1.5,   y,           x + 1.5,     y + h]
        self._sh_bot.points    = [x,         y + 1.5,     x + w,       y + 1.5]
        self._sh_right.points  = [x + w - 1.5, y,         x + w - 1.5, y + h]
        # Inner edges (3-4 px in) for added depth.
        self._hi2_top.points   = [x + 3,     y + h - 4,   x + w - 3,   y + h - 4]
        self._hi2_left.points  = [x + 4,     y + 3,       x + 4,       y + h - 3]
        self._sh2_bot.points   = [x + 3,     y + 4,       x + w - 3,   y + 4]
        self._sh2_right.points = [x + w - 4, y + 3,       x + w - 4,   y + h - 3]
        # Own background rectangle.
        self._own_bg_rect.pos  = (x, y); self._own_bg_rect.size = (w, h)
        # Stencil clip + diagonal slashes (hidden via alpha=0 when unlocked).
        self._slash_clip1.pos  = (x, y); self._slash_clip1.size = (w, h)
        self._slash_clip2.pos  = (x, y); self._slash_clip2.size = (w, h)
        spacing  = dp(11)
        i        = 0
        x_start  = -h
        # Sweep past the right edge by `h` so diagonals whose bottom-left
        # falls in the rightmost strip still get drawn (stencil clips the
        # off-rect portion).  Without this the lower-right corner is missed.
        while x_start < w + h and i < len(self._slash_lines):
            self._slash_lines[i].points = [
                x + x_start,     y,
                x + x_start + h, y + h,
            ]
            i += 1
            x_start += spacing
        while i < len(self._slash_lines):
            self._slash_lines[i].points = [0, 0, 0, 0]
            i += 1


class _ShinyOverlay:
    """Adds a subtle 'glass card' shine to a button — two diagonal highlight
    bands, one tucked into the upper-right corner and one into the lower-left,
    drawn on `canvas.before` so the button's text renders above them.  Lines
    extend well past the button bounds; a stencil clip keeps the visible
    portion inside the rectangle.  Toggle with `set_visible(bool)`.
    """

    def __init__(self, btn, tint=(1, 1, 1)):
        from kivy.graphics import (
            StencilPush, StencilUse, StencilUnUse, StencilPop,
            Rectangle, Color, Line,
        )
        self.btn = btn
        # Band color.  Defaults to white; pass a darker grey for surfaces with
        # bright backgrounds (e.g. FotT Egyptian yellow / New Atlantis teal)
        # where a white shine washes out and is hard to see.
        self._tint = tint
        # canvas.before puts the shine BEHIND the button's text.  Order within
        # canvas.before matters — these instructions are appended after the
        # button's own bg/bevel layer, so they draw on top of the background
        # but still under the text rendered by the Button on canvas (default).
        with btn.canvas.before:
            StencilPush()
            self._clip1 = Rectangle(pos=(0, 0), size=(0, 0))
            StencilUse()
            # Two layered bands per corner: a thicker, very soft outer band
            # plus a thinner brighter inner band for a glass-edge feel.  All
            # off by default (alpha 0).
            self._col_soft   = Color(1, 1, 1, 0.0)
            self._band_ur_soft = Line(points=[0, 0, 0, 0], width=dp(10))
            self._band_ll_soft = Line(points=[0, 0, 0, 0], width=dp(10))
            self._col_bright = Color(1, 1, 1, 0.0)
            self._band_ur_brt  = Line(points=[0, 0, 0, 0], width=dp(3))
            self._band_ll_brt  = Line(points=[0, 0, 0, 0], width=dp(3))
            StencilUnUse()
            self._clip2 = Rectangle(pos=(0, 0), size=(0, 0))
            StencilPop()
        btn.bind(pos=self._update, size=self._update)
        self._update()

    def _update(self, *_):
        x, y, w, h = self.btn.x, self.btn.y, self.btn.width, self.btn.height
        self._clip1.pos = (x, y); self._clip1.size = (w, h)
        self._clip2.pos = (x, y); self._clip2.size = (w, h)

        # Both bands run anti-diagonally — slope (+1, -1), upper-left to
        # lower-right — so the shine reads distinctly from the lower-left→
        # upper-right "restricted / locked" slashes drawn elsewhere.  Each is
        # positioned to pass through its target corner; the stencil clip trims
        # anything beyond the button.

        # Lower-right band: enters above the top edge, sweeps down-right
        # through the lower-right corner, exiting along the right edge.
        lr_x0 = x + w - h * 1.2
        lr_y0 = y + h + h * 0.2
        lr_end = h * 2.0
        self._band_ur_soft.points = [
            lr_x0, lr_y0,
            lr_x0 + lr_end, lr_y0 - lr_end,
        ]
        self._band_ur_brt.points = [
            lr_x0 + dp(10), lr_y0,
            lr_x0 + dp(10) + lr_end, lr_y0 - lr_end,
        ]

        # Upper-left band: point-mirror of the lower-right band so it passes
        # through the upper-left corner and exits along the left edge.
        ul_x0 = x - h * 0.2
        ul_y0 = y + h + h * 0.2
        ul_end = h * 2.0
        self._band_ll_soft.points = [
            ul_x0, ul_y0,
            ul_x0 + ul_end, ul_y0 - ul_end,
        ]
        self._band_ll_brt.points = [
            ul_x0 + dp(10), ul_y0,
            ul_x0 + dp(10) + ul_end, ul_y0 - ul_end,
        ]

    def set_visible(self, on: bool, intensity: float = 1.0) -> None:
        r, g, b = self._tint
        if on:
            # Soft band ~22%, bright inner ~45%.  `intensity` scales both down
            # for secondary surfaces (e.g. campaign sub-tabs get a fainter shine
            # than the scenario tiles they summarize).
            self._col_soft.rgba   = (r, g, b, 0.22 * intensity)
            self._col_bright.rgba = (r, g, b, 0.45 * intensity)
        else:
            self._col_soft.rgba   = (r, g, b, 0.0)
            self._col_bright.rgba = (r, g, b, 0.0)


class _ClickThroughBox(BoxLayout):
    """BoxLayout whose touch events always propagate past it.  Used to overlay
    multi-line labels on top of a button face so each line can individually
    shorten/ellipsise — click still falls through to the button below."""
    def on_touch_down(self, touch): return False
    def on_touch_move(self, touch): return False
    def on_touch_up(self,   touch): return False


class _WrapTabBar(BoxLayout):
    """Light-weight tab system that wraps tab buttons across rows of fixed
    column count and swaps content below.  Replaces Kivy's TabbedPanel which
    only supports a single row of tabs.

    Usage:
        tb = _WrapTabBar(cols=4, btn_height=dp(44))
        tb.add_tab("Summary", (0.4,0.4,0.4,0.6), summary_widget)
        tb.add_tab("Greek",   (0.3,0.3,1.0,0.6), greek_widget)
        ...
        tb.select(0)
    """

    def __init__(self, cols: int = 4, btn_height: int = 44, **kw):
        super().__init__(orientation="vertical", spacing=4, **kw)
        self._cols       = cols
        self._btn_height = btn_height
        self._btn_group  = f"_aom_tab_{id(self)}"
        self._buttons: list = []
        self._contents: list = []

        self._btn_grid = GridLayout(cols=cols, size_hint_y=None, spacing=4)
        self._btn_grid.bind(minimum_height=self._btn_grid.setter("height"))
        self._content_holder = BoxLayout(orientation="vertical")
        self.add_widget(self._btn_grid)
        self.add_widget(self._content_holder)

    def clear_tabs(self) -> None:
        self._btn_grid.clear_widgets()
        self._content_holder.clear_widgets()
        self._buttons  = []
        self._contents = []

    def add_tab(self, text: str, rgba: tuple, content, text_color: tuple | None = None) -> int:
        idx = len(self._buttons)
        btn = _BeveledToggleButton(
            text=text, group=self._btn_group, markup=True,
            size_hint_y=None, height=self._btn_height,
            background_color=rgba, background_normal="", background_down="",
        )
        if text_color is not None:
            btn.color = text_color
        btn.bind(on_press=lambda _b, i=idx: self.select(i))
        self._btn_grid.add_widget(btn)
        self._buttons.append(btn)
        self._contents.append(content)
        return idx

    def select(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._buttons):
            return
        self._content_holder.clear_widgets()
        self._content_holder.add_widget(self._contents[idx])
        for i, b in enumerate(self._buttons):
            b.state = "down" if i == idx else "normal"

    def set_button_text(self, idx: int, text: str) -> None:
        if 0 <= idx < len(self._buttons):
            self._buttons[idx].text = text

    def set_tab_locked(self, idx: int, locked: bool) -> None:
        if 0 <= idx < len(self._buttons):
            self._buttons[idx].set_locked(locked)


# God-name -> civ-color hex used for the scenario tile god label.  Matches
# _CIV_HEADER_HEX so the god name shares the civ's color scheme.  Add new
# DLC majors here when introduced (e.g. Japanese gods -> their civ color).
_GOD_TO_CIV_COLOR: dict = {
    # Greek (blue)
    "Zeus": "4D4DFF", "Poseidon": "4D4DFF", "Hades": "4D4DFF", "Demeter": "4D4DFF",
    # Egyptian (yellow)
    "Isis": "FFE033", "Ra": "FFE033", "Set": "FFE033",
    # Norse (dark rusty brown) — RGB 100,70,70.  Darker than Aztec orange and
    # paired with a white outline below so they're easy to tell apart on the
    # Scenarios tab.
    "Odin": "644646", "Thor": "644646", "Loki": "644646", "Freyr": "644646",
    # Atlantean (teal)
    "Kronos": "00FFFF", "Oranos": "00FFFF", "Gaia": "00FFFF",
    # Chinese (pink)
    "Nuwa": "FF69B4", "Fuxi": "FF69B4", "Shennong": "FF69B4",
    # Japanese (forest green)
    "Amaterasu": "166E2D", "Tsukuyomi": "166E2D", "Susanoo": "166E2D",
    # Aztec (orange) — RGB 255,140,0
    "Huitzilopochtli": "FF8C00", "Tezcatlipoca": "FF8C00", "Quetzalcoatl": "FF8C00",
}

# RGB triples (0-1) per campaign for the Scenarios tab tiles.
# Matches the colors specified in the option spec.
_CAMPAIGN_TILE_COLORS: dict[str, tuple[float, float, float]] = {
    "FOTT_GREEK":    (0.3,   0.3,    1.0),
    "FOTT_EGYPTIAN": (1.0,   1.0,    0.0),
    "FOTT_NORSE":    (0.53,  0.31,   0.31),
    "FOTT_FINAL":    (1.0,   0.0,    0.0),
    "GOLDEN_GIFT":   (0.855, 0.65,   0.1255),
    "NEW_ATLANTIS":  (0.0,   1.0,    1.0),
}

# Campaigns whose tile/tab background is bright enough (yellow, teal) that a
# white shine washes out — these use a dark-grey shine instead for contrast.
_BRIGHT_SHINE_CAMPAIGNS = frozenset({"FOTT_EGYPTIAN", "NEW_ATLANTIS"})
_GREY_SHINE_TINT = (0.40, 0.40, 0.40)


def _shine_tint_for(campaign_name: str) -> tuple:
    """White shine by default; dark grey for bright-background campaigns."""
    return _GREY_SHINE_TINT if campaign_name in _BRIGHT_SHINE_CAMPAIGNS else (1, 1, 1)


def _e_stack_display_count(remaining: int, total: int, disp_max: int = 5) -> int:
    """How many cards to draw in a Shop E deck stack, distributing the
    reduction across the whole deck (not just at the bottom).

    Rules:
      * full deck shows up to `disp_max` cards;
      * the first purchase always drops the count by one;
      * exactly one card left shows a single card;
      * the in-between counts are spread evenly across the deck size.

    Example (total=12, disp_max=5): 12→5, 11→4, 7→3, 4→2, 1→1.
    """
    r, D = int(remaining), int(total)
    if r <= 1:
        return 1
    if r >= D:
        return max(1, min(disp_max, D))
    if D <= 2:
        return max(1, min(disp_max, r))
    # Map remaining 1..(D-1) onto display 1..(disp_max-1), rounding to nearest.
    d = 1 + round((r - 1) / (D - 2) * (disp_max - 2))
    return max(1, min(d, disp_max, r))


# Max diagonal slash lines drawn per locked tile — sized for the widest possible span.
_SLASH_COUNT = 60

if TYPE_CHECKING:
    from .ApClient import AoMContext


class AoMManager(GameManager):
    """Custom Archipelago GameManager subclass — adds the AoMR status panel
    to the standard kvui chrome.  Instantiated by `start_ap_ui` (called from
    ApClient.py once the AoMContext is ready)."""
    base_title = "Archipelago Age of Mythology: Retold Client"
    icon = str(Path(__file__).parent.parent / "aom_icon.ico")

    def build(self):
        """Kivy entry — construct the widget tree.  Wraps the base kvui
        layout in a FloatLayout so we can pin a status `BoxLayout` to the
        top-right above the chat tabs.  Returns the root widget."""
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

    def build_scenarios_tab(self) -> None:
        """Lazy-build 'Scenarios' tab. kvui modern API: `add_client_tab(title, content)`.
        Top-level kvui tab wraps an inner TabbedPanel: one sub-tab per campaign
        plus an Overview tab showing per-campaign progress at-a-glance."""
        if getattr(self, "_scenarios_tab", None) is not None:
            return
        root_box = BoxLayout(
            orientation="vertical",
            padding=(dp(6), dp(100), dp(6), dp(4)),  # top pad clears status panel
            spacing=dp(4),
        )
        tabbar = _WrapTabBar(cols=4, btn_height=dp(44))
        root_box.add_widget(tabbar)
        try:
            self.add_client_tab("Scenarios", root_box)
        except Exception as ex:
            logging.getLogger(__name__).warning(f"Could not add Scenarios tab: {ex}")
            return
        self._scenarios_tab        = root_box
        self._scenarios_tabbar     = tabbar
        self._scenarios_overview   = None
        self._campaign_subtabs: dict = {}     # camp.name -> (button_idx, short_name)
        self._campaign_grids: dict   = {}
        self._scenario_tile_widgets: dict = {}

    def update_scenarios_view(
        self,
        max_keys_on_keyrings: int,
        scenario_to_gate_id: dict,
        gate_display_names: dict,
        held_gates: set,
        campaign_unlocked_by_id: dict,
        disabled_campaign_ids: set,
        scenario_to_god: dict = None,
        scenario_check_counts: dict = None,
        scenario_in_logic: dict = None,
    ) -> None:
        """Refresh the Scenarios tab.  Safe to call repeatedly; on first call,
        builds the grid; on subsequent calls, just recolors tiles.

        Args:
            max_keys_on_keyrings:     option value (0 means option is off; tab
                still renders but tile state collapses to campaign-only).
            scenario_to_gate_id:      scenario global_number → AP item id that
                gates it (Scenario Key id when max==1, Key Ring id when max>=2).
            gate_display_names:       AP gate item id → friendly name (unused
                in render, kept for caller-side debugging).
            held_gates:               set of AP item ids the player has that
                gate scenarios (Scenario Keys and/or Key Rings).
            campaign_unlocked_by_id:  campaign.id → bool.
            disabled_campaign_ids:    campaign.id ints to omit entirely.
            scenario_to_god:          scenario global_number → major god name (optional).
            scenario_check_counts:    scenario global_number → (found, total) tuple (optional).
        """
        if scenario_to_god is None:
            scenario_to_god = {}
        if scenario_check_counts is None:
            scenario_check_counts = {}
        if scenario_in_logic is None:
            scenario_in_logic = {}

        def _update(dt):
            from ..locations.Scenarios import aomScenarioData
            from ..locations.Campaigns  import aomCampaignData

            self.build_scenarios_tab()

            if not getattr(self, "_scenario_tile_widgets", None):
                # First-time grid build.
                self._scenarios_tabbar.clear_tabs()
                self._scenario_tile_widgets = {}
                self._campaign_subtabs      = {}
                self._campaign_grids        = {}
                self._scenario_tile_shine   = {}   # global_number -> _ShinyOverlay
                self._scenarios_tab_shine   = {}   # campaign.name  -> _ShinyOverlay

                # --- Overview tab (default) ---
                ov_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
                ov_box    = BoxLayout(
                    orientation="vertical", size_hint_y=None,
                    spacing=dp(6), padding=(dp(8), dp(8), dp(8), dp(8)),
                )
                ov_box.bind(minimum_height=ov_box.setter("height"))
                ov_scroll.add_widget(ov_box)
                self._scenarios_tabbar.add_tab(
                    "Overview", (0.92, 0.92, 0.92, 0.95), ov_scroll,
                    text_color=(0, 0, 0, 1),
                )
                self._scenarios_overview = ov_box

                # Group scenarios by campaign in enum order.
                by_campaign: dict = {}
                for s in aomScenarioData:
                    by_campaign.setdefault(s.campaign, []).append(s)

                for campaign, scenarios in by_campaign.items():
                    if campaign.id in disabled_campaign_ids:
                        continue
                    _short = campaign.campaign_name.replace("Fall of the Trident", "FotT")
                    base_rgb = _CAMPAIGN_TILE_COLORS.get(campaign.name, (0.5, 0.5, 0.5))
                    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
                    section = BoxLayout(
                        orientation="vertical", size_hint_y=None,
                        spacing=dp(2), padding=(dp(6), dp(6), dp(6), dp(6)),
                    )
                    section.bind(minimum_height=section.setter("height"))
                    scroll.add_widget(section)
                    idx = self._scenarios_tabbar.add_tab(
                        _short, (base_rgb[0], base_rgb[1], base_rgb[2], 0.7), scroll,
                    )
                    self._campaign_subtabs[campaign.name] = (idx, _short, campaign.id)
                    # Faint shine on the tab itself, lit when any scenario in
                    # this campaign is in logic with checks left.
                    self._scenarios_tab_shine[campaign.name] = _ShinyOverlay(
                        self._scenarios_tabbar._buttons[idx],
                        tint=_shine_tint_for(campaign.name),
                    )

                    # 2-col wide tiles; each campaign now has its own sub-tab so
                    # there's plenty of horizontal room for full scenario names.
                    grid = GridLayout(cols=2, size_hint_y=None, spacing=dp(6))
                    grid.bind(minimum_height=grid.setter("height"))
                    self._campaign_grids[campaign.name] = (grid, campaign.campaign_name)

                    for s in scenarios:
                        tile = BoxLayout(
                            orientation="vertical",
                            size_hint_y=None, height=dp(110),
                        )
                        # Scenario name: clamped to a single line (ellipsised on
                        # overflow) so the god and check rows below it are never
                        # pushed out of the tile when the window is narrow.
                        name_lbl = Label(
                            markup=True, halign="center", valign="top",
                            shorten=True, shorten_from="right", max_lines=1,
                            size_hint_y=None, height=dp(40), font_size=dp(22),
                        )
                        name_lbl.bind(size=name_lbl.setter("text_size"))
                        god_lbl = Label(
                            markup=True, halign="center", valign="middle",
                            font_size=dp(22),
                            size_hint_y=None, height=dp(26),
                        )
                        god_lbl.bind(size=god_lbl.setter("text_size"))
                        checks_lbl = Label(
                            markup=True, halign="center", valign="middle",
                            font_size=dp(22),
                            size_hint_y=None, height=dp(26),
                        )
                        checks_lbl.bind(size=checks_lbl.setter("text_size"))
                        tile.add_widget(name_lbl)
                        tile.add_widget(god_lbl)
                        tile.add_widget(checks_lbl)

                        with tile.canvas.before:
                            bg_color   = Color(0.2, 0.2, 0.2, 1.0)
                            tile_rect  = Rectangle(pos=tile.pos, size=tile.size)
                            # Stencil-clip slashes to this tile's exact bounds so they
                            # never bleed into adjacent tiles.
                            from kivy.graphics import StencilPush, StencilUse, StencilUnUse, StencilPop
                            StencilPush()
                            clip_rect  = Rectangle(pos=tile.pos, size=tile.size)
                            StencilUse()
                            slash_col  = Color(0.5, 0.5, 0.5, 0.0)
                            slash_lines = [
                                Line(points=[0, 0, 0, 0], width=dp(3))
                                for _ in range(_SLASH_COUNT)
                            ]
                            StencilUnUse()
                            clip_rect2 = Rectangle(pos=tile.pos, size=tile.size)
                            StencilPop()

                        def _bind_tile(label=tile, rect=tile_rect, crect=clip_rect, crect2=clip_rect2, slines=slash_lines):
                            def _sync(*_a):
                                lx, ly = label.x, label.y
                                lw, lh = label.width, label.height
                                rect.pos   = (lx, ly)
                                rect.size  = (lw, lh)
                                crect.pos  = (lx, ly)
                                crect.size = (lw, lh)
                                crect2.pos  = (lx, ly)
                                crect2.size = (lw, lh)
                                # Recompute 45° diagonal slash positions.
                                # Start far enough left that a full-height diagonal
                                # beginning off-screen still enters from the left edge,
                                # covering the full width of even a very wide tile.
                                spacing = dp(22)
                                i = 0
                                x_start = -lh
                                while x_start < lw and i < len(slines):
                                    slines[i].points = [
                                        lx + x_start,      ly,
                                        lx + x_start + lh, ly + lh,
                                    ]
                                    i += 1
                                    x_start += spacing
                                # Extra passes for wide tiles: keep going past lw so the
                                # stencil clip catches every remaining slash.
                                while i < len(slines):
                                    slines[i].points = [0, 0, 0, 0]
                                    i += 1
                            label.bind(pos=_sync, size=_sync)
                        _bind_tile()

                        # Store bg_color, slash_col, and campaign name for the recolor loop.
                        self._scenario_tile_widgets[s.global_number] = (
                            tile, bg_color, slash_col, s.campaign.name,
                            name_lbl, god_lbl, checks_lbl,
                        )
                        # Glass-card shine, lit when this scenario is in logic
                        # and still has at least one missing check.
                        self._scenario_tile_shine[s.global_number] = _ShinyOverlay(
                            tile, tint=_shine_tint_for(s.campaign.name),
                        )
                        grid.add_widget(tile)

                    section.add_widget(grid)

            # Recolor every tile based on current state.
            _camp_has_shine: dict = {}   # campaign.name -> any tile shining
            for sid, (tile, color, slash_col, camp_name, name_lbl, god_lbl, checks_lbl) in self._scenario_tile_widgets.items():
                base = _CAMPAIGN_TILE_COLORS.get(camp_name, (0.5, 0.5, 0.5))
                gid = scenario_to_gate_id.get(sid)
                key_held = (gid is not None and gid in held_gates)
                # Without the scenario-key option, every scenario is treated as key-held.
                if max_keys_on_keyrings <= 0:
                    key_held = True
                from ..locations.Scenarios import aomScenarioData as _SD
                scen_obj = next((s for s in _SD if s.global_number == sid), None)
                campaign_open = bool(campaign_unlocked_by_id.get(scen_obj.campaign.id, False)) if scen_obj else False

                # Four states: key × campaign
                if key_held and campaign_open:
                    r, g, b = base; a = 1.0
                elif key_held:
                    r, g, b = base; a = 0.55
                elif campaign_open:
                    r = base[0] * 0.35; g = base[1] * 0.35; b = base[2] * 0.35; a = 1.0
                else:
                    r = g = b = 0.18; a = 1.0
                color.rgba = (r, g, b, a)

                # All checks obtained → gray the tile out (overriding the civ
                # color) so it stops drawing attention; there's nothing left to
                # do there.
                ci = scenario_check_counts.get(sid)
                all_checks_done = bool(ci) and ci[1] > 0 and ci[0] >= ci[1]
                if all_checks_done:
                    color.rgba = (0.30, 0.30, 0.30, 1.0)

                # Slashes: hidden on fully-unlocked tiles; black + high alpha when the
                # player holds the key but the campaign branch is still locked (making
                # it obvious something is blocking access); grey otherwise.
                fully_unlocked = key_held and campaign_open
                if fully_unlocked:
                    slash_col.rgba = (0.5, 0.5, 0.5, 0.0)
                elif key_held and not campaign_open:
                    slash_col.rgba = (0.0, 0.0, 0.0, 0.9)
                else:
                    slash_col.rgba = (0.5, 0.5, 0.5, 0.4)

                # Build tile text:
                #   Row 1: "[big bold num]. [small name]"  e.g. "1. Omens"
                #   Row 2: god name (italic)
                #   Row 3: check count
                # valign=top means overflow clips from the bottom, so the
                # number is never the thing that gets dropped.
                full_name = scen_obj.display_name if scen_obj else str(sid)
                _num_tok, _sep, _scen_name = full_name.partition(". ")
                # Text color: black on bright-background tiles, white elsewhere.
                # When the tile background is a bright color (FotT Egyptian /
                # FotT Final / New Atlantis), swap text to black so it stays
                # legible.  Only applies once fully unlocked — locked tiles
                # are darkened enough that white text reads fine.
                if fully_unlocked and not all_checks_done and camp_name in ("NEW_ATLANTIS", "FOTT_EGYPTIAN", "FOTT_FINAL"):
                    _c0, _c1 = "[color=000000]", "[/color]"
                    god_markup = lambda g: f"[i][color=000000]{g}[/color][/i]"
                    checks_markup = lambda s: f"[color=000000]{s}[/color]"
                else:
                    _c0, _c1 = "", ""
                    god_markup = lambda g: f"[i]{g}[/i]"
                    checks_markup = lambda s: s
                # Wide 2-col tiles fit the full scenario name; render it the
                # same size as the god/checks rows below so the tile feels balanced.
                if _sep:
                    name_line_markup = (
                        f"[b]{_c0}{_num_tok}. {_scen_name}{_c1}[/b]"
                    )
                else:
                    name_line_markup = f"[b]{_c0}{full_name}{_c1}[/b]"

                name_lbl.text = name_line_markup

                god_name = scenario_to_god.get(sid)
                if god_name:
                    # Color god name by civ.  Greek gods get a white border
                    # (blue text on white = readable on any bg).  All other
                    # civs get a black border so the brighter civ colors stay
                    # legible against light tile backgrounds.
                    _gcol = _GOD_TO_CIV_COLOR.get(god_name, "FFFFFF")
                    god_lbl.text = f"[i][color={_gcol}]{god_name}[/color][/i]"
                    god_lbl.outline_width = 2
                    # Dark text colors get a white border for legibility;
                    # bright text colors get a black border.
                    if _gcol in ("4D4DFF", "166E2D"):  # Greek / Japanese → white border
                        god_lbl.outline_color = (1, 1, 1, 1)
                    else:                              # Egyptian / Norse / Atlantean / Chinese / Aztec → black border
                        god_lbl.outline_color = (0, 0, 0, 1)
                else:
                    god_lbl.text = ""
                    god_lbl.outline_width = 0

                check_info = scenario_check_counts.get(sid)
                if check_info:
                    found, total = check_info
                    checks_lbl.text = checks_markup(f"{found}/{total} checks")
                else:
                    checks_lbl.text = ""

                # Shine: in logic (gates 1-5) AND at least one missing check.
                has_missing = bool(check_info) and check_info[0] < check_info[1]
                shine_on    = bool(scenario_in_logic.get(sid, False)) and has_missing
                shine = self._scenario_tile_shine.get(sid)
                if shine is not None:
                    shine.set_visible(shine_on)
                if shine_on:
                    _camp_has_shine[camp_name] = True

            # Faint shine on each campaign sub-tab that contains a shining
            # scenario — half-strength so the tile-level cue stays dominant.
            for cn, tab_shine in getattr(self, "_scenarios_tab_shine", {}).items():
                tab_shine.set_visible(bool(_camp_has_shine.get(cn, False)), intensity=0.6)

            # --- Per-campaign progress: tab titles + Overview tab ----------
            from ..locations.Scenarios import aomScenarioData as _SD2
            camp_totals: dict = {}   # camp.name -> [found_checks, total_checks, beaten, scen_count, display_name]
            for s in _SD2:
                cn = s.campaign.name
                if s.campaign.id in disabled_campaign_ids:
                    continue
                if cn not in camp_totals:
                    camp_totals[cn] = [0, 0, 0, 0, s.campaign.campaign_name]
                t = camp_totals[cn]
                ci = scenario_check_counts.get(s.global_number)
                if ci:
                    t[0] += ci[0]
                    t[1] += ci[1]
                    if ci[1] > 0 and ci[0] >= ci[1]:
                        t[2] += 1
                t[3] += 1

            # Update sub-tab titles with % + lock state.
            for cn, (idx, short_name, camp_id) in self._campaign_subtabs.items():
                t = camp_totals.get(cn)
                if t and t[1] > 0:
                    pct = t[0] * 100 // t[1]
                    self._scenarios_tabbar.set_button_text(idx, f"{short_name}  {pct}%")
                elif t:
                    self._scenarios_tabbar.set_button_text(idx, f"{short_name}  0%")
                # Mute + slash the tab if the campaign isn't unlocked yet.
                locked = not bool(campaign_unlocked_by_id.get(camp_id, False))
                self._scenarios_tabbar.set_tab_locked(idx, locked)
                # Gray out the tab when every check in this campaign is found.
                all_found = bool(t) and t[1] > 0 and t[0] >= t[1]
                if 0 <= idx < len(self._scenarios_tabbar._buttons):
                    tab_btn = self._scenarios_tabbar._buttons[idx]
                    if all_found:
                        new_base = (0.35, 0.35, 0.35, 0.7)
                    else:
                        base_rgb = _CAMPAIGN_TILE_COLORS.get(cn, (0.5, 0.5, 0.5))
                        new_base = (base_rgb[0], base_rgb[1], base_rgb[2], 0.7)
                    tab_btn._base_bg = new_base
                    if not tab_btn._locked:
                        tab_btn._own_bg_col.rgba = new_base

            # Default to Overview on first build.
            if self._scenarios_tabbar._buttons and \
               all(b.state == "normal" for b in self._scenarios_tabbar._buttons):
                self._scenarios_tabbar.select(0)

            # Populate Overview tab.
            ov = self._scenarios_overview
            if ov is not None:
                ov.clear_widgets()
                ov.add_widget(Label(
                    text="[b]Campaign Progress[/b]",
                    markup=True, halign="center", valign="middle",
                    size_hint_y=None, height=dp(40), font_size=dp(22),
                ))
                _tf = sum(t[0] for t in camp_totals.values())
                _tt = sum(t[1] for t in camp_totals.values())
                _tp = (_tf * 100 // _tt) if _tt > 0 else 0
                _tb = sum(t[2] for t in camp_totals.values())
                _ts = sum(t[3] for t in camp_totals.values())
                _ov_row = BoxLayout(
                    orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8),
                )
                _ovl = Label(text="[b]Overall[/b]", markup=True, halign="left",
                              valign="middle", size_hint_x=0.28)
                _ovl.bind(size=_ovl.setter("text_size"))
                _ov_row.add_widget(_ovl)
                _ov_row.add_widget(ProgressBar(max=100, value=_tp, size_hint_x=0.52))
                _ovp = Label(
                    text=f"{_tf}/{_tt} checks  •  {_tb}/{_ts} beaten  ({_tp}%)",
                    halign="right", valign="middle", size_hint_x=0.20,
                )
                _ovp.bind(size=_ovp.setter("text_size"))
                _ov_row.add_widget(_ovp)
                ov.add_widget(_ov_row)

                _sep = Label(
                    text="[color=303030]" + ("─" * 80) + "[/color]",
                    markup=True, halign="left", valign="middle",
                    size_hint_y=None, height=dp(12), font_size=dp(10),
                )
                _sep.bind(size=_sep.setter("text_size"))
                ov.add_widget(_sep)

                for cn, t in camp_totals.items():
                    found, tot, beaten, scen_n, disp = t
                    pct = (found * 100 // tot) if tot > 0 else 0
                    base = _CAMPAIGN_TILE_COLORS.get(cn, (0.7, 0.7, 0.7))
                    hex_col = "{:02X}{:02X}{:02X}".format(
                        int(base[0]*255), int(base[1]*255), int(base[2]*255),
                    )
                    row = BoxLayout(
                        orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8),
                    )
                    _nm = Label(
                        text=f"[b][color={hex_col}]{disp}[/color][/b]",
                        markup=True, halign="left", valign="middle", size_hint_x=0.28,
                    )
                    _nm.bind(size=_nm.setter("text_size"))
                    row.add_widget(_nm)
                    row.add_widget(ProgressBar(max=100, value=pct, size_hint_x=0.52))
                    _pl = Label(
                        text=f"{found}/{tot} checks  •  {beaten}/{scen_n} beaten",
                        halign="right", valign="middle", size_hint_x=0.20,
                    )
                    _pl.bind(size=_pl.setter("text_size"))
                    row.add_widget(_pl)
                    ov.add_widget(row)

        Clock.schedule_once(_update)

    def update_atlantis_status(self, text: str, green: bool = False) -> None:
        """Update the row-1 status label.

        Args:
            text:  The status string (or "" to hide).
            green: If True, render in bright green (unlocked / open state).
                    Otherwise gold (in-progress / neutral).

        Marshals onto the Kivy main thread via Clock.schedule_once so async
        AP code can call this safely.

        Caller: `_update_atlantis_ui` in ApClient.py.
        """
        def _update(dt):
            if not text:
                self._atlantis_label.text = ""
                return
            color = "44FF44" if green else "FFD700"
            self._atlantis_label.text = f"[b][color={color}]{text}[/b]"
        Clock.schedule_once(_update)

    def update_shop_status(self, gems, shops_open) -> None:
        """Update gems / shops-open rows.

        Args:
            gems:       Current gem balance, or None to hide both rows
                        (used when gem_shop is disabled).
            shops_open: Number of shop tiers currently unlocked (1-4).
        """
        def _update(dt):
            if gems is None:
                self._gems_label.text  = ""
                self._shops_label.text = ""
            else:
                self._gems_label.text  = f"[b][color=44FF44]Gems: {gems}[/color][/b]"
                self._shops_label.text = f"[b][color=AAAAFF]Shops open: {shops_open}[/color][/b]"
        Clock.schedule_once(_update)

    def update_trap_status(self, queue_size: int, next_trap_name: str) -> None:
        """Update trap-queue display.  Hides both rows when queue is empty.

        Args:
            queue_size:    Number of pending traps in `ctx.trap_queue`.
            next_trap_name: Display name of the next trap to fire.

        Caller: `_update_atlantis_ui` plus the trap-queue update path in
        `_resolve_shop_signal` / `read_new_checks`.
        """
        def _update(dt):
            if queue_size <= 0:
                self._trap_count_label.text = ""
                self._trap_next_label.text  = ""
            else:
                c = "C9695F"
                self._trap_count_label.text = f"[b][color={c}]Traps in Queue: {queue_size}[/color][/b]"
                self._trap_next_label.text  = f"[b][color={c}]Next Trap: {next_trap_name}[/color][/b]"
        Clock.schedule_once(_update)

    # -------------------------------------------------------------------------
    # Civilizations Tab
    # -------------------------------------------------------------------------
    # One section per active civ: Generic first, then Greek/Egyptian/Norse/
    # Atlantean.  Skips civs that are excluded from the seed.  Rebuilds the
    # section skeleton on first call, then only rewrites item-row content on
    # every subsequent update so layout is stable.
    # -------------------------------------------------------------------------

    _AGE_HEX   = ["737373", "33BF33", "4D8CFF", "BF4DFF"]
    _AGE_NAMES = ["Archaic", "Classical", "Heroic", "Mythic"]

    _CIV_HEADER_HEX = {
        "Generic":   "FF4444",   # red
        "Greek":     "4D4DFF",   # blue
        "Egyptian":  "FFE033",   # yellow
        "Norse":     "CC7070",   # rusty red
        "Atlantean": "00FFFF",   # teal
        "Chinese":   "FF69B4",   # pink
        "Japanese":  "166E2D",   # forest green
        "Aztec":     "FF8C00",   # orange
    }

    def build_civs_tab(self) -> None:
        """Lazy-build the Civilizations tab (called from update_civs_view).
        Sub-tabs (Summary + one per civ) are added on the first update so the
        skeleton can be torn down and rebuilt when the active-civ set changes."""
        if getattr(self, "_civs_tab", None) is not None:
            return
        # Top padding reduced from dp(100) so the global-missing banner can
        # spill into the status panel area; the banner is short enough that the
        # tab bar still aligns visually with the Scenarios tab bar below.
        root_box = BoxLayout(
            orientation="vertical",
            padding=(dp(6), dp(64), dp(6), dp(4)),
            spacing=dp(4),
        )
        # Global "items still in multiworld" banner pinned above the sub-tabs.
        gml = Label(
            text="", markup=True, halign="left", valign="middle",
            size_hint_y=None, height=dp(36), font_size=dp(22),
        )
        gml.bind(size=gml.setter("text_size"))
        root_box.add_widget(gml)

        tabbar = _WrapTabBar(cols=4, btn_height=dp(44))
        root_box.add_widget(tabbar)

        try:
            self.add_client_tab("Civilizations", root_box)
        except Exception as ex:
            logging.getLogger(__name__).warning(f"Could not add Civilizations tab: {ex}")
            return
        self._civs_tab               = root_box
        self._civs_tabbar            = tabbar
        self._civs_global_missing_lbl = gml
        self._civ_section_widgets: dict = {}
        self._civ_subtab_index: dict  = {}   # civ -> int (button index)
        self._civs_summary_box        = None

    def update_civs_view(
        self,
        received_ids: list,
        excluded_civs,
        random_major_gods: bool,
    ) -> None:
        """Refresh the Civilizations tab.

        Args:
            received_ids:      Full list of received AP item IDs (may have duplicates).
            excluded_civs:     Civs absent from this seed (their sections are omitted).
            random_major_gods: Whether Atlantean items exist in this seed.
        """
        def _update(dt):
            from ..items.Items import (
                aomItemData,
                AgeUnlock,
                UnitUnlockProgression, UnitUnlockUseful,
                MythUnitUnlockProgression, MythUnitUnlockUseful, MythUnitUnlockFiller,
                AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful, AtlanteanMythUnitUnlock,
                ChineseUnitUnlockProgression, ChineseUnitUnlockUseful, ChineseMythUnitUnlock,
                JapaneseUnitUnlockProgression, JapaneseUnitUnlockUseful, JapaneseMythUnitUnlock,
                AztecUnitUnlockProgression, AztecUnitUnlockUseful, AztecMythUnitUnlock,
                VillagerCarryCapacity,
                StartingResources, StartingResourcesLarge,
                PassiveIncome, PassiveIncomeLarge,
                RelicTrickle, RelicEffect,
                StartingArmy, StartingArmyUseful,
                UnitStatBonus,
                HeroStatBoost, HeroStatBoostFiller,
                HeroSpecialEffect, HeroActionBoost,
                ArkantosHousing,
                GenericVillagerDiscount,
                StartingEconomyTech, StartingMilitaryTech,
                StartingDockTech, StartingBuildingsTech,
                Victory, Campaign, FinalUnlock, Trap, Gem, ProgressiveShopInfo, ScenarioKey,
            )
            from collections import Counter

            self.build_civs_tab()
            if not hasattr(self, "_civs_tabbar"):
                return

            counts     = Counter(received_ids)
            received_s = set(received_ids)

            # --- Determine active civs -------------------------------------------
            _CIV_ORDER  = ["Generic", "Greek", "Egyptian", "Norse", "Atlantean", "Chinese", "Japanese", "Aztec"]
            active_civs = []
            for _civ in _CIV_ORDER:
                if _civ in ("Atlantean", "Chinese", "Japanese", "Aztec") and not random_major_gods:
                    continue
                if _civ != "Generic" and _civ in excluded_civs:
                    continue
                active_civs.append(_civ)

            # --- Item-type sets ---------------------------------------------------
            _CIV_TYPES  = (
                AgeUnlock,
                UnitUnlockProgression, UnitUnlockUseful,
                MythUnitUnlockProgression, MythUnitUnlockUseful, MythUnitUnlockFiller,
                AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful, AtlanteanMythUnitUnlock,
                ChineseUnitUnlockProgression, ChineseUnitUnlockUseful, ChineseMythUnitUnlock,
                JapaneseUnitUnlockProgression, JapaneseUnitUnlockUseful, JapaneseMythUnitUnlock,
                AztecUnitUnlockProgression, AztecUnitUnlockUseful, AztecMythUnitUnlock,
                VillagerCarryCapacity,
            )
            # Types that are never counted as "in multiworld" items for display
            _SKIP_TYPES = (Victory, Campaign, FinalUnlock, Trap, Gem, ProgressiveShopInfo, ScenarioKey)
            # Unit/myth training unlocks — shown with checkmarks
            _UNIT_TYPES = (UnitUnlockProgression, UnitUnlockUseful,
                           AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful,
                           ChineseUnitUnlockProgression, ChineseUnitUnlockUseful,
                           JapaneseUnitUnlockProgression, JapaneseUnitUnlockUseful,
                           AztecUnitUnlockProgression, AztecUnitUnlockUseful)
            _MYTH_TYPES = (MythUnitUnlockProgression, MythUnitUnlockUseful,
                           MythUnitUnlockFiller, AtlanteanMythUnitUnlock,
                           ChineseMythUnitUnlock, JapaneseMythUnitUnlock, AztecMythUnitUnlock)
            # Misc: civ-specific but not unit/myth/age — shown only when received
            _MISC_TYPES = (VillagerCarryCapacity,)

            def _item_culture(item):
                t = item.type
                if isinstance(t, _CIV_TYPES):
                    c = getattr(t, "culture", None)
                    if c:
                        return c
                    un = getattr(t, "unit_name", "")
                    for _c in ("Greek", "Egyptian", "Norse", "Atlantean", "Chinese", "Japanese", "Aztec"):
                        if _c in un:
                            return _c
                return None

            def _is_generic(item):
                return (
                    not isinstance(item.type, _CIV_TYPES)
                    and not isinstance(item.type, _SKIP_TYPES)
                )

            def _get_age_item(culture):
                return next(
                    (it for it in aomItemData
                     if isinstance(it.type, AgeUnlock)
                     and getattr(it.type, "culture", None) == culture),
                    None,
                )

            def _civ_items_all(culture):
                """All non-AgeUnlock items that belong to `culture`."""
                return [
                    it for it in aomItemData
                    if not isinstance(it.type, AgeUnlock)
                    and _item_culture(it) == culture
                ]

            def _generic_items_all():
                return [it for it in aomItemData if _is_generic(it)]

            def _age_markup(age_count):
                """Four coloured age badges; past ages bright, future ages dim."""
                parts = []
                for i in range(4):
                    name  = self._AGE_NAMES[i]
                    hx    = self._AGE_HEX[i]
                    if i <= age_count:
                        parts.append(f"[b][color={hx}] {name} [/color][/b]")
                    else:
                        parts.append(f"[color=444444] {name} [/color]")
                return "  ".join(parts)

            # --- Compute global missing count (no traps, no skip types) ----------
            # Count every non-skip, non-trap catalog item that belongs to an
            # active civ (or is generic), then subtract what's been received.
            all_countable = [
                it for it in aomItemData
                if not isinstance(it.type, _SKIP_TYPES)
                and (
                    _is_generic(it)
                    or _item_culture(it) in active_civs
                    or isinstance(it.type, AgeUnlock)
                )
            ]
            global_in_seed  = len(all_countable)
            global_received = sum(1 for it in all_countable if it.id in received_s)
            global_missing  = global_in_seed - global_received

            # --- Skeleton build (once per active-civ set) ----------------------
            cached_civs = set(k for k in self._civ_section_widgets.keys() if k != "_summary_")
            if cached_civs != set(active_civs):
                self._civs_tabbar.clear_tabs()
                self._civ_section_widgets = {}
                self._civ_subtab_index    = {}
                self._civs_summary_box    = None

                # --- Summary tab (default) ---
                summary_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
                summary_box    = BoxLayout(
                    orientation="vertical", size_hint_y=None,
                    spacing=dp(6), padding=(dp(8), dp(8), dp(8), dp(8)),
                )
                summary_box.bind(minimum_height=summary_box.setter("height"))
                summary_scroll.add_widget(summary_box)
                self._civs_tabbar.add_tab("Summary", (0.35, 0.35, 0.35, 0.7), summary_scroll)
                self._civs_summary_box = summary_box
                self._civ_section_widgets["_summary_"] = {"section": summary_box}

                # --- One tab per active civ ---
                for civ in active_civs:
                    hdr_hex = self._CIV_HEADER_HEX.get(civ, "AAAAAA")
                    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
                    section = BoxLayout(
                        orientation="vertical", size_hint_y=None,
                        spacing=dp(1), padding=(dp(8), dp(8), dp(8), dp(8)),
                    )
                    section.bind(minimum_height=section.setter("height"))
                    scroll.add_widget(section)
                    idx = self._civs_tabbar.add_tab(civ, _hex_rgba(hdr_hex, 0.7), scroll)
                    self._civ_subtab_index[civ] = idx

                    header = Label(
                        text=f"[b][color={hdr_hex}]{civ}[/color][/b]",
                        markup=True, halign="left", valign="middle",
                        size_hint_y=None, height=dp(41), font_size=dp(29),
                    )
                    header.bind(size=header.setter("text_size"))
                    section.add_widget(header)

                    age_lbl = None
                    if civ != "Generic":
                        age_lbl = Label(
                            text="", markup=True, halign="left", valign="middle",
                            size_hint_y=None, height=dp(29), font_size=dp(18),
                        )
                        age_lbl.bind(size=age_lbl.setter("text_size"))
                        section.add_widget(age_lbl)

                    items_box = BoxLayout(
                        orientation="vertical", size_hint_y=None, spacing=dp(0),
                    )
                    items_box.bind(minimum_height=items_box.setter("height"))
                    section.add_widget(items_box)

                    self._civ_section_widgets[civ] = {
                        "section":   section,
                        "age_lbl":   age_lbl,
                        "items_box": items_box,
                    }

                # Default to Summary tab
                self._civs_tabbar.select(0)

            # --- Update global missing label -------------------------------------
            if self._civs_global_missing_lbl is not None:
                if global_missing > 0:
                    self._civs_global_missing_lbl.text = (
                        f"[b][color=FF8844]{global_missing} items still in multiworld[/color][/b]"
                    )
                else:
                    self._civs_global_missing_lbl.text = (
                        "[b][color=44FF44]All items received![/color][/b]"
                    )

            # --- Per-update content refresh ------------------------------------
            def _mkrow(text_markup, h=dp(23), fs=dp(16)):
                lbl = Label(
                    text=text_markup, markup=True,
                    halign="left", valign="middle",
                    size_hint_y=None, height=h, font_size=fs,
                )
                lbl.bind(size=lbl.setter("text_size"))
                return lbl

            def _subhdr(title, color="CCCCCC"):
                return _mkrow(
                    f"[b][color={color}]  {title}[/color][/b]",
                    h=dp(26), fs=dp(17),
                )

            # Checkmark rows: green tick if received, dark red X if missing
            # Missing item text is very dark (363636 ≈ 20 % darker than 444444)
            def _itemrow(display_name, has_it):
                col      = "DDFFDD" if has_it else "363636"
                icon     = "\u2714" if has_it else "\u2718"
                icon_col = "44FF44" if has_it else "5C1A1A"
                return _mkrow(
                    f"[color={icon_col}]    {icon}[/color] [color={col}]{display_name}[/color]"
                )

            # Per-civ strength for Summary tab + sub-tab titles.
            strength: dict = {}

            for civ, refs in self._civ_section_widgets.items():
                if civ == "_summary_":
                    continue
                ib      = refs["items_box"]
                age_ref = refs["age_lbl"]
                ib.clear_widgets()

                # Compute received/total for tab title + Summary bars.
                if civ == "Generic":
                    _civset = _generic_items_all()
                else:
                    _civset = _civ_items_all(civ)
                _civ_total = sum(1 for it in _civset if not isinstance(it.type, _SKIP_TYPES))
                _civ_recv  = sum(1 for it in _civset
                                  if not isinstance(it.type, _SKIP_TYPES)
                                  and counts.get(it.id, 0) > 0)
                _civ_pct   = (_civ_recv * 100 // _civ_total) if _civ_total > 0 else 0
                strength[civ] = (_civ_recv, _civ_total, _civ_pct)

                # Update sub-tab title with %.
                _idx = self._civ_subtab_index.get(civ)
                if _idx is not None:
                    self._civs_tabbar.set_button_text(_idx, f"{civ} {_civ_pct}%")

                if civ == "Generic":
                    # ---- Generic: received non-civ items grouped by category ----
                    all_gen = _generic_items_all()
                    # (group_name, types, header_hex_color)
                    _GEN_GROUPS = [
                        ("Starting Resources",  (StartingResources, StartingResourcesLarge),   "FFD24D"),
                        ("Passive Income",       (PassiveIncome, PassiveIncomeLarge),           "55DD66"),
                        ("Relic Trickles",       (RelicTrickle,),                                "55C8E6"),
                        ("Relic Effects",        (RelicEffect,),                                 "C088FF"),
                        ("Starting Army",        (StartingArmy, StartingArmyUseful),             "FF9933"),
                        ("Unit Stat Bonuses",    (UnitStatBonus,),                               "FF6F6F"),
                        ("Villager Discounts",   (GenericVillagerDiscount,),                     "B8E04D"),
                        ("Starting Techs",       (StartingEconomyTech, StartingMilitaryTech,
                                                  StartingDockTech, StartingBuildingsTech),     "4DBFFF"),
                    ]
                    for grp_name, grp_types, hdr_col in _GEN_GROUPS:
                        grp = [
                            (it, counts.get(it.id, 0)) for it in all_gen
                            if isinstance(it.type, grp_types)
                            and counts.get(it.id, 0) > 0
                        ]
                        if not grp:
                            continue
                        ib.add_widget(_subhdr(grp_name, color=hdr_col))
                        for it, n in grp:
                            sfx = f" [color=AAAAAA]x{n}[/color]" if n > 1 else ""
                            ib.add_widget(
                                _mkrow(f"[color=EEEEEE]    \u2022 {it.item_name}[/color]{sfx}")
                            )

                    # Hero Items: one sub-header per hero, Arkantos first then
                    # alphabetical.  Different gold shade so heroes stand out
                    # from category sub-headers above.
                    _HERO_TYPES = (HeroStatBoost, HeroStatBoostFiller,
                                   HeroSpecialEffect, HeroActionBoost, ArkantosHousing)
                    hero_items_all = [
                        it for it in all_gen
                        if isinstance(it.type, _HERO_TYPES)
                        and counts.get(it.id, 0) > 0
                    ]
                    if hero_items_all:
                        def _hero_name(it):
                            if isinstance(it.type, ArkantosHousing):
                                return "Kastor" if it.item_name.startswith("Kastor") else "Arkantos"
                            h = getattr(it.type, "hero", "") or ""
                            return h[:-3] if h.endswith("SPC") else h
                        def _hero_sort_key(it):
                            h = _hero_name(it)
                            return (0, it.item_name) if h == "Arkantos" else (1, h, it.item_name)
                        hero_items_all.sort(key=_hero_sort_key)
                        # Group by hero, emit subheader per hero.
                        _last_hero = None
                        _HERO_HEX = "F2C84A"   # warm gold for hero subheaders
                        for it in hero_items_all:
                            h = _hero_name(it)
                            if h != _last_hero:
                                ib.add_widget(_subhdr(h, color=_HERO_HEX))
                                _last_hero = h
                            ib.add_widget(
                                _mkrow(f"[color=EEEEEE]    \u2022 {it.item_name}[/color]")
                            )

                else:
                    # ---- Civ section: age bar, unit unlocks, myth unlocks, misc --
                    age_item  = _get_age_item(civ)
                    age_count = counts.get(age_item.id, 0) if age_item else 0
                    if age_ref is not None:
                        age_ref.text = "  " + _age_markup(min(age_count, 3))

                    all_civ = _civ_items_all(civ)

                    # Unit Unlocks — checkmark rows (show all, dim if missing)
                    unit_items = [
                        (it, counts.get(it.id, 0)) for it in all_civ
                        if isinstance(it.type, _UNIT_TYPES)
                    ]
                    if unit_items:
                        ib.add_widget(_subhdr("Can Train"))
                        for it, n in unit_items:
                            _uname = it.item_name
                            if _uname.lower().startswith("can train "):
                                _uname = _uname[len("can train "):]
                            _has_u = n > 0
                            if _has_u:
                                ib.add_widget(_mkrow(
                                    f"[color=44FF44]    \u2714[/color] [b][color=DDFFDD]{_uname}[/color][/b]"
                                ))
                            else:
                                ib.add_widget(_mkrow(
                                    f"        [color=363636]{_uname}[/color]"
                                ))

                    # Myth Units: each age tier is a single checkmark row (no sub-bullets)
                    for age_name, age_hex in zip(
                        ["Classical", "Heroic", "Mythic"],
                        [self._AGE_HEX[1], self._AGE_HEX[2], self._AGE_HEX[3]],
                    ):
                        myth_age = [
                            (it, counts.get(it.id, 0)) for it in all_civ
                            if isinstance(it.type, _MYTH_TYPES)
                            and getattr(it.type, "age", None) == age_name
                        ]
                        if not myth_age:
                            continue
                        any_received = any(n > 0 for _, n in myth_age)
                        _myth_lbl_col = self._CIV_HEADER_HEX.get(civ, "CCCCCC") if any_received else "363636"
                        if any_received:
                            ib.add_widget(_mkrow(
                                f"[color=44FF44]    \u2714[/color]"
                                f" [b][color={_myth_lbl_col}]{age_name} Myth Units[/color][/b]"
                            ))
                        else:
                            ib.add_widget(_mkrow(
                                f"        [color={_myth_lbl_col}]{age_name} Myth Units[/color]"
                            ))

                    # Misc — civ-specific items that aren't unit/myth unlocks.
                    # Only show received items; omit the section entirely if none.
                    misc_received = [
                        it for it in all_civ
                        if isinstance(it.type, _MISC_TYPES)
                        and counts.get(it.id, 0) > 0
                    ]
                    if misc_received:
                        ib.add_widget(_subhdr("Misc"))
                        for it in misc_received:
                            ib.add_widget(
                                _mkrow(f"[color=EEEEEE]    \u2022 {it.item_name}[/color]")
                            )

            # --- Summary sub-tab: per-civ strength bars + overall ----------
            sb = self._civs_summary_box
            if sb is not None:
                sb.clear_widgets()
                sb.add_widget(Label(
                    text="[b]Civilization Strength[/b]",
                    markup=True, halign="center", valign="middle",
                    size_hint_y=None, height=dp(40), font_size=dp(22),
                ))
                # Overall = sum across civs.
                _tot_recv = sum(s[0] for s in strength.values())
                _tot_all  = sum(s[1] for s in strength.values())
                _tot_pct  = (_tot_recv * 100 // _tot_all) if _tot_all > 0 else 0
                _overall = BoxLayout(
                    orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8),
                )
                _ovl_lbl = Label(
                    text="[b]Overall[/b]", markup=True, halign="left", valign="middle",
                    size_hint_x=0.28,
                )
                _ovl_lbl.bind(size=_ovl_lbl.setter("text_size"))
                _overall.add_widget(_ovl_lbl)
                _overall.add_widget(ProgressBar(max=100, value=_tot_pct, size_hint_x=0.52))
                _ovl_pct = Label(
                    text=f"{_tot_recv}/{_tot_all}  ({_tot_pct}%)",
                    halign="right", valign="middle", size_hint_x=0.20,
                )
                _ovl_pct.bind(size=_ovl_pct.setter("text_size"))
                _overall.add_widget(_ovl_pct)
                sb.add_widget(_overall)

                # Thin separator.
                _sep = Label(
                    text="[color=303030]" + ("\u2500" * 80) + "[/color]",
                    markup=True, halign="left", valign="middle",
                    size_hint_y=None, height=dp(12), font_size=dp(10),
                )
                _sep.bind(size=_sep.setter("text_size"))
                sb.add_widget(_sep)

                for civ in active_civs:
                    recv, tot, pct = strength.get(civ, (0, 0, 0))
                    hdr_hex = self._CIV_HEADER_HEX.get(civ, "AAAAAA")

                    # Compute reachable-age and trainable-unit count for this civ.
                    # age_count caps at 3 (Mythic).  Trainable units = received
                    # UnitUnlock items (both regular and Atlantean variants).
                    if civ == "Generic":
                        # No age / trainable concept for Generic — skip extra rows.
                        _age_idx     = -1
                        _train_count = -1
                    else:
                        _aitem = _get_age_item(civ)
                        _age_idx = min(counts.get(_aitem.id, 0), 3) if _aitem else 0
                        _train_count = sum(
                            1 for it in _civ_items_all(civ)
                            if isinstance(it.type, _UNIT_TYPES)
                            and counts.get(it.id, 0) > 0
                        )

                    # Main row: name + bar + counts.
                    row = BoxLayout(
                        orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8),
                    )
                    _name = Label(
                        text=f"[b][color={hdr_hex}]{civ}[/color][/b]",
                        markup=True, halign="left", valign="middle", size_hint_x=0.28,
                    )
                    _name.bind(size=_name.setter("text_size"))
                    row.add_widget(_name)
                    row.add_widget(ProgressBar(max=100, value=pct, size_hint_x=0.52))
                    _pct_lbl = Label(
                        text=f"{recv}/{tot}  ({pct}%)",
                        halign="right", valign="middle", size_hint_x=0.20,
                    )
                    _pct_lbl.bind(size=_pct_lbl.setter("text_size"))
                    row.add_widget(_pct_lbl)
                    sb.add_widget(row)

                    # Indented age + trainable rows.
                    if _age_idx >= 0:
                        _age_name = self._AGE_NAMES[_age_idx]
                        _age_hex  = self._AGE_HEX[_age_idx]
                        age_row = Label(
                            text=f"      [b][color={_age_hex}]{_age_name} Age[/color][/b]",
                            markup=True, halign="left", valign="middle",
                            size_hint_y=None, height=dp(22), font_size=dp(15),
                        )
                        age_row.bind(size=age_row.setter("text_size"))
                        sb.add_widget(age_row)

                        train_row = Label(
                            text=f"      [color=DDDDDD]{_train_count} Trainable Unit"
                                 f"{'' if _train_count == 1 else 's'}[/color]",
                            markup=True, halign="left", valign="middle",
                            size_hint_y=None, height=dp(22), font_size=dp(15),
                        )
                        train_row.bind(size=train_row.setter("text_size"))
                        sb.add_widget(train_row)

                    # Small gap between civ entries.
                    _gap = Label(text="", size_hint_y=None, height=dp(6))
                    sb.add_widget(_gap)

                # Re-render Summary as 2-up grid (overwrites the per-civ rows
                # written above so we keep one canonical layout path).  Done as
                # a clear + rebuild so existing strength/_age_idx logic above
                # still computes for the per-civ tabs.
                self._build_summary_grid(sb, strength, active_civs, counts,
                                          _get_age_item, _civ_items_all,
                                          _UNIT_TYPES, _MYTH_TYPES)

        Clock.schedule_once(_update)

    # -------------------------------------------------------------------------
    # Civ Summary grid builder
    # -------------------------------------------------------------------------
    # Lays out the Summary sub-tab as a 2-column grid of cells, one cell per
    # civ + an "Overall" cell (top-left) and a "Generic" cell (top-right).
    # Each cell shows: civ name (in civ color), max reachable age (in age
    # color), trainable unit count (human-soldier + myth-unit items), and a
    # progress bar with x/n.  When new civilizations are added to
    # `_CIV_ORDER` / `_CIV_HEADER_HEX`, this grid auto-extends — each new civ
    # becomes another cell at the bottom.
    # -------------------------------------------------------------------------
    def _build_summary_grid(self, sb, strength, active_civs, counts,
                             _get_age_item, _civ_items_all,
                             _UNIT_TYPES, _MYTH_TYPES) -> None:
        sb.clear_widgets()

        # Assemble entries: (label, hex, age_idx_or_-1, train_count_or_-1, recv, tot).
        entries: list = []
        _tot_recv = sum(s[0] for s in strength.values())
        _tot_all  = sum(s[1] for s in strength.values())
        entries.append(("Overall", "DDDDDD", -1, -1, _tot_recv, _tot_all))

        # Generic shares the top row with Overall.
        if "Generic" in strength:
            g_recv, g_tot, _ = strength["Generic"]
            entries.append((
                "Generic", self._CIV_HEADER_HEX.get("Generic", "FF4444"),
                -1, -1, g_recv, g_tot,
            ))

        for civ in active_civs:
            if civ == "Generic":
                continue
            recv, tot, _ = strength.get(civ, (0, 0, 0))
            hdr_hex = self._CIV_HEADER_HEX.get(civ, "AAAAAA")
            _aitem = _get_age_item(civ)
            _age_idx = min(counts.get(_aitem.id, 0), 3) if _aitem else 0
            # Trainable = human-soldier unlock items + myth-unit-tier unlock
            # items received.  E.g. Greek with Hoplite + Peltast + Classical/
            # Heroic/Mythic Myth Units = 5.
            _train = sum(
                1 for it in _civ_items_all(civ)
                if isinstance(it.type, _UNIT_TYPES + _MYTH_TYPES)
                and counts.get(it.id, 0) > 0
            )
            entries.append((civ, hdr_hex, _age_idx, _train, recv, tot))

        grid = GridLayout(
            cols=2, size_hint_y=None,
            spacing=(dp(24), dp(16)),
            padding=(dp(8), dp(4), dp(8), dp(4)),
        )
        grid.bind(minimum_height=grid.setter("height"))

        def _make_cell(label_text, color_hex, age_idx, train_count, recv, tot, col_idx, row_idx, last_row):
            cell = BoxLayout(
                orientation="vertical", size_hint_y=None,
                spacing=dp(2), padding=(dp(10), dp(8), dp(10), dp(10)),
            )
            cell.bind(minimum_height=cell.setter("height"))
            # Dividers: right edge for left-column cells, bottom edge for
            # non-last-row cells.  Drawn on canvas.after so they sit above the
            # cell background but below any child labels.
            with cell.canvas.after:
                _div_col = Color(0.45, 0.45, 0.45, 0.5)
                _right   = Line(points=[0, 0, 0, 0], width=1.4)
                _bottom  = Line(points=[0, 0, 0, 0], width=1.4)
            def _redraw(*_):
                pad = dp(6)
                # Right divider only on left column (col_idx == 0).
                if col_idx == 0:
                    _right.points = [
                        cell.right + dp(12), cell.y + pad,
                        cell.right + dp(12), cell.top - pad,
                    ]
                else:
                    _right.points = [0, 0, 0, 0]
                # Bottom divider on every row except the last.
                if not last_row:
                    _bottom.points = [
                        cell.x + pad,           cell.y - dp(8),
                        cell.right - pad,       cell.y - dp(8),
                    ]
                else:
                    _bottom.points = [0, 0, 0, 0]
            cell.bind(pos=_redraw, size=_redraw)
            # Initial layout pass may not yet have correct cell pos/size when
            # this binding runs; schedule a redraw on the next Clock tick so
            # divider lines land in the right place without needing a window
            # resize to trigger pos/size events.
            Clock.schedule_once(_redraw, 0)
            Clock.schedule_once(_redraw, 0.05)
            _nm = Label(
                text=f"[b][color={color_hex}]{label_text}[/color][/b]",
                markup=True, halign="left", valign="middle",
                size_hint_y=None, height=dp(28), font_size=dp(18),
            )
            _nm.bind(size=_nm.setter("text_size"))
            cell.add_widget(_nm)
            if age_idx >= 0:
                _ahex  = self._AGE_HEX[age_idx]
                _aname = self._AGE_NAMES[age_idx]
                _age = Label(
                    text=f"[b][color={_ahex}]{_aname} Age[/color][/b]",
                    markup=True, halign="left", valign="middle",
                    size_hint_y=None, height=dp(22), font_size=dp(15),
                )
                _age.bind(size=_age.setter("text_size"))
                cell.add_widget(_age)
            if train_count >= 0:
                _tr = Label(
                    text=f"[color=DDDDDD]{train_count} Trainable Unit"
                         f"{'' if train_count == 1 else 's'}[/color]",
                    markup=True, halign="left", valign="middle",
                    size_hint_y=None, height=dp(22), font_size=dp(15),
                )
                _tr.bind(size=_tr.setter("text_size"))
                cell.add_widget(_tr)
            bar_row = BoxLayout(
                orientation="horizontal", size_hint_y=None,
                height=dp(22), spacing=dp(6),
            )
            bar_row.add_widget(ProgressBar(
                max=tot if tot > 0 else 1, value=recv, size_hint_x=0.65,
            ))
            _cnt = Label(
                text=f"{recv}/{tot}", halign="right", valign="middle",
                size_hint_x=0.35, font_size=dp(14),
            )
            _cnt.bind(size=_cnt.setter("text_size"))
            bar_row.add_widget(_cnt)
            cell.add_widget(bar_row)
            return cell

        # Determine the last row index for the "no bottom divider" rule.
        n_cells   = len(entries)
        n_rows    = (n_cells + 1) // 2
        for i, entry in enumerate(entries):
            col_idx  = i % 2
            row_idx  = i // 2
            last_row = (row_idx == n_rows - 1)
            grid.add_widget(_make_cell(*entry, col_idx, row_idx, last_row))
        if n_cells % 2 == 1:
            # Pad with an empty placeholder so the bottom row stays balanced.
            grid.add_widget(BoxLayout(size_hint_y=None, height=dp(1)))
        sb.add_widget(grid)

    # -------------------------------------------------------------------------
    # Relics Tab
    # -------------------------------------------------------------------------

    _RELIC_CAMPAIGN_HEX: dict = {
        "FOTT_GREEK":    "4D4DFF",
        "FOTT_EGYPTIAN": "FFFF00",
        "FOTT_NORSE":    "CC7070",
        "FOTT_FINAL":    "FF2222",
        "GOLDEN_GIFT":   "DAA520",
        "NEW_ATLANTIS":  "00FFFF",
    }

    def build_relics_tab(self) -> None:
        """Eagerly build the Relics tab.  Always called from on_start() so the
        tab exists in the nav bar from launch.  Content is populated by
        update_relics_view() once slot_data is received.

        Layout mirrors the Scenarios tab: a _WrapTabBar of campaign sub-tabs
        (color-coded with _RELIC_CAMPAIGN_HEX) sits at the top, each tab
        contains a ScrollView listing every relic location for that campaign.
        Adding a new campaign just means adding it to _RELIC_CAMPAIGN_HEX and
        ensuring SCENARIO_TO_LOCATIONS / aomCampaignData expose its scenarios."""
        if getattr(self, "_relics_tab", None) is not None:
            return
        root_box = BoxLayout(
            orientation="vertical",
            padding=(dp(6), dp(100), dp(6), dp(4)),  # top pad clears status panel
            spacing=dp(4),
        )
        # Placeholder shown before slot_data arrives or when relicsanity is off
        placeholder = Label(
            text="[color=666666]Relicsanity is not enabled for this seed.[/color]",
            markup=True, halign="left", valign="top",
            size_hint_y=None, height=dp(40), font_size=dp(18),
        )
        placeholder.bind(size=placeholder.setter("text_size"))
        root_box.add_widget(placeholder)

        tabbar = _WrapTabBar(cols=4, btn_height=dp(44))
        root_box.add_widget(tabbar)

        try:
            self.add_client_tab("Relics", root_box)
        except Exception as ex:
            logging.getLogger(__name__).warning(f"Could not add Relics tab: {ex}")
            return
        self._relics_tab         = root_box
        self._relics_tabbar      = tabbar
        self._relics_placeholder = placeholder
        # loc_id -> Label widget so we can update only the text on refresh
        self._relic_row_widgets: dict = {}
        # campaign.name -> (tab_index, campaign.id) for lock-state updates.
        self._relic_campaign_subtabs: dict = {}
        # campaign.name -> [loc_id, ...] for all-found gray-out detection.
        self._relic_campaign_loc_ids: dict = {}
        # campaign.name -> [(loc_id, scenario_global_number), ...] for shine.
        self._relic_campaign_loc_scen: dict = {}
        # campaign.name -> _ShinyOverlay on the relics sub-tab button.
        self._relic_tab_shine: dict = {}
        self._relics_built = False

    def update_relics_view(
        self,
        relicsanity: bool,
        checked_locs: set,
        disabled_campaign_ids: set,
        campaign_unlocked_by_id: dict = None,
        scenario_in_logic: dict = None,
    ) -> None:
        """Refresh the Relics tab.

        Only builds the tab when relicsanity is True.  Safe to call every
        update; on first call it constructs the full skeleton, on subsequent
        calls it only updates the checkmark state of each row.

        Args:
            relicsanity:           Whether the relicsanity option is on.
            checked_locs:          Set of location IDs the player has checked.
            disabled_campaign_ids: Campaign IDs excluded from this seed.
        """
        if scenario_in_logic is None:
            scenario_in_logic = {}

        def _update(dt):
            # When relicsanity is off keep the placeholder; do nothing else.
            if not relicsanity:
                return
            # Relicsanity is on: hide the placeholder if it is still there.
            if hasattr(self, "_relics_placeholder") and self._relics_placeholder.parent:
                self._relics_tab.remove_widget(self._relics_placeholder)

            from ..locations.Locations import (
                aomLocationData, aomLocationType, SCENARIO_TO_LOCATIONS,
            )
            from ..locations.Scenarios import aomScenarioData
            from ..locations.Campaigns import aomCampaignData

            self.build_relics_tab()
            if not hasattr(self, "_relics_tabbar"):
                return

            # ---- Build skeleton once ----------------------------------------
            if not self._relics_built:
                self._relics_built = True
                self._relic_row_widgets = {}
                self._relics_tabbar.clear_tabs()

                # Collect all RELIC locations, grouped by campaign then scenario.
                # Preserve the natural enum order throughout.
                by_campaign: dict = {}
                for scenario, locs in SCENARIO_TO_LOCATIONS.items():
                    relic_locs = [l for l in locs if l.type == aomLocationType.RELIC]
                    if not relic_locs:
                        continue
                    campaign = scenario.campaign
                    by_campaign.setdefault(campaign, []).append((scenario, relic_locs))

                for campaign, scenario_groups in by_campaign.items():
                    if campaign.id in disabled_campaign_ids:
                        continue
                    camp_hex = self._RELIC_CAMPAIGN_HEX.get(campaign.name, "AAAAAA")
                    _short = campaign.campaign_name.replace("Fall of the Trident", "FotT")

                    # Per-campaign ScrollView + content box.
                    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
                    content = BoxLayout(
                        orientation="vertical", size_hint_y=None,
                        spacing=dp(2), padding=(dp(6), dp(6), dp(6), dp(6)),
                    )
                    content.bind(minimum_height=content.setter("height"))
                    scroll.add_widget(content)
                    _ridx = self._relics_tabbar.add_tab(_short, _hex_rgba(camp_hex, 0.7), scroll)
                    self._relic_campaign_subtabs[campaign.name] = (_ridx, campaign.id)
                    self._relic_campaign_loc_ids[campaign.name] = []
                    self._relic_campaign_loc_scen[campaign.name] = []
                    # Faint shine on the sub-tab, lit when an in-logic relic
                    # check is still available in this campaign.
                    self._relic_tab_shine[campaign.name] = _ShinyOverlay(
                        self._relics_tabbar._buttons[_ridx],
                        tint=_shine_tint_for(campaign.name),
                    )

                    for scenario, relic_locs in scenario_groups:
                        scen_lbl = Label(
                            text=f"[b][color={camp_hex}]{scenario.display_name}[/color][/b]",
                            markup=True, halign="left", valign="middle",
                            size_hint_y=None, height=dp(28), font_size=dp(18),
                        )
                        scen_lbl.bind(size=scen_lbl.setter("text_size"))
                        content.add_widget(scen_lbl)

                        for loc in relic_locs:
                            row_lbl = Label(
                                text="", markup=True,
                                halign="left", valign="middle",
                                size_hint_y=None, height=dp(23), font_size=dp(16),
                            )
                            row_lbl.bind(size=row_lbl.setter("text_size"))
                            content.add_widget(row_lbl)
                            self._relic_row_widgets[loc.id] = (row_lbl, loc.location_name)
                            self._relic_campaign_loc_ids[campaign.name].append(loc.id)
                            self._relic_campaign_loc_scen[campaign.name].append(
                                (loc.id, scenario.global_number)
                            )

                        sep = Label(
                            text="[color=252525]" + ("\u2500" * 80) + "[/color]",
                            markup=True, halign="left", valign="middle",
                            size_hint_y=None, height=dp(10), font_size=dp(9),
                        )
                        sep.bind(size=sep.setter("text_size"))
                        content.add_widget(sep)

                # Hide the placeholder once we have tabs.
                if hasattr(self, "_relics_placeholder") and self._relics_placeholder.parent:
                    self._relics_tab.remove_widget(self._relics_placeholder)
                # Default to first campaign tab.
                if self._relics_tabbar._buttons:
                    self._relics_tabbar.select(0)

            # ---- Update campaign-tab lock state on every call ----------------
            _unlock_map = campaign_unlocked_by_id or {}
            for cn, (idx, camp_id) in self._relic_campaign_subtabs.items():
                locked = not bool(_unlock_map.get(camp_id, False))
                self._relics_tabbar.set_tab_locked(idx, locked)
                # Gray out the tab when every relic in this campaign is checked.
                camp_loc_ids = self._relic_campaign_loc_ids.get(cn, [])
                all_found = bool(camp_loc_ids) and all(lid in checked_locs for lid in camp_loc_ids)
                if 0 <= idx < len(self._relics_tabbar._buttons):
                    tab_btn = self._relics_tabbar._buttons[idx]
                    if all_found:
                        new_base = (0.35, 0.35, 0.35, 0.7)
                    else:
                        camp_hex = self._RELIC_CAMPAIGN_HEX.get(cn, "AAAAAA")
                        new_base = _hex_rgba(camp_hex, 0.7)
                    tab_btn._base_bg = new_base
                    if not tab_btn._locked:
                        tab_btn._own_bg_col.rgba = new_base
                # Shine: an in-logic relic check is still available in this campaign.
                tab_shine = self._relic_tab_shine.get(cn)
                if tab_shine is not None:
                    shine_on = any(
                        (lid not in checked_locs) and bool(scenario_in_logic.get(scen, False))
                        for lid, scen in self._relic_campaign_loc_scen.get(cn, [])
                    )
                    tab_shine.set_visible(shine_on, intensity=0.6)

            # ---- Update checkmark state on every call -----------------------
            for loc_id, (row_lbl, loc_name) in self._relic_row_widgets.items():
                checked  = loc_id in checked_locs
                if checked:
                    # Collected: green tick, gray text (still legible).
                    row_lbl.text = (
                        f"[color=55AA55]    \u2714[/color]"
                        f" [color=4d4d4d]{loc_name}[/color]"
                    )
                else:
                    # Uncollected: blank indent, bold white text, no X.
                    row_lbl.text = (
                        f"        [b][color=FFFFFF]{loc_name}[/color][/b]"
                    )

        Clock.schedule_once(_update)

    # -------------------------------------------------------------------------
    # Gem Shop Tab
    # -------------------------------------------------------------------------
    # Mirrors Scenarios/Civilizations/Relics layout: one sub-tab per shop tier
    # (A-D, plus E when present in slot_data).  Each sub-tab is a grid of
    # buttons, one per shop slot.  Buttons show:
    #   - Slot id (e.g. "A_ITEM_3")
    #   - Item / hint label (obfuscated until enough Progressive Shop Info
    #     items have been received for that tier)
    #   - Gem cost (currently 1 per slot)
    #   - State: Purchased / Locked / Available
    # In-game shop UI has been removed; all purchases happen here.
    # -------------------------------------------------------------------------

    # AP-conventional item classification colors.  Trap matches the trap-queue
    # color already used elsewhere in the panel; the rest follow the standard
    # Archipelago palette (light purple for progression, light blue for useful,
    # teal for filler).
    _SHOP_RARITY_HEX = {
        "trap":        "C9695F",
        "filler":      "00CCCC",
        "useful":      "6D8BE8",
        "progression": "AF99EF",
    }

    _SHOP_TIER_HEX = {
        "A": "4DBF4D",   # Marsh — green
        "B": "BFA94D",   # Desert — sand
        "C": "4D8CBF",   # Grass — blue (avoid clashing with A)
        "D": "8C4DBF",   # Hades — purple
        "E": "BF4D4D",   # Sink   — red (Phase 5)
    }
    def _make_shop_button_cell(
        self, height: int, n_rows: int, base_bg_rgba: tuple,
        font_size: int = 14,
    ):
        """Create a FloatLayout grid cell containing a _BeveledToggleButton
        (face) and N click-through Labels stacked vertically on top.  Each
        label individually shrinks/ellipsises so multi-line button text
        collapses gracefully when the window narrows.

        Returns (cell, btn, labels).  `labels[i].text` drives row i."""
        from kivy.uix.floatlayout import FloatLayout
        cell = FloatLayout(size_hint_y=None, height=dp(height))
        # `pos_hint={"x":0,"y":0}` anchors children to the FloatLayout's own
        # origin.  Without it FloatLayout leaves child.pos at the default
        # (0,0) absolute, stacking every cell's children at the window origin.
        btn = _BeveledToggleButton(
            text="", markup=True,
            size_hint=(1, 1), pos_hint={"x": 0, "y": 0},
            background_color=base_bg_rgba,
        )
        cell.add_widget(btn)
        rows = _ClickThroughBox(
            orientation="vertical",
            size_hint=(1, 1), pos_hint={"x": 0, "y": 0},
            padding=(dp(6), dp(6), dp(6), dp(6)),
        )
        labels = []
        for _ in range(n_rows):
            lbl = Label(
                text="", markup=True, halign="center", valign="middle",
                shorten=True, shorten_from="right", max_lines=1,
                font_size=dp(font_size),
            )
            lbl.bind(size=lbl.setter("text_size"))
            rows.add_widget(lbl)
            labels.append(lbl)
        cell.add_widget(rows)
        # Shine overlay starts hidden; refresh path toggles it on the obelisk
        # with the most items per tier (when the player has unlocked enough
        # Progressive Shop Info to see item counts).
        shine = _ShinyOverlay(btn)
        return cell, btn, labels, shine

    # Distinct background hue per slot kind — sub-tabs keep their tier color
    # but the buttons inside use a fixed palette so the type of purchase reads
    # at a glance regardless of which shop you're in.
    _SHOP_KIND_HEX = {
        "item":      "8C4DBF",    # purple — item obelisk
        "hint":      "4D8CBF",    # blue   — mission-hint slot
        "hint_info": "F2C84A",    # yellow — Progressive Shop Info slot
    }

    def build_gem_shop_tab(self) -> None:
        """Lazy-build 'Gem Shop' tab. Sub-tabs are added on first update_gem_shop_view
        call once slot_data is known.  Placeholder shown until then or when gem_shop
        is disabled for the seed."""
        if getattr(self, "_gem_shop_tab", None) is not None:
            return
        # Reduced top padding (was dp(100)) so the header label can spill into
        # the area previously reserved for the status panel — the header has
        # plenty of room and the status panel is narrower than the tab area.
        root_box = BoxLayout(
            orientation="vertical",
            padding=(dp(6), dp(40), dp(6), dp(4)),
            spacing=dp(6),
        )
        header = Label(
            text="", markup=True, halign="center", valign="middle",
            size_hint_y=None, height=dp(56), font_size=dp(20),
        )
        header.bind(size=header.setter("text_size"))
        root_box.add_widget(header)
        placeholder = Label(
            text="[color=666666]Gem Shop is not enabled for this seed.[/color]",
            markup=True, halign="left", valign="top",
            size_hint_y=None, height=dp(40), font_size=dp(18),
        )
        placeholder.bind(size=placeholder.setter("text_size"))
        root_box.add_widget(placeholder)

        tabbar = _WrapTabBar(cols=5, btn_height=dp(44))
        root_box.add_widget(tabbar)

        try:
            self.add_client_tab("Gem Shop", root_box)
        except Exception as ex:
            logging.getLogger(__name__).warning(f"Could not add Gem Shop tab: {ex}")
            return
        self._gem_shop_tab         = root_box
        self._gem_shop_tabbar      = tabbar
        self._gem_shop_header      = header
        self._gem_shop_placeholder = placeholder
        self._gem_shop_built       = False
        self._gem_shop_tier_subtabs: dict = {}   # tier -> (tab_idx, content_box)
        self._gem_shop_slot_buttons: dict = {}   # slot_id -> button widget

    def update_gem_shop_view(
        self,
        gem_shop_enabled: bool,
        gems_available: int,
        threshold: int,
        beaten_count: int,
        shop_item_details: dict,
        shop_hint_config: dict,
        shop_slot_order: list,
        shop_obelisk_assignments: dict,
        purchased_slots: set,
        info_level: int,
        shop_e_enabled: bool = False,
        shop_e_decks: list = None,
        on_buy_clicked=None,
        on_buy_e_card=None,
    ) -> None:
        """Refresh the Gem Shop tab.

        Args:
            gem_shop_enabled:        seed option.
            gems_available:          current gem balance (earned minus spent).
            threshold:               wins_to_open_shop value.  0 = all open.
            beaten_count:            victories already cleared this run.
            shop_item_details:       loc_id -> {player, name, cls}.
            shop_hint_config:        slot_id -> {type:"progressive_info"|"mission_hints", ...}.
            shop_slot_order:         ordered list of slot id strings, e.g. ["A_ITEM_1", ..., "A_HINT_1", ...].
            shop_obelisk_assignments: slot_id -> [loc_id, ...]  (one ITEM slot = an obelisk bundling
                                     multiple locations).
            purchased_slots:         set of slot_id strings the player has already bought.
            info_level:              global Progressive Shop Info reveal level 0..4.
                                     0 — nothing; 1 — count; 2 — +rarest class; 3 — +main recipient;
                                     4 — +rarest count.  Applied to every tier.
            on_buy_clicked:          callable(slot_id, tier_unlocked, gems_avail) invoked on click.
                                     Implementations may show lock-message dialog or do the buy.
        """
        def _update(dt):
            if not gem_shop_enabled:
                return
            self.build_gem_shop_tab()
            if not hasattr(self, "_gem_shop_tabbar"):
                return
            if hasattr(self, "_gem_shop_placeholder") and self._gem_shop_placeholder.parent:
                self._gem_shop_tab.remove_widget(self._gem_shop_placeholder)

            # Header — global gem balance only.  Per-button "Costs 1 gem"
            # badge replaces the cost-reminder line.
            hdr = getattr(self, "_gem_shop_header", None)
            if hdr is not None:
                hdr.text = (
                    f"[b][color=44FF44]Gems available: {int(gems_available)}[/color][/b]"
                )

            from collections import defaultdict
            from ..locations.Locations import TIER_ITEM_IDS

            # Skeleton build — once per session, tiers A-D only (E added in Phase 5).
            if not self._gem_shop_built:
                self._gem_shop_built          = True
                self._gem_shop_tabbar.clear_tabs()
                self._gem_shop_tier_subtabs   = {}
                self._gem_shop_slot_buttons   = {}
                self._gem_shop_slot_labels    = {}   # sid -> [Label, ...]
                self._gem_shop_slot_shine     = {}   # sid -> _ShinyOverlay

                tier_slots: dict = defaultdict(list)
                for sid in shop_slot_order:
                    tier_slots[sid.split("_", 1)[0]].append(sid)
                # Display order within each tier: PSI first (yellow Better
                # Shop Information), then ITEM slots, then mission-hint slots.
                # Shop A has no PSI button — its HINT slots are all mission
                # hints and live at the bottom.  Bucket selection consults the
                # hint config so PSI detection works regardless of slot index.
                def _slot_sort_key(sid: str) -> tuple:
                    t, _, rest = sid.partition("_")
                    is_hint = rest.startswith("HINT_")
                    try:
                        idx = int(rest.split("_")[-1])
                    except ValueError:
                        idx = 0
                    is_psi = (is_hint and
                              shop_hint_config.get(sid, {}).get("type") == "progressive_info")
                    if is_psi:
                        bucket = 0
                    elif not is_hint:
                        bucket = 1
                    else:
                        bucket = 2
                    return (bucket, idx)
                for _t in tier_slots:
                    tier_slots[_t].sort(key=_slot_sort_key)

                for tier in ("A", "B", "C", "D"):
                    if not tier_slots.get(tier):
                        continue
                    hex_col = self._SHOP_TIER_HEX.get(tier, "AAAAAA")
                    scroll  = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True,
                                          scroll_y=1.0)
                    # Force scroll position to top after Kivy lays out the
                    # content.  Without this, tiers whose content overflows the
                    # viewport sometimes end up positioned at the bottom
                    # (especially Shop A which now has 8+ buttons).
                    Clock.schedule_once(lambda _dt, s=scroll: setattr(s, "scroll_y", 1.0), 0)
                    Clock.schedule_once(lambda _dt, s=scroll: setattr(s, "scroll_y", 1.0), 0.05)
                    content = BoxLayout(
                        orientation="vertical", size_hint_y=None,
                        spacing=dp(6), padding=(dp(8), dp(8), dp(8), dp(8)),
                    )
                    content.bind(minimum_height=content.setter("height"))
                    scroll.add_widget(content)
                    idx = self._gem_shop_tabbar.add_tab(
                        f"Shop {tier}", _hex_rgba(hex_col, 0.7), scroll,
                    )

                    grid = GridLayout(cols=3, size_hint_y=None, spacing=dp(6))
                    grid.bind(minimum_height=grid.setter("height"))
                    content.add_widget(grid)

                    for sid in tier_slots[tier]:
                        # 4 stacked labels: header (item summary line 1 OR
                        # title), summary line 2, summary line 3, status badge.
                        cell, btn, lbls, shine = self._make_shop_button_cell(
                            height=144, n_rows=4,
                            base_bg_rgba=_hex_rgba(hex_col, 0.35),
                        )
                        grid.add_widget(cell)
                        self._gem_shop_slot_buttons[sid] = btn
                        self._gem_shop_slot_labels[sid] = lbls
                        self._gem_shop_slot_shine[sid] = shine

                    self._gem_shop_tier_subtabs[tier] = (idx, content)

                # Shop E sub-tab — 4 deck buttons with stack visuals.
                self._gem_shop_e_deck_buttons: list = []
                self._gem_shop_e_deck_labels:  list = []   # per deck: [Label,...]
                if shop_e_enabled:
                    hex_col = self._SHOP_TIER_HEX.get("E", "BF4D4D")
                    e_scroll  = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
                    e_content = BoxLayout(
                        orientation="vertical", size_hint_y=None,
                        spacing=dp(10), padding=(dp(8), dp(8), dp(8), dp(8)),
                    )
                    e_content.bind(minimum_height=e_content.setter("height"))
                    e_scroll.add_widget(e_content)
                    e_idx = self._gem_shop_tabbar.add_tab(
                        "Shop E", _hex_rgba(hex_col, 0.7), e_scroll,
                    )
                    intro = Label(
                        text="",
                        markup=True, halign="center", valign="middle",
                        size_hint_y=None, height=dp(48), font_size=dp(16),
                    )
                    intro.bind(size=intro.setter("text_size"))
                    e_content.add_widget(intro)
                    self._gem_shop_e_intro = intro
                    self._gem_shop_e_content = e_content
                    deck_row = GridLayout(cols=4, size_hint_y=None, spacing=dp(10),
                                          row_default_height=dp(255),
                                          row_force_default=True)
                    deck_row.bind(minimum_height=deck_row.setter("height"))
                    _E_MAX_BACK = 4            # max peeking cards (top card → 5 shown)
                    _E_STEP     = dp(4)       # per-card offset (up + right)
                    _e_base_rgb = tuple(_hex_rgba(hex_col, 1.0)[:3])
                    self._gem_shop_e_max_back = _E_MAX_BACK
                    self._gem_shop_e_cells: list = []   # deck_idx -> FloatLayout
                    self._gem_shop_e_syncs: list = []   # deck_idx -> sync callable
                    for deck_idx in range(4):
                        # Card-stack visual: up to _E_MAX_BACK solid "back cards"
                        # painted in canvas.before — each offset up-and-right from
                        # the one in front, progressively darker, with a 1px dark
                        # border (also darker further back).  The face button is
                        # the bright, clickable top card anchored at lower-left.
                        cell = FloatLayout(size_hint=(1, 1))
                        cell._e_back_count = _E_MAX_BACK
                        cell._e_base_rgb   = _e_base_rgb
                        _fills, _rects, _borders, _lines = [], [], [], []
                        with cell.canvas.before:
                            for _i in range(_E_MAX_BACK):
                                _fills.append(Color(0, 0, 0, 1))
                                _rects.append(Rectangle())
                                _borders.append(Color(0, 0, 0, 1))
                                _lines.append(Line(width=1.0))
                        face_btn = _BeveledToggleButton(
                            text="", markup=True,
                            size_hint=(None, None),
                            background_color=(*_e_base_rgb, 1),
                        )
                        # 6 click-through labels stacked on top of the button:
                        # title / item name / recipient / classification /
                        # remaining-count / state badge.  Each shortens
                        # individually so multi-line text collapses cleanly.
                        face_rows = _ClickThroughBox(
                            orientation="vertical",
                            size_hint=(None, None),
                            padding=(dp(6), dp(6), dp(6), dp(6)),
                        )
                        deck_labels = []
                        for _ in range(6):
                            lbl = Label(
                                text="", markup=True,
                                halign="center", valign="middle",
                                shorten=True, shorten_from="right", max_lines=1,
                                font_size=dp(14),
                            )
                            lbl.bind(size=lbl.setter("text_size"))
                            face_rows.add_widget(lbl)
                            deck_labels.append(lbl)
                        self._gem_shop_e_deck_labels.append(deck_labels)

                        def _sync_cards(_w=None, _v=None, _cell=cell,
                                        _fills=_fills, _rects=_rects,
                                        _borders=_borders, _lines=_lines,
                                        _btn=face_btn, _rows=face_rows,
                                        _base=_e_base_rgb, _step=_E_STEP,
                                        _maxb=_E_MAX_BACK):
                            x, y, w, h = _cell.x, _cell.y, _cell.width, _cell.height
                            back = max(0, min(_maxb, getattr(_cell, "_e_back_count", _maxb)))
                            # Card size shrinks so the whole stack fits the cell;
                            # the backmost card's top-right touches the cell edge.
                            cw = max(1, w - _step * back)
                            ch = max(1, h - _step * back)
                            br, bg, bb = getattr(_cell, "_e_base_rgb", _base)
                            for i in range(_maxb):
                                if i < back:
                                    b = back - i          # i=0 → backmost card
                                    f  = max(0.30, 1.0 - 0.13 * b)   # darker further back
                                    gv = max(0.06, 0.30 - 0.045 * b) # border darker further back
                                    px, py = x + _step * b, y + _step * b
                                    _fills[i].rgba   = (br * f, bg * f, bb * f, 1)
                                    _rects[i].pos    = (px, py)
                                    _rects[i].size   = (cw, ch)
                                    _borders[i].rgba = (gv, gv, gv, 1)
                                    _lines[i].rectangle = (px, py, cw, ch)
                                else:
                                    _rects[i].size = (0, 0)
                                    _lines[i].rectangle = (0, 0, 0, 0)
                            # Top card = the face button + label overlay, anchored
                            # at the lower-left so back cards peek up and right.
                            _btn.pos  = (x, y); _btn.size  = (cw, ch)
                            _rows.pos = (x, y); _rows.size = (cw, ch)
                        cell.bind(pos=_sync_cards, size=_sync_cards)
                        cell.add_widget(face_btn)
                        cell.add_widget(face_rows)
                        deck_row.add_widget(cell)
                        self._gem_shop_e_deck_buttons.append(face_btn)
                        self._gem_shop_e_cells.append(cell)
                        self._gem_shop_e_syncs.append(_sync_cards)
                    e_content.add_widget(deck_row)
                    self._gem_shop_e_deck_row = deck_row
                    self._gem_shop_tier_subtabs["E"] = (e_idx, e_content)

                if self._gem_shop_tabbar._buttons:
                    self._gem_shop_tabbar.select(0)

            # ---- Compute per-tier unlock state -----------------------------
            def _tier_unlocked(t: str) -> bool:
                # A always open.  B/C/D require beaten >= threshold * (tier-index).
                # threshold == 0 means everything opens immediately.
                if t == "A":
                    return True
                tier_idx = "ABCD".index(t)   # 0..3
                if threshold == 0:
                    return True
                return beaten_count >= threshold * tier_idx

            # ---- Compute Shop E unlock state (only when E is enabled) -----
            # E unlocks once every A-D ITEM/HINT slot has been purchased.
            ad_slot_count   = len([s for s in shop_slot_order
                                    if s.split("_", 1)[0] in "ABCD"])
            ad_purchased    = len([s for s in purchased_slots
                                    if s.split("_", 1)[0] in "ABCD"])
            e_remaining_ad  = max(0, ad_slot_count - ad_purchased)
            e_unlocked      = shop_e_enabled and e_remaining_ad == 0

            def _tier_unlocked_e_aware(t: str) -> bool:
                if t == "E":
                    return e_unlocked
                return _tier_unlocked(t)

            # ---- Refresh sub-tab titles + lock state -----------------------
            for tier, (idx, _content) in self._gem_shop_tier_subtabs.items():
                unlocked = _tier_unlocked_e_aware(tier)
                base_label = f"Shop {tier}"
                self._gem_shop_tabbar.set_button_text(
                    idx, base_label if unlocked else f"{base_label} (locked)"
                )
                # Gray out the tab button when every slot in this tier is bought.
                tier_slots_for_tab = [s for s in shop_slot_order
                                      if s.split("_", 1)[0] == tier]
                all_bought = bool(tier_slots_for_tab) and all(
                    s in purchased_slots for s in tier_slots_for_tab
                )
                if 0 <= idx < len(self._gem_shop_tabbar._buttons):
                    tab_btn = self._gem_shop_tabbar._buttons[idx]
                    hex_col = self._SHOP_TIER_HEX.get(tier, "AAAAAA")
                    new_base = (0.35, 0.35, 0.35, 0.7) if all_bought else _hex_rgba(hex_col, 0.7)
                    tab_btn._base_bg = new_base
                    if not tab_btn._locked:
                        tab_btn._own_bg_col.rgba = new_base
                self._gem_shop_tabbar.set_tab_locked(idx, not unlocked)

            # ---- Per-obelisk summary helpers (mirror archipelago.xs labels)
            from collections import Counter
            _CLS_RANK = {"trap": -1, "filler": 0, "useful": 1, "progression": 2}
            _CLS_DISP = {"trap": "Trap", "filler": "Filler",
                         "useful": "Useful", "progression": "Advancement"}

            def _items_word(n: int) -> str:
                return "item" if n == 1 else "items"

            def _rarest_markup(cls_key: str, disp: str) -> str:
                col = self._SHOP_RARITY_HEX.get(cls_key)
                if col is None:
                    return disp
                return f"[b][color={col}]{disp}[/color][/b]"

            def _obelisk_summary(det_list: list, level: int) -> str:
                if not det_list or level <= 0:
                    return "? items\n? is rarest\n?: main recipient"
                n = len(det_list)
                rarest_cls = max(
                    (d.get("classification", "filler") for d in det_list),
                    key=lambda c: _CLS_RANK.get(c, -1),
                )
                rarest_disp = _CLS_DISP.get(rarest_cls, "?")
                rarest_n    = sum(1 for d in det_list
                                  if d.get("classification", "filler") == rarest_cls)
                main_player = Counter(
                    d.get("player_name", "?") for d in det_list
                ).most_common(1)[0][0]
                n_w  = _items_word(n)
                rn_w = _items_word(rarest_n)
                # Color the rarest classification with the AP item palette
                # once the player has unlocked rarity reveal (level >= 2).
                rarest_text = _rarest_markup(rarest_cls, rarest_disp)
                if level == 1:
                    return f"{n} {n_w}\n? is rarest\n?: main recipient"
                if level == 2:
                    return f"{n} {n_w}\n{rarest_text} is rarest\n?: main recipient"
                if level == 3:
                    return f"{n} {n_w}\n{rarest_text} is rarest\n{main_player}: main recipient"
                return (f"{n} {n_w}\n{rarest_text} is rarest\n"
                        f"{rarest_n} {rarest_text} {rn_w}\n{main_player}: main recipient")

            # ---- Per-tier "most items" obelisk for shine effect --------------
            # When info_level >= 1 (item counts revealed) and the obelisk has
            # not been purchased yet, the obelisk with the most items in each
            # tier gets a glassy shine to highlight the best gem deal.
            tier_max_item_sid: dict = {}
            if int(info_level or 0) >= 1:
                _per_tier: dict = {}
                for _sid in self._gem_shop_slot_buttons.keys():
                    if "_ITEM_" not in _sid:
                        continue
                    _t = _sid.split("_", 1)[0]
                    _n = len(shop_obelisk_assignments.get(_sid, []) or [])
                    if _sid in purchased_slots:
                        continue
                    prev = _per_tier.get(_t)
                    if prev is None or _n > prev[1]:
                        _per_tier[_t] = (_sid, _n)
                tier_max_item_sid = {t: pair[0] for t, pair in _per_tier.items()}

            # ---- Refresh each button face ----------------------------------
            # Each button face is split across 4 stacked labels so individual
            # lines collapse/ellipsise when the window narrows.  rows[0..3]:
            #   item slot       — summary line 1 / 2 / 3 / state badge
            #   shop info slot  — title / subtitle a / subtitle b / state badge
            #   hint slot       — title / subtitle / blank / state badge
            for sid, btn in self._gem_shop_slot_buttons.items():
                rows = self._gem_shop_slot_labels.get(sid) or []
                if len(rows) < 4:
                    continue
                tier      = sid.split("_", 1)[0]
                unlocked  = _tier_unlocked(tier)
                purchased = sid in purchased_slots

                if "_ITEM_" in sid:
                    loc_ids = shop_obelisk_assignments.get(sid, []) or []
                    det     = [shop_item_details.get(int(l), {}) for l in loc_ids]
                    det     = [d for d in det if d]
                    summary = _obelisk_summary(det, int(info_level or 0))
                    parts   = summary.split("\n")
                    row_texts = [
                        parts[0] if len(parts) > 0 else "",
                        parts[1] if len(parts) > 1 else "",
                        parts[2] if len(parts) > 2 else "",
                    ]
                    kind = "item"
                else:
                    hcfg  = shop_hint_config.get(sid, {}) or {}
                    htype = hcfg.get("type", "")
                    if htype == "progressive_info":
                        row_texts = [
                            "[b][color=F2C84A]★ Better Shop Information[/color][/b]",
                            "[color=DDDDDD]Reveals more about every[/color]",
                            "[color=DDDDDD]shop item[/color]",
                        ]
                        kind = "hint_info"
                    else:
                        # Prefer the new static missions_count (rolled at gen);
                        # fall back to the legacy missions_range for older slots.
                        count = hcfg.get("missions_count")
                        if count is None:
                            rng = hcfg.get("missions_range")
                            if rng and rng[0] == rng[1]:
                                count = rng[0]
                        if count is not None:
                            word = "mission" if count == 1 else "missions"
                            subtitle = f"Hints {count} {word}"
                        else:
                            rng = hcfg.get("missions_range")
                            subtitle = f"Hints ({rng[0]}-{rng[1]} missions)" if rng else "Hints"
                        row_texts = [
                            "[b][color=44CCFF]❖ Mission Hints[/color][/b]",
                            f"[color=DDDDDD]{subtitle}[/color]",
                            "",
                        ]
                        kind = "hint"

                if purchased:
                    state_badge = "[color=AAAAAA]Purchased[/color]"
                elif not unlocked:
                    state_badge = "[color=AA4444]Shop locked[/color]"
                else:
                    state_badge = "[color=44FF44]Costs 1 gem[/color]"

                if purchased:
                    import re as _re
                    _strip = lambda s: _re.sub(r'\[/?(?:b|color(?:=[^\]]*)?)\]', '', s)
                    row_texts = [_strip(t) for t in row_texts]

                rows[0].text = row_texts[0]
                rows[1].text = row_texts[1]
                rows[2].text = row_texts[2]
                rows[3].text = state_badge

                # Background color is keyed off slot kind, not tier — sub-tabs
                # carry the tier color so buttons can show purpose at a glance.
                base_hex = self._SHOP_KIND_HEX.get(kind, "8C4DBF")
                alpha    = 0.55 if kind == "hint_info" else 0.45
                btn._base_bg = _hex_rgba(base_hex, alpha)

                btn.set_locked(purchased or not unlocked)

                # Shine highlight on the item-count champion of each tier.
                shine = self._gem_shop_slot_shine.get(sid)
                if shine is not None:
                    shine.set_visible(tier_max_item_sid.get(tier) == sid
                                       and not purchased and unlocked)

                # Re-bind click handler each refresh so it captures the *latest*
                # tier-unlock / gems-available / purchased state by closure.  Cheap
                # rebind avoids stale-context bugs at the cost of one fbind per slot.
                btn.unbind(on_release=getattr(btn, "_aom_buy_handler", lambda *a: None))
                def _make_handler(s=sid, t=tier, _unl=unlocked, _av=gems_available,
                                  _pur=purchased):
                    def _h(_b):
                        self._on_gem_shop_slot_clicked(
                            slot_id=s, tier=t,
                            tier_unlocked=_unl,
                            gems_available=_av,
                            purchased=_pur,
                            threshold=threshold,
                            beaten_count=beaten_count,
                            on_buy_clicked=on_buy_clicked,
                        )
                    return _h
                _h = _make_handler()
                btn._aom_buy_handler = _h
                btn.bind(on_release=_h)

            # ---- Refresh Shop E deck buttons -------------------------------
            if shop_e_enabled and getattr(self, "_gem_shop_e_deck_buttons", None):
                deck_row = getattr(self, "_gem_shop_e_deck_row", None)
                e_content = getattr(self, "_gem_shop_e_content", None)
                intro     = getattr(self, "_gem_shop_e_intro", None)
                if not e_unlocked:
                    # Hide deck entirely.  Only show the "purchase X more"
                    # message in the intro — no cards visible, no clicks fire.
                    if deck_row is not None and deck_row.parent is not None:
                        e_content.remove_widget(deck_row)
                    if intro is not None:
                        intro.text = (
                            f"[b][color=DDDDDD]Purchase {e_remaining_ad} more "
                            f"item{'' if e_remaining_ad == 1 else 's'} from "
                            f"the shop to unlock this shop.[/color][/b]"
                        )
                else:
                    # Unlocked — show deck + brief instructions (no "Gem Sink").
                    if deck_row is not None and deck_row.parent is None and e_content is not None:
                        e_content.add_widget(deck_row)
                    if intro is not None:
                        intro.text = (
                            "[color=DDDDDD]Each deck reveals one card at a time. "
                            "Buy the top card to flip the next.[/color]"
                        )
                    e_decks = shop_e_decks or []
                    for deck_idx, face_btn in enumerate(self._gem_shop_e_deck_buttons):
                        rows = (self._gem_shop_e_deck_labels[deck_idx]
                                if deck_idx < len(self._gem_shop_e_deck_labels) else [])
                        if len(rows) < 6:
                            continue
                        deck = e_decks[deck_idx] if deck_idx < len(e_decks) else []
                        # Find first unpurchased card.  Slot id format for E:
                        # "E_<loc_id>" — matches what on_buy_e_card persists.
                        top_card  = None
                        remaining = 0
                        for card in deck:
                            sid = f"E_{card.get('loc_id')}"
                            if sid not in purchased_slots:
                                if top_card is None:
                                    top_card = card
                                remaining += 1
                        if top_card is None:
                            row_texts = [
                                "[color=AAAAAA]Empty[/color]",
                                "", "", "", "", "",
                            ]
                        elif top_card.get("kind", "filler") == "hint":
                            # Hint cards carry no item reward — they reveal a
                            # random unbeaten mission's checks on purchase.
                            row_texts = [
                                "[b]❖ Mission Hint[/b]",
                                "[color=DDDDDD]Reveals a random[/color]",
                                "[color=DDDDDD]unbeaten mission's checks[/color]",
                                "",
                                "[color=44FF44]Costs 1 gem[/color]",
                                "",
                            ]
                        else:
                            # E unlocking requires every PSI bought, so always
                            # show full info — no obfuscation.
                            item_name = top_card.get("item_name") or "???"
                            player    = top_card.get("player_name") or ""
                            cls       = (top_card.get("classification") or "filler").lower()
                            cls_disp  = {"trap": "Trap", "filler": "Filler",
                                         "useful": "Useful", "progression": "Advancement"}.get(
                                            cls, cls.title())
                            # Match the rest of the shop's rarity palette
                            # (filler teal, useful blue, etc.).
                            cls_col   = self._SHOP_RARITY_HEX.get(cls, "AAAAAA")
                            row_texts = [
                                f"[b]{item_name}[/b]",
                                f"[color=DDDDDD]→ {player}[/color]" if player else "",
                                f"[color={cls_col}]{cls_disp}[/color]",
                                f"[color=DDDDDD]{remaining} card{'' if remaining == 1 else 's'} left[/color]",
                                "[color=44FF44]Costs 1 gem[/color]",
                                "",
                            ]
                        for _i in range(6):
                            rows[_i].text = row_texts[_i]

                        cells = getattr(self, "_gem_shop_e_cells", [])
                        syncs = getattr(self, "_gem_shop_e_syncs", [])

                        # Top-card color: purple for item cards, blue for hint
                        # cards — matching the shop A-D item/hint button hues.
                        if top_card is not None:
                            _kind = top_card.get("kind", "filler")
                            _base_hex = self._SHOP_KIND_HEX["hint"] if _kind == "hint" \
                                        else self._SHOP_KIND_HEX["item"]
                            _base_rgb = tuple(_hex_rgba(_base_hex, 1.0)[:3])
                            face_btn._base_bg = (*_base_rgb, 1)
                            if deck_idx < len(cells):
                                cells[deck_idx]._e_base_rgb = _base_rgb
                        face_btn.set_locked(top_card is None)

                        # Distribute the stack-height reduction across the whole
                        # deck (not just the bottom), then re-sync geometry.
                        if deck_idx < len(cells):
                            _disp = _e_stack_display_count(remaining, len(deck), disp_max=5)
                            cells[deck_idx]._e_back_count = max(0, _disp - 1)
                            syncs[deck_idx]()

                        # Rebind click for this deck button.
                        face_btn.unbind(on_release=getattr(face_btn, "_aom_buy_handler",
                                                           lambda *a: None))
                        def _make_e_handler(_di=deck_idx, _unl=e_unlocked, _av=gems_available,
                                            _top=top_card, _rem_ad=e_remaining_ad):
                            def _h(_b):
                                self._on_gem_shop_e_clicked(
                                    deck_idx=_di,
                                    unlocked=_unl,
                                    gems_available=_av,
                                    top_card=_top,
                                    remaining_ad=_rem_ad,
                                    on_buy_e_card=on_buy_e_card,
                                )
                            return _h
                        _eh = _make_e_handler()
                        face_btn._aom_buy_handler = _eh
                        face_btn.bind(on_release=_eh)

        Clock.schedule_once(_update)

    def _check_gem_shop_click_lockout(self, key: str, period_s: float) -> bool:
        """Anti-double-click guard.  Returns True if the click should proceed
        (and records the click), False if the same `key` was clicked less
        than `period_s` seconds ago.  Tracked per-key so different buttons
        don't block each other."""
        import time
        if not hasattr(self, "_gem_shop_click_lockout"):
            self._gem_shop_click_lockout: dict = {}
        now  = time.monotonic()
        last = self._gem_shop_click_lockout.get(key, 0.0)
        if now - last < period_s:
            return False
        self._gem_shop_click_lockout[key] = now
        return True

    def _on_gem_shop_slot_clicked(
        self, slot_id: str, tier: str, tier_unlocked: bool,
        gems_available: int, purchased: bool,
        threshold: int, beaten_count: int,
        on_buy_clicked,
    ) -> None:
        """Dispatch a click on a gem-shop button.

          * purchased         → toast: already bought
          * tier locked       → popup: "Beat N more scenarios to unlock this shop"
          * no gems           → popup: earn gems by beating scenarios
          * otherwise         → invoke on_buy_clicked(slot_id) (ApClient does the buy)

        Always reset the source ToggleButton back to the normal state — Kivy's
        ToggleButton keeps state="down" after a click otherwise, which left
        un-buyable buttons looking pressed.
        """
        logger = logging.getLogger(__name__)
        btn = self._gem_shop_slot_buttons.get(slot_id)
        if btn is not None:
            btn.state = "normal"

        # 5s double-click guard per slot.  Purchases that take a moment to
        # round-trip to the server otherwise get duplicated when impatient
        # players click again.
        if not self._check_gem_shop_click_lockout(slot_id, 5.0):
            return

        if purchased:
            self._show_shop_message("Already purchased.")
            return
        if not tier_unlocked:
            tier_idx = "ABCD".index(tier) if tier in "ABCD" else 0
            need_total = threshold * tier_idx
            remaining  = max(0, need_total - beaten_count)
            msg = (f"Beat {remaining} more scenario{'s' if remaining != 1 else ''} "
                   f"to unlock Shop {tier}.")
            self._show_shop_message(msg, title=f"Shop {tier} locked")
            return
        if gems_available <= 0:
            self._show_shop_message(
                "Earn gems by beating scenarios.", title="Not enough gems",
            )
            return
        if on_buy_clicked is None:
            logger.info(f"Gem Shop clicked (no-op): {slot_id}")
            return
        try:
            on_buy_clicked(slot_id)
        except Exception as ex:
            logger.warning(f"Gem Shop buy callback failed for {slot_id}: {ex}")

    def _on_gem_shop_e_clicked(
        self, deck_idx: int, unlocked: bool, gems_available: int,
        top_card, remaining_ad: int, on_buy_e_card,
    ) -> None:
        """Click handler for a Shop E deck button.

          * deck empty       → toast
          * E locked         → "Purchase X more items from the shop to unlock"
          * no gems          → popup: earn gems by beating scenarios
          * otherwise        → on_buy_e_card(deck_idx, loc_id, kind)
        """
        # Reset visual press state regardless of outcome.
        if 0 <= deck_idx < len(getattr(self, "_gem_shop_e_deck_buttons", [])):
            self._gem_shop_e_deck_buttons[deck_idx].state = "normal"

        # Lighter 0.5s lockout per deck — long enough to swallow accidental
        # double-clicks but short enough to support rapid sequential buys
        # of the next card up.
        if not self._check_gem_shop_click_lockout(f"E_deck_{deck_idx}", 0.5):
            return

        if top_card is None:
            self._show_shop_message("Deck is empty.", title="Shop E")
            return
        if not unlocked:
            msg = (f"Purchase {remaining_ad} more item"
                   f"{'s' if remaining_ad != 1 else ''} from the shop "
                   f"to unlock this shop.")
            self._show_shop_message(msg, title="Shop E locked")
            return
        if gems_available <= 0:
            self._show_shop_message(
                "Earn gems by beating scenarios.", title="Not enough gems",
            )
            return
        if on_buy_e_card is None:
            logging.getLogger(__name__).info(
                f"Shop E deck {deck_idx+1} clicked (no-op)")
            return
        try:
            on_buy_e_card(
                deck_idx, int(top_card.get("loc_id", 0)),
                top_card.get("kind", "filler"),
            )
        except Exception as ex:
            logging.getLogger(__name__).warning(
                f"Shop E buy callback failed for deck {deck_idx+1}: {ex}")

    def _show_shop_message(self, message: str, title: str = "Gem Shop") -> None:
        """Modal popup for shop notices (locked tier, already bought, etc.).
        Auto-dismisses on Close-button click; click outside also closes."""
        from kivy.uix.popup import Popup
        from kivy.uix.button import Button
        body = BoxLayout(
            orientation="vertical",
            spacing=dp(8), padding=(dp(10), dp(10), dp(10), dp(10)),
        )
        lbl = Label(
            text=message, markup=True, halign="center", valign="middle",
            font_size=dp(16),
        )
        lbl.bind(size=lbl.setter("text_size"))
        body.add_widget(lbl)
        close_btn = Button(
            text="OK", size_hint_y=None, height=dp(40),
        )
        body.add_widget(close_btn)
        popup = Popup(
            title=title, content=body,
            size_hint=(None, None), size=(dp(380), dp(180)),
            auto_dismiss=True,
        )
        close_btn.bind(on_release=lambda _b: popup.dismiss())
        popup.open()

    def on_start(self) -> None:
        logging.getLogger(__name__).addHandler(LogtoUI(self.log_panels["All"].on_log))
        logger = logging.getLogger("Client")
        logger.info("Age of Mythology: Retold client commands:")
        logger.info("  /status              - show connection info and Atlantis Key progress")
        logger.info("  /scenarios (/progress) - list beaten, in-progress, and untouched scenarios")
        # Build all custom tabs eagerly on startup so they always appear in the
        # nav bar.  add_client_tab must be called from the main Kivy thread
        # before the MDNavigationBar layout finalises; calling it mid-session
        # from inside Clock.schedule_once is not guaranteed to work in every
        # version of KivyMD.  Tabs whose data depends on slot_data will show a
        # placeholder until the first update call populates them.
        self.build_scenarios_tab()
        self.build_civs_tab()
        self.build_relics_tab()
        self.build_gem_shop_tab()

    @staticmethod
    def start_ap_ui(ctx: "AoMContext") -> None:
        """Bootstrap the Kivy UI alongside the running asyncio loop.
        Stores both the manager and its task on `ctx` so the client can
        cancel them on shutdown.

        Caller: `main()` in ApClient.py.
        """
        ctx.ui = AoMManager(ctx)
        ctx.ui_task = asyncio.create_task(ctx.ui.async_run(), name="UI")
