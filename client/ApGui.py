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
from kivy.uix.scrollview import ScrollView
from kvui import GameManager, LogtoUI


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
        Called from on_start() so the tab always appears regardless of option settings."""
        if getattr(self, "_scenarios_tab", None) is not None:
            return
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        # Top padding pushes the first row of tiles below the status panel (dp(100) tall).
        outer = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=(dp(6), dp(100), dp(6), dp(6)))
        outer.bind(minimum_height=outer.setter("height"))
        scroll.add_widget(outer)
        try:
            self.add_client_tab("Scenarios", scroll)
        except Exception as ex:
            logging.getLogger(__name__).warning(f"Could not add Scenarios tab: {ex}")
            return
        self._scenarios_tab = scroll
        self._scenarios_outer = outer
        self._scenario_tile_widgets: dict = {}

    def update_scenarios_view(
        self,
        unlock_sets_of_scenarios: int,
        scenario_to_key_id: dict,
        bundle_display_names: dict,
        held_keys: set,
        campaign_unlocked_by_id: dict,
        disabled_campaign_ids: set,
        scenario_to_god: dict = None,
        scenario_check_counts: dict = None,
    ) -> None:
        """Refresh the Scenarios tab.  Safe to call repeatedly; on first call,
        builds the grid; on subsequent calls, just recolors tiles.

        Args:
            unlock_sets_of_scenarios: option value (0 means option is off; tab
                still renders but tile state collapses to campaign-only).
            scenario_to_key_id:       scenario global_number → AP item id.
            bundle_display_names:     AP item id → friendly bundle name.
            held_keys:                set of AP item ids the player has.
            campaign_unlocked_by_id:  campaign.id → bool.
            disabled_campaign_ids:    campaign.id ints to omit entirely.
            scenario_to_god:          scenario global_number → major god name (optional).
            scenario_check_counts:    scenario global_number → (found, total) tuple (optional).
        """
        if scenario_to_god is None:
            scenario_to_god = {}
        if scenario_check_counts is None:
            scenario_check_counts = {}

        def _update(dt):
            from ..locations.Scenarios import aomScenarioData
            from ..locations.Campaigns  import aomCampaignData

            self.build_scenarios_tab()

            if not getattr(self, "_scenario_tile_widgets", None):
                # First-time grid build.
                self._scenarios_outer.clear_widgets()
                self._scenario_tile_widgets = {}
                # Group by campaign in enum order.
                by_campaign: dict = {}
                for s in aomScenarioData:
                    by_campaign.setdefault(s.campaign, []).append(s)

                for campaign, scenarios in by_campaign.items():
                    if campaign.id in disabled_campaign_ids:
                        continue
                    section = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
                    section.bind(minimum_height=section.setter("height"))

                    header = Label(
                        text=f"[b]{campaign.campaign_name}[/b]",
                        markup=True, halign="left", valign="middle",
                        size_hint_y=None, height=dp(36), font_size=dp(26),
                    )
                    header.bind(size=header.setter("text_size"))
                    section.add_widget(header)

                    # 5 columns; GridLayout auto-sizes tile widths.
                    # At ~800 px window the natural width per tile is ~160 px, giving
                    # approximately a 2:1 width:height ratio with the dp(80) height below.
                    grid = GridLayout(cols=5, size_hint_y=None, spacing=dp(4))
                    grid.bind(minimum_height=grid.setter("height"))

                    for s in scenarios:
                        tile = Label(
                            text=s.display_name, markup=True,
                            halign="center", valign="middle",
                            size_hint_y=None, height=dp(80), font_size=dp(22),
                        )
                        tile.bind(size=tile.setter("text_size"))

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
                            tile, bg_color, slash_col, s.campaign.name
                        )
                        grid.add_widget(tile)

                    section.add_widget(grid)
                    self._scenarios_outer.add_widget(section)

            # Recolor every tile based on current state.
            for sid, (tile, color, slash_col, camp_name) in self._scenario_tile_widgets.items():
                base = _CAMPAIGN_TILE_COLORS.get(camp_name, (0.5, 0.5, 0.5))
                kid = scenario_to_key_id.get(sid)
                key_held = (kid is not None and kid in held_keys)
                # Without the scenario-key option, every scenario is treated as key-held.
                if unlock_sets_of_scenarios <= 0:
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

                # Build tile text: scenario name (truncated to first line), god, check count.
                name = scen_obj.display_name if scen_obj else str(sid)
                # Keep adding words until the running total exceeds 14 chars so the name
                # fits on a single line without wrapping and pushing god/checks off the tile.
                words = name.split()
                kept, total_chars = [], 0
                for w in words:
                    candidate = total_chars + len(w) + (1 if kept else 0)
                    if kept and candidate > 14:
                        break
                    kept.append(w)
                    total_chars = candidate
                name_line = " ".join(kept)
                # Text color: black on fully-unlocked NEW_ATLANTIS tiles (teal background
                # makes white text hard to read) and fully-unlocked FOTT_EGYPTIAN tiles
                # (bright yellow background also makes white text hard to read); white elsewhere.
                if fully_unlocked and camp_name in ("NEW_ATLANTIS", "FOTT_EGYPTIAN"):
                    name_line_markup = f"[b][color=000000]{name_line}[/color][/b]"
                    god_markup = lambda g: f"[i][color=000000]{g}[/color][/i]"
                    checks_markup = lambda s: f"[color=000000]{s}[/color]"
                else:
                    name_line_markup = f"[b]{name_line}[/b]"
                    god_markup = lambda g: f"[i]{g}[/i]"
                    checks_markup = lambda s: s

                lines = [name_line_markup]

                god_name = scenario_to_god.get(sid)
                if god_name:
                    lines.append(god_markup(god_name))

                check_info = scenario_check_counts.get(sid)
                if check_info:
                    found, total = check_info
                    lines.append(checks_markup(f"{found}/{total} checks"))

                tile.text = "\n".join(lines)

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
    }

    def build_civs_tab(self) -> None:
        """Lazy-build the Civilizations tab (called from update_civs_view)."""
        if getattr(self, "_civs_tab", None) is not None:
            return
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        outer = BoxLayout(
            orientation="vertical", size_hint_y=None,
            spacing=dp(10), padding=(dp(8), dp(8), dp(8), dp(8)),
        )
        outer.bind(minimum_height=outer.setter("height"))
        scroll.add_widget(outer)
        try:
            self.add_client_tab("Civilizations", scroll)
        except Exception as ex:
            logging.getLogger(__name__).warning(f"Could not add Civilizations tab: {ex}")
            return
        self._civs_tab   = scroll
        self._civs_outer = outer
        self._civ_section_widgets: dict = {}
        self._civs_global_missing_lbl = None

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
                VillagerCarryCapacity,
                StartingResources, StartingResourcesLarge,
                PassiveIncome, PassiveIncomeLarge,
                RelicTrickle, RelicEffect,
                Reinforcement, ReinforcementUseful,
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
            if not hasattr(self, "_civs_outer"):
                return

            counts     = Counter(received_ids)
            received_s = set(received_ids)

            # --- Determine active civs -------------------------------------------
            _CIV_ORDER  = ["Generic", "Greek", "Egyptian", "Norse", "Atlantean"]
            active_civs = []
            for _civ in _CIV_ORDER:
                if _civ == "Atlantean" and not random_major_gods:
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
                VillagerCarryCapacity,
            )
            # Types that are never counted as "in multiworld" items for display
            _SKIP_TYPES = (Victory, Campaign, FinalUnlock, Trap, Gem, ProgressiveShopInfo, ScenarioKey)
            # Unit/myth training unlocks — shown with checkmarks
            _UNIT_TYPES = (UnitUnlockProgression, UnitUnlockUseful,
                           AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful)
            _MYTH_TYPES = (MythUnitUnlockProgression, MythUnitUnlockUseful,
                           MythUnitUnlockFiller, AtlanteanMythUnitUnlock)
            # Misc: civ-specific but not unit/myth/age — shown only when received
            _MISC_TYPES = (VillagerCarryCapacity,)

            def _item_culture(item):
                t = item.type
                if isinstance(t, _CIV_TYPES):
                    c = getattr(t, "culture", None)
                    if c:
                        return c
                    un = getattr(t, "unit_name", "")
                    for _c in ("Greek", "Egyptian", "Norse", "Atlantean"):
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
            cached_civs = set(self._civ_section_widgets.keys())
            if cached_civs != set(active_civs):
                self._civs_outer.clear_widgets()
                self._civ_section_widgets  = {}
                self._civs_global_missing_lbl = None

                # --- Global missing header (above Generic) ---
                gml = Label(
                    text="", markup=True, halign="left", valign="middle",
                    size_hint_y=None, height=dp(41), font_size=dp(29),
                )
                gml.bind(size=gml.setter("text_size"))
                self._civs_outer.add_widget(gml)
                self._civs_global_missing_lbl = gml

                for civ in active_civs:
                    hdr_hex = self._CIV_HEADER_HEX.get(civ, "AAAAAA")

                    section = BoxLayout(
                        orientation="vertical", size_hint_y=None, spacing=dp(1),
                    )
                    section.bind(minimum_height=section.setter("height"))

                    header = Label(
                        text=f"[b][color={hdr_hex}]{civ}[/color][/b]",
                        markup=True, halign="left", valign="middle",
                        size_hint_y=None, height=dp(41), font_size=dp(29),
                    )
                    header.bind(size=header.setter("text_size"))
                    section.add_widget(header)

                    # Age progress row (civ sections only)
                    age_lbl = None
                    if civ != "Generic":
                        age_lbl = Label(
                            text="", markup=True, halign="left", valign="middle",
                            size_hint_y=None, height=dp(29), font_size=dp(18),
                        )
                        age_lbl.bind(size=age_lbl.setter("text_size"))
                        section.add_widget(age_lbl)

                    # Item-rows container (cleared and rebuilt each update)
                    items_box = BoxLayout(
                        orientation="vertical", size_hint_y=None, spacing=dp(0),
                    )
                    items_box.bind(minimum_height=items_box.setter("height"))
                    section.add_widget(items_box)

                    # Thin decorative separator
                    sep = Label(
                        text="[color=252525]" + ("\u2500" * 80) + "[/color]",
                        markup=True, halign="left", valign="middle",
                        size_hint_y=None, height=dp(12), font_size=dp(10),
                    )
                    sep.bind(size=sep.setter("text_size"))
                    section.add_widget(sep)

                    self._civs_outer.add_widget(section)
                    self._civ_section_widgets[civ] = {
                        "section":   section,
                        "age_lbl":   age_lbl,
                        "items_box": items_box,
                    }

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

            for civ, refs in self._civ_section_widgets.items():
                ib      = refs["items_box"]
                age_ref = refs["age_lbl"]
                ib.clear_widgets()

                if civ == "Generic":
                    # ---- Generic: received non-civ items grouped by category ----
                    all_gen = _generic_items_all()
                    _GEN_GROUPS = [
                        ("Starting Resources",  (StartingResources, StartingResourcesLarge)),
                        ("Passive Income",       (PassiveIncome, PassiveIncomeLarge)),
                        ("Relic Trickles",       (RelicTrickle,)),
                        ("Relic Effects",        (RelicEffect,)),
                        ("Reinforcements",       (Reinforcement, ReinforcementUseful)),
                        ("Unit Stat Bonuses",    (UnitStatBonus,)),
                        ("Villager Discounts",   (GenericVillagerDiscount,)),
                        ("Starting Techs",       (StartingEconomyTech, StartingMilitaryTech,
                                                  StartingDockTech, StartingBuildingsTech)),
                    ]
                    for grp_name, grp_types in _GEN_GROUPS:
                        grp = [
                            (it, counts.get(it.id, 0)) for it in all_gen
                            if isinstance(it.type, grp_types)
                            and counts.get(it.id, 0) > 0
                        ]
                        if not grp:
                            continue
                        ib.add_widget(_subhdr(grp_name))
                        for it, n in grp:
                            sfx = f" [color=AAAAAA]x{n}[/color]" if n > 1 else ""
                            ib.add_widget(
                                _mkrow(f"[color=EEEEEE]    \u2022 {it.item_name}[/color]{sfx}")
                            )

                    # Hero Items: Arkantos first, then other heroes alphabetically.
                    # No group sub-header; hero name acts as implicit separator.
                    _HERO_TYPES = (HeroStatBoost, HeroStatBoostFiller,
                                   HeroSpecialEffect, HeroActionBoost, ArkantosHousing)
                    hero_items_all = [
                        it for it in all_gen
                        if isinstance(it.type, _HERO_TYPES)
                    ]
                    if hero_items_all:
                        def _hero_name(it):
                            if isinstance(it.type, ArkantosHousing):
                                # Both Arkantos and Kastor reuse ArkantosHousing;
                                # distinguish by item name prefix.
                                return "Kastor" if it.item_name.startswith("Kastor") else "Arkantos"
                            h = getattr(it.type, "hero", "") or ""
                            return h[:-3] if h.endswith("SPC") else h
                        def _hero_sort_key(it):
                            h = _hero_name(it)
                            return (0, it.item_name) if h == "Arkantos" else (1, h, it.item_name)
                        hero_items_all.sort(key=_hero_sort_key)
                        ib.add_widget(_subhdr("Hero Items"))
                        for it in hero_items_all:
                            if counts.get(it.id, 0) == 0:
                                continue
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

        Clock.schedule_once(_update)

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
        update_relics_view() once slot_data is received.  If relicsanity is
        disabled in the seed a placeholder message is shown instead."""
        if getattr(self, "_relics_tab", None) is not None:
            return
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        outer = BoxLayout(
            orientation="vertical", size_hint_y=None,
            spacing=dp(6), padding=(dp(8), dp(8), dp(8), dp(8)),
        )
        outer.bind(minimum_height=outer.setter("height"))
        # Placeholder shown before slot_data arrives or when relicsanity is off
        placeholder = Label(
            text="[color=666666]Relicsanity is not enabled for this seed.[/color]",
            markup=True, halign="left", valign="top",
            size_hint_y=None, height=dp(40), font_size=dp(18),
        )
        placeholder.bind(size=placeholder.setter("text_size"))
        outer.add_widget(placeholder)
        scroll.add_widget(outer)
        try:
            self.add_client_tab("Relics", scroll)
        except Exception as ex:
            logging.getLogger(__name__).warning(f"Could not add Relics tab: {ex}")
            return
        self._relics_tab         = scroll
        self._relics_outer       = outer
        self._relics_placeholder = placeholder
        # loc_id -> Label widget so we can update only the text on refresh
        self._relic_row_widgets: dict = {}
        self._relics_built = False

    def update_relics_view(
        self,
        relicsanity: bool,
        checked_locs: set,
        disabled_campaign_ids: set,
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
        def _update(dt):
            # When relicsanity is off keep the placeholder; do nothing else.
            if not relicsanity:
                return
            # Relicsanity is on: hide the placeholder if it is still there.
            if hasattr(self, "_relics_placeholder") and self._relics_placeholder.parent:
                self._relics_outer.remove_widget(self._relics_placeholder)

            from ..locations.Locations import (
                aomLocationData, aomLocationType, SCENARIO_TO_LOCATIONS,
            )
            from ..locations.Scenarios import aomScenarioData
            from ..locations.Campaigns import aomCampaignData

            self.build_relics_tab()
            if not hasattr(self, "_relics_outer"):
                return

            # ---- Build skeleton once ----------------------------------------
            if not self._relics_built:
                self._relics_built = True
                self._relic_row_widgets = {}
                self._relics_outer.clear_widgets()

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

                    # Campaign header
                    camp_lbl = Label(
                        text=f"[b][color={camp_hex}]{campaign.campaign_name}[/color][/b]",
                        markup=True, halign="left", valign="middle",
                        size_hint_y=None, height=dp(41), font_size=dp(29),
                    )
                    camp_lbl.bind(size=camp_lbl.setter("text_size"))
                    self._relics_outer.add_widget(camp_lbl)

                    for scenario, relic_locs in scenario_groups:
                        # Scenario sub-header
                        scen_lbl = Label(
                            text=f"[b][color=CCCCCC]  {scenario.display_name}[/color][/b]",
                            markup=True, halign="left", valign="middle",
                            size_hint_y=None, height=dp(26), font_size=dp(17),
                        )
                        scen_lbl.bind(size=scen_lbl.setter("text_size"))
                        self._relics_outer.add_widget(scen_lbl)

                        for loc in relic_locs:
                            row_lbl = Label(
                                text="", markup=True,
                                halign="left", valign="middle",
                                size_hint_y=None, height=dp(23), font_size=dp(16),
                            )
                            row_lbl.bind(size=row_lbl.setter("text_size"))
                            self._relics_outer.add_widget(row_lbl)
                            self._relic_row_widgets[loc.id] = (row_lbl, loc.location_name)

                        # Thin separator after each scenario block
                        sep = Label(
                            text="[color=252525]" + ("\u2500" * 80) + "[/color]",
                            markup=True, halign="left", valign="middle",
                            size_hint_y=None, height=dp(10), font_size=dp(9),
                        )
                        sep.bind(size=sep.setter("text_size"))
                        self._relics_outer.add_widget(sep)

            # ---- Update checkmark state on every call -----------------------
            for loc_id, (row_lbl, loc_name) in self._relic_row_widgets.items():
                checked  = loc_id in checked_locs
                if checked:
                    # Collected: dim green tick, dark text
                    row_lbl.text = (
                        f"[color=336633]    \u2714[/color]"
                        f" [color=363636]{loc_name}[/color]"
                    )
                else:
                    # Uncollected: blank indent, bold bright text, no X
                    row_lbl.text = (
                        f"        [b][color=EEEEEE]{loc_name}[/color][/b]"
                    )

        Clock.schedule_once(_update)

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

    @staticmethod
    def start_ap_ui(ctx: "AoMContext") -> None:
        """Bootstrap the Kivy UI alongside the running asyncio loop.
        Stores both the manager and its task on `ctx` so the client can
        cancel them on shutdown.

        Caller: `main()` in ApClient.py.
        """
        ctx.ui = AoMManager(ctx)
        ctx.ui_task = asyncio.create_task(ctx.ui.async_run(), name="UI")
