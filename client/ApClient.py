# =============================================================================
# Age of Mythology Retold — Archipelago client (CLI + Tk GUI)
# =============================================================================
#
# Spawned by the Archipelago Launcher when the user clicks "Age Of Mythology
# Retold Client".  Connects to the AP server, exchanges items/locations, and
# bridges those events into the running game by writing XS state files into
# the player's AoMR user folder.
#
# Responsibilities:
#   * Authenticate to the AP server and load slot_data.
#   * Install the bundled XS trigger files (archipelago.xs, ap_init.xs,
#     ap_ai_*.xs) into the AoMR user folder so the game has them available.
#   * Maintain `user.cfg` so AI echo / trigger echo are enabled (we read
#     the AoMR log file to detect in-game events).
#   * Watch the AoMR log file for `APLocationCheck` markers emitted by the
#     game's XS triggers and forward them as AP location events.
#   * Receive items from the AP server, hand them to GameClient.py which
#     writes the per-game `aom_state.xs` (state file consumed by archipelago.xs).
#   * Surface a Tk-based status window via ApGui.py.
#
# Critical files & paths:
#   * `<user_folder>/trigger/archipelago.xs` and `ap_init.xs` — included from
#     each scenario.
#   * `<user_folder>/Game/AI/ap_ai_*.xs` — AI script referenced by every map.
#   * `<user_folder>/config/user.cfg` — must contain `aiDebug` and
#     `enableTriggerEcho` for the AP↔game bridge to work.
#   * `<user_folder>/Logs/<latest>.txt` — AoMR's stdout-equivalent.  We tail
#     this to detect game events.
#
# Slot data flow:
#   server -> on_package -> _load_slot_data -> self.game_ctx.<field>
#   The fields are then read by GameClient.py when emitting aom_state.xs.
#
# Adding a new server-to-game datum:
#   1. Emit it from `aomWorld.fill_slot_data` in __init__.py.
#   2. Read it in `_load_slot_data` here and store on `self.game_ctx`.
#   3. Reference it in GameClient.py XS emission and consume it in
#      archipelago.xs at runtime.
#
# Adding a new game-to-server event:
#   1. Make archipelago.xs print a unique token via trChatSend / aiEcho.
#   2. Add a regex pattern + handler in the log-watcher (search for
#      'APLocationCheck' / 'APStatus' to find existing patterns).
#   3. Implement the AP-side handling (typically calling
#      `await self.send_msgs([...])` to forward the event).
# =============================================================================

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

import Utils
import tkinter
import tkinter.filedialog
import tkinter.messagebox
from CommonClient import ClientCommandProcessor, CommonContext, get_base_parser, server_loop
from NetUtils import ClientStatus, NetworkItem

from ..items.Items import aomItemData
from .ApGui import AoMManager
from .GameClient import AoMGameContext, game_loop, generate_ap_ai_xs, on_items_received

logger = logging.getLogger("Client")

import zipfile

# Path to the icon file, bundled alongside this module
_ICON_PATH = Path(__file__).parent.parent / "aom_icon.ico"

# Trigger files bundled inside the apworld at aom/triggers/
# Format: (source filename in apworld, destination subfolder relative to user_folder)
_TRIGGER_FILES = [
    ("ap_init.xs",        "trigger"),   # scenario trigger include
    ("archipelago.xs",    "trigger"),   # main AP logic
    ("ap_ai_init.xs",     "Game\\AI"),  # stable AI entry point used by scenarios
    ("ap_ai_runtime.xs",  "Game\\AI"),  # runtime AI template; regenerated on connect
]


def _find_apworld_path() -> Optional[Path]:
    """Locate the .apworld zip file by walking up from this module's path."""
    for parent in Path(__file__).parents:
        if parent.suffix == ".apworld":
            return parent
    return None


def _install_trigger_files(user_folder: str) -> None:
    """
    Copy XS trigger files from the apworld zip to the player's trigger folder.
    Runs on every connection so files stay in sync with apworld updates.
    Destination: <user_folder>\\trigger\\
    Source:       aom/triggers/ inside aom.apworld
    """
    if not user_folder:
        logger.warning("Trigger install skipped: user folder not set.")
        return

    apworld_path = _find_apworld_path()
    if apworld_path is None:
        logger.warning("Could not locate aom.apworld — trigger files not installed.")
        return

    installed = []
    failed   = []
    try:
        with zipfile.ZipFile(apworld_path) as zf:
            for filename, subfolder in _TRIGGER_FILES:
                dest_dir = Path(user_folder) / subfolder
                dest_dir.mkdir(parents=True, exist_ok=True)
                source = f"aom/triggers/{filename}"
                dest   = dest_dir / filename
                try:
                    dest.write_bytes(zf.read(source))
                    installed.append(filename)
                except KeyError:
                    failed.append(filename)
                    logger.warning(f"Trigger file missing from apworld: {source}")
    except Exception as e:
        logger.error(f"Failed to open apworld for trigger install: {e}")
        return

    if installed:
        logger.info(f"Trigger files installed to {user_folder}: {installed}")
    if failed:
        logger.warning(
            f"Some trigger files could not be installed: {failed}. "
            f"Copy them manually to their destinations in {user_folder}"
        )


# Lines required in user.cfg for the AI echo log to function.
# aiDebug       — enables the AI subsystem and writes aiEcho() output to the log file.
# enableTriggerEcho — routes trMessageSetText() calls through the AI echo log.
_REQUIRED_CFG_LINES = ["aiDebug", "enableTriggerEcho"]


def _ensure_user_cfg(user_folder: str) -> None:
    """
    Ensures user.cfg in the player's AoMR user folder contains the two lines
    required for the mod's AI echo system to function. Creates the file if it
    does not exist. Appends only the missing lines if it already exists, so
    any custom settings the player has are preserved.
    """
    if not user_folder:
        logger.warning("user.cfg check skipped: user folder not set.")
        return

    cfg_path = Path(user_folder) / "config" / "user.cfg"

    # Read existing content if the file exists
    existing_lines: set[str] = set()
    if cfg_path.exists():
        try:
            existing_lines = {line.strip() for line in cfg_path.read_text().splitlines()}
        except Exception as e:
            logger.warning(f"Could not read user.cfg: {e}")
            return

    missing = [line for line in _REQUIRED_CFG_LINES if line not in existing_lines]

    if not missing:
        return  # Nothing to do

    try:
        with cfg_path.open("a") as f:
            # Add a newline separator if the file exists and doesn't end with one
            if cfg_path.stat().st_size > 0:
                f.write("\n")
            f.write("\n".join(missing) + "\n")
        logger.info(f"user.cfg updated with required lines: {missing}")
    except Exception as e:
        logger.error(
            f"Could not update user.cfg: {e}. "
            f"This usually means the wrong AoMR folder was selected at first-time setup. "
            f"Run /fix_aom_folder to clear the saved path and pick the correct folder. "
            f"The folder we need is likely here: "
            f"C:\\Users\\[YourName]\\Games\\Age of Mythology Retold\\[SteamID] "
            f"(not the Steam install directory). "
            f"If the path above is correct, add these lines manually to {cfg_path}: {missing}"
        )


AOMR = "Age Of Mythology Retold"
AOMR_CONFIG_FILE = "aomr_client.json"


def _load_user_folder() -> str:
    """Load the saved AoMR user folder path from `aomr_client.json` in the AP
    user directory.  This is the same folder set in the launcher GUI; we
    persist it so the player only has to point at it once."""
    try:
        config_path = Utils.user_path(AOMR_CONFIG_FILE)
        if os.path.exists(config_path):
            with open(config_path) as f:
                return json.load(f).get("user_folder", "")
    except Exception:
        pass
    return ""


def _save_user_folder(folder: str) -> None:
    """Persist the AoMR user folder path so the next launch picks it up
    automatically.  Counterpart to `_load_user_folder`."""
    try:
        config_path = Utils.user_path(AOMR_CONFIG_FILE)
        with open(config_path, "w") as f:
            json.dump({"user_folder": folder}, f, indent=2)
    except Exception as e:
        print(f"Warning: could not save config: {e}")


# Subdirectories AoMR creates inside every per-user (Steam-ID) folder.
# Used to recognise a valid user folder and to reject common wrong picks
# (the parent folder, the game install directory, etc.).
_AOMR_MARKER_DIRS = ("config", "Data", "Game", "mods", "scenario")


def _looks_like_aomr_folder(folder: str) -> bool:
    """True if `folder` exists and looks like an AoMR per-user folder — i.e.
    it contains the subdirectories AoMR creates (config, Data, Game, ...).
    The "temp" folder AoMR keeps alongside the real per-user folders is
    excluded — it also has those subdirs but is never the right pick."""
    if not folder:
        return False
    p = Path(folder)
    if not p.is_dir():
        return False
    if p.name.lower() == "temp":
        return False
    return any((p / d).is_dir() for d in _AOMR_MARKER_DIRS)


def _aomr_base_dir() -> Path:
    """Standard location AoMR creates per-Steam-ID user folders under:
    %USERPROFILE%\\Games\\Age of Mythology Retold."""
    return Path(os.path.expanduser("~")) / "Games" / "Age of Mythology Retold"


def _scan_aomr_user_folders(base: Path) -> list:
    """Return every immediate subfolder of `base` that looks like an AoMR
    per-user folder.  Used both for auto-detection and for guiding the user
    when they accidentally pick the parent folder."""
    found: list = []
    try:
        if base.is_dir():
            for child in sorted(base.iterdir()):
                if child.is_dir() and _looks_like_aomr_folder(str(child)):
                    found.append(str(child).replace("/", "\\"))
    except Exception:
        pass
    return found


def _autodetect_user_folders() -> list:
    """Auto-detect AoMR user folders at the standard base path.  Normally
    returns exactly one (the player's Steam-ID folder); empty if AoMR user
    data is absent (game never run, or installed to a non-standard path)."""
    candidates = _scan_aomr_user_folders(_aomr_base_dir())
    # The real per-user folder is named with the numeric Steam ID.  When any
    # numeric-named folder exists, restrict to those so detection is not
    # derailed by other siblings the game may create next to it.
    numeric = [c for c in candidates if Path(c).name.isdigit()]
    if numeric:
        return numeric
    return candidates


def _confirm_detected_folder(folder: str) -> bool:
    """Ask the player to confirm an auto-detected user folder before using it."""
    root = tkinter.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", True)
    try:
        root.iconbitmap(str(_ICON_PATH))
    except Exception:
        pass  # icon is optional
    try:
        return bool(tkinter.messagebox.askyesno(
            "AoMR user folder found",
            "Found your Age of Mythology: Retold user folder:\n\n"
            f"{folder}\n\nUse this folder?",
        ))
    finally:
        root.destroy()


def _resolve_mods_local_dir(user_folder: str) -> Path:
    """Build the path to the player's local mods directory under the AoMR user
    folder.  Used when verifying the AoMR Archipelago mod is installed."""
    return Path(user_folder) / "mods" / "local"


# -----------------------------------------------------------------------
# Scenario progress helpers
# -----------------------------------------------------------------------

def _count_beaten_scenarios(ctx: "AoMContext") -> int:
    """
    Counts how many non-final scenarios the player has beaten by checking
    which Victory location IDs are in sent_checks.
    Completion locations have address=None (they are AP events, never sent
    as LocationChecks). Victory locations are real addressed locations that
    ARE sent when the player wins a scenario, so they appear in sent_checks.
    Scenarios that count: FotT 1-30 (global_number <= 30), all of New Atlantis
    (501-512), and all of The Golden Gift (601-604). FotT 31 (the goal) is
    excluded.
    """
    from ..locations.Locations import aomLocationData, aomLocationType
    beaten = 0
    for loc in aomLocationData:
        if loc.type != aomLocationType.VICTORY:
            continue
        gn = loc.scenario.global_number
        counts = (gn <= 30) or (501 <= gn <= 512) or (601 <= gn <= 604)
        if counts and loc.id in ctx.game_ctx.sent_checks:
            beaten += 1
    return beaten


def _get_atlantis_status(ctx: "AoMContext") -> tuple[str, bool]:
    """
    Returns (status_text, is_green) for the Atlantis Key status label.
    is_green=True  → bright green (unlocked / open)
    is_green=False → yellow (in progress or neutral)
    """
    from ..items.Items import aomItemData
    threshold  = getattr(ctx, "_x_scenarios_threshold", None)
    final_mode = getattr(ctx, "_final_mode_value", None)

    # Check whether Atlantis Key is in received items
    atlantis_key_id = aomItemData.ATLANTIS_KEY.id
    has_key = atlantis_key_id in ctx.game_ctx.received_items

    if has_key:
        return ("You have the Atlantis Key! Atlantis is Open!", True)

    if final_mode == 0 and threshold is not None:
        # beat_x_scenarios mode — no key item; Final section opens on completion count
        beaten = _count_beaten_scenarios(ctx)
        if beaten >= threshold:
            return ("Atlantis is Open!", True)
        return (f"Missions Beaten for Atlantis: {beaten} / {threshold}", False)

    if final_mode == 2:
        # atlantis_key mode — key is somewhere in the multiworld
        return ("Atlantis Key is out in the multiworld", False)

    if final_mode == 1:
        # always_open
        return ("Atlantis is Open!", True)

    return ("", False)


def _ap_client_buy_shop_slot(ctx: "AoMContext", slot_id: str) -> None:
    """Process an AP-client gem-shop purchase (A-D).

    Replaces the in-game XS shop's AP_SHOP aiEcho path.  Routes through the
    same `_resolve_shop_signal` so dedup + persistence + hint broadcast all
    behave identically.  Loc-id checks are sent in a single batch.
    """
    from .GameClient import _resolve_shop_signal
    gc = ctx.game_ctx
    if not gc.gem_shop_enabled:
        return
    if slot_id in gc.purchased_slots:
        return
    loc_ids = _resolve_shop_signal(gc, slot_id)
    new_locs = [lid for lid in loc_ids
                if lid not in gc.sent_checks and lid not in gc.server_known_checks]
    for lid in new_locs:
        gc.sent_checks.add(lid)
    if new_locs:
        from .GameClient import save_sent_checks
        save_sent_checks(gc)
        asyncio.ensure_future(ctx.on_locations_received_batch(new_locs))


def _ap_client_buy_shop_e_card(ctx: "AoMContext", deck_idx: int,
                                loc_id: int, kind: str) -> None:
    """Process an AP-client Shop E card purchase.

    Bookkeeping mirrors `_resolve_shop_signal`:
      * append `E_<loc_id>` to purchased_slots for gem accounting
      * persist shop state + rewrite aom_state.xs
      * send the location check for the card
      * if kind == "hint", trigger a mission-hint broadcast for an unbeaten
        scenario (range covers all currently-active scenarios)

    No-op if E disabled or this card already bought.
    """
    from .GameClient import save_shop_state, save_sent_checks, write_aom_state
    gc = ctx.game_ctx
    if not gc.shop_e_enabled:
        return
    slot_id = f"E_{loc_id}"
    if slot_id in gc.purchased_slots:
        return
    gc.purchased_slots.add(slot_id)
    save_shop_state(gc)
    write_aom_state(gc)

    # Hint cards hold no reward — they never check their location, so no item
    # is sent.  Item/filler cards check the location as normal.
    if kind != "hint" and loc_id not in gc.sent_checks and loc_id not in gc.server_known_checks:
        gc.sent_checks.add(loc_id)
        save_sent_checks(gc)
        asyncio.ensure_future(ctx.on_locations_received_batch([loc_id]))

    if kind == "hint":
        # Reveal exactly one random unbeaten mission's checks.  send_mission_hints
        # draws from every campaign (all of aomScenarioData), so NA / GG / any
        # future campaign are all candidates automatically.
        try:
            ctx.send_mission_hints((1, 1))
        except Exception as ex:
            logger.warning(f"Shop E hint broadcast failed: {ex}")

    _update_atlantis_ui(ctx)


def _update_atlantis_ui(ctx: "AoMContext") -> None:
    """Push the current Atlantis and shop status to the UI labels if the UI is ready."""
    if not (hasattr(ctx, "ui") and ctx.ui and hasattr(ctx.ui, "update_atlantis_status")):
        return
    text, green = _get_atlantis_status(ctx)
    ctx.ui.update_atlantis_status(text, green)

    if hasattr(ctx.ui, "update_shop_status"):
        if not ctx.game_ctx.gem_shop_enabled:
            ctx.ui.update_shop_status(None, None)
        else:
            from .GameClient import GEM_ITEM_ID, VICTORY_LOCATION_IDS
            gems_earned = sum(1 for i in ctx.game_ctx.received_items if i == GEM_ITEM_ID)
            gems_spent  = len(ctx.game_ctx.purchased_slots)
            gems_avail  = max(0, gems_earned - gems_spent)
            threshold   = ctx.game_ctx.wins_to_open_shop
            beaten      = len((ctx.game_ctx.sent_checks | ctx.game_ctx.server_known_checks)
                              & VICTORY_LOCATION_IDS)
            if threshold == 0:
                shops_open = 4
            else:
                shops_open = 1 + min(3, beaten // threshold)
            ctx.ui.update_shop_status(gems_avail, shops_open)

    if hasattr(ctx.ui, "update_trap_status"):
        # Auto-derive trap_type -> display name from Items.py.  New traps
        # added there flow through automatically — no edit needed here.
        # Strips the "Trap: " prefix so the GUI shows just the GP name.
        from ..items.Items import Trap as _Trap
        _TRAP_NAMES = {
            it.type.trap_type: (it.item_name[6:] if it.item_name.startswith("Trap: ") else it.item_name)
            for it in aomItemData
            if it.type_data == _Trap
        }
        queue = ctx.game_ctx.trap_queue
        next_name = _TRAP_NAMES.get(queue[0], f"Trap {queue[0]}") if queue else ""
        ctx.ui.update_trap_status(len(queue), next_name)

    if hasattr(ctx.ui, "update_scenarios_view"):
        scenario_to_key_id        = getattr(ctx.game_ctx, "scenario_to_key_id", {}) or {}
        scenario_to_ring_item_id  = getattr(ctx.game_ctx, "scenario_to_ring_item_id", {}) or {}
        ring_display_names        = getattr(ctx.game_ctx, "ring_display_names", {}) or {}
        mk = int(getattr(ctx.game_ctx, "max_keys_on_keyrings", 0))
        # Per-scenario gate item id — Scenario Key when mk==1, Key Ring when mk>=2.
        if mk == 1:
            scenario_to_gate_id = scenario_to_key_id
            gate_display_names  = {kid: f"key {kid}" for kid in scenario_to_key_id.values()}
        else:
            scenario_to_gate_id = scenario_to_ring_item_id
            gate_display_names  = ring_display_names
        received  = set(ctx.game_ctx.received_items)
        held_gates = {iid for iid in scenario_to_gate_id.values() if iid in received}
        from ..items.Items import aomItemData as _IData
        threshold_val = getattr(ctx, "_x_scenarios_threshold", None)
        beaten = _count_beaten_scenarios(ctx)
        has_atlantis_now = (_IData.ATLANTIS_KEY.id in received) or (
            threshold_val is not None and beaten >= threshold_val
        )
        campaign_unlocked_by_id = {
            1: _IData.GREEK_SCENARIOS.id    in received,
            2: _IData.EGYPTIAN_SCENARIOS.id in received,
            3: _IData.NORSE_SCENARIOS.id    in received,
            4: has_atlantis_now,
            5: _IData.UNLOCK_NEW_ATLANTIS.id in received,
            6: _IData.UNLOCK_GOLDEN_GIFT.id  in received,
        }
        disabled_ids = set(getattr(ctx, "_disabled_campaign_ids", set()))
        
        # Build scenario_to_god mapping
        scenario_to_god = {}
        god_names = {
            1: "Zeus",   2: "Poseidon", 3: "Hades",
            4: "Isis",   5: "Ra",       6: "Set",
            7: "Odin",   8: "Thor",     9: "Loki",
            10: "Kronos", 11: "Oranos", 12: "Gaia",
            13: "Demeter", 14: "Freyr",
            15: "Nuwa", 16: "Fuxi", 17: "Shennong",
            18: "Amaterasu", 19: "Tsukuyomi", 20: "Susanoo",
            21: "Huitzilopochtli", 22: "Tezcatlipoca", 23: "Quetzalcoatl",
        }
        god_assignments = getattr(ctx.game_ctx, "god_assignments", {}) or {}
        for scenario_id, god_id in god_assignments.items():
            if god_id in god_names:
                scenario_to_god[scenario_id] = god_names[god_id]
        
        # Build scenario_check_counts mapping.
        # _display_checks  = locally sent + server-confirmed (covers released/force-checked locs)
        # _pool_loc_ids     = every location ID the server actually placed in the pool for this
        #                     slot.  Using this as the "total" source means any location removed
        #                     at generation time (relicsanity off, excluded objectives, etc.) is
        #                     automatically excluded from the count without needing to mirror
        #                     every generation-side option in the client.
        _display_checks = ctx.game_ctx.sent_checks | ctx.game_ctx.server_known_checks
        _pool_loc_ids   = ctx.missing_locations | ctx.checked_locations
        scenario_check_counts = {}
        from ..locations.Locations import SCENARIO_TO_LOCATIONS, aomLocationType
        from ..locations.Scenarios import aomScenarioData
        # Only count check-worthy location types (OBJECTIVE, VICTORY, RELIC).
        # COMPLETION locations are never checks; filtering by type keeps the count
        # consistent with what the player sees in-game.
        _check_types = (aomLocationType.OBJECTIVE, aomLocationType.VICTORY, aomLocationType.RELIC)
        for scenario in aomScenarioData:
            locations = SCENARIO_TO_LOCATIONS.get(scenario, [])
            # Intersect with the server pool so only locations that were actually
            # generated for this slot contribute to found and total.
            pool_locs  = [l for l in locations if l.type in _check_types
                          and l.id in _pool_loc_ids]
            total_checks = len(pool_locs)
            found_checks = len([l for l in pool_locs if l.id in _display_checks])
            if total_checks > 0:
                scenario_check_counts[scenario.global_number] = (found_checks, total_checks)
        
        # Full gate 1-5 in-logic replica: reuse the generation-side rule math
        # against a name→count multiset of the player's received items so the
        # GUI can flag scenarios that are reachable right now.
        scenario_in_logic = {}
        try:
            from ..items.Items import ID_TO_ITEM
            from ..rules.Rules import compute_scenarios_in_logic
            from collections import Counter
            received_counts = Counter()
            for _iid in ctx.game_ctx.received_items:
                _it = ID_TO_ITEM.get(_iid)
                if _it is not None:
                    received_counts[_it.item_name] += 1
            scenario_in_logic = compute_scenarios_in_logic(
                received_counts,
                god_assignments,
                campaign_unlocked_by_id,
                scenario_to_gate_id,
                held_gates,
                mk,
                disabled_ids,
                minor_god_assignments=getattr(
                    ctx.game_ctx, "minor_god_assignments", {}
                ),
            )
        except Exception as _ex:
            import logging
            logging.getLogger(__name__).warning(f"in-logic computation failed: {_ex}")

        ctx.ui.update_scenarios_view(
            mk, scenario_to_gate_id, gate_display_names,
            held_gates, campaign_unlocked_by_id, disabled_ids,
            scenario_to_god, scenario_check_counts,
            scenario_in_logic,
        )

    if hasattr(ctx.ui, "update_civs_view"):
        excluded_civs = getattr(ctx, "_excluded_civs", frozenset())
        random_major_gods = getattr(ctx.game_ctx, "random_major_gods", False)
        received_ids = list(ctx.game_ctx.received_items)
        ctx.ui.update_civs_view(
            received_ids=received_ids,
            excluded_civs=excluded_civs,
            random_major_gods=random_major_gods,
        )

    if hasattr(ctx.ui, "update_gem_shop_view"):
        from .GameClient import GEM_ITEM_ID, VICTORY_LOCATION_IDS
        gc = ctx.game_ctx
        if not gc.gem_shop_enabled:
            ctx.ui.update_gem_shop_view(
                gem_shop_enabled=False,
                gems_available=0, threshold=0, beaten_count=0,
                shop_item_details={}, shop_hint_config={},
                shop_slot_order=[], shop_obelisk_assignments={},
                purchased_slots=set(), info_level=0,
            )
        else:
            from ..items.Items import aomItemData as _ID
            PROG_INFO_ID = _ID.PROGRESSIVE_SHOP_INFO.id
            gems_earned = sum(1 for i in gc.received_items if i == GEM_ITEM_ID)
            gems_spent  = len(gc.purchased_slots)
            gems_avail  = max(0, gems_earned - gems_spent)
            threshold   = gc.wins_to_open_shop
            beaten      = len((gc.sent_checks | gc.server_known_checks) & VICTORY_LOCATION_IDS)
            info_level  = min(4, sum(1 for i in gc.received_items if i == PROG_INFO_ID))
            ctx.ui.update_gem_shop_view(
                gem_shop_enabled=True,
                gems_available=gems_avail,
                threshold=threshold,
                beaten_count=beaten,
                shop_item_details=gc.shop_item_details,
                shop_hint_config=gc.shop_hint_config,
                shop_slot_order=gc.shop_slot_order,
                shop_obelisk_assignments=gc.shop_obelisk_assignments,
                purchased_slots=set(gc.purchased_slots),
                info_level=info_level,
                shop_e_enabled=bool(gc.shop_e_enabled),
                shop_e_decks=gc.shop_e_decks,
                on_buy_clicked=lambda sid: _ap_client_buy_shop_slot(ctx, sid),
                on_buy_e_card=lambda di, lid, kind: _ap_client_buy_shop_e_card(ctx, di, lid, kind),
            )

    if hasattr(ctx.ui, "update_relics_view"):
        relicsanity = getattr(ctx.game_ctx, "relicsanity_enabled", False)
        checked_locs = (getattr(ctx.game_ctx, "sent_checks", set())
                        | getattr(ctx.game_ctx, "server_known_checks", set()))
        disabled_ids = set(getattr(ctx, "_disabled_campaign_ids", set()))
        ctx.ui.update_relics_view(
            relicsanity=relicsanity,
            checked_locs=checked_locs,
            disabled_campaign_ids=disabled_ids,
            campaign_unlocked_by_id=campaign_unlocked_by_id,
            scenario_in_logic=locals().get("scenario_in_logic", {}),
        )


def _format_progress(ctx: "AoMContext") -> str:

    """
    Returns a human-readable progress string for beat_x_scenarios mode.
    Returns an empty string if the mode is not active.
    """
    threshold = getattr(ctx, "_x_scenarios_threshold", None)
    if threshold is None:
        return ""
    beaten = _count_beaten_scenarios(ctx)
    if beaten >= threshold:
        return f"Scenarios beaten: {beaten} / {threshold} — Atlantis is Open!"
    return f"Scenarios beaten: {beaten} / {threshold}"


class AoMCommandProcessor(ClientCommandProcessor):

    ctx: "AoMContext"

    def _cmd_status(self) -> None:
        """Print current client status and scenario progress."""
        ctx = self.ctx
        self.output(f"User folder: {ctx.game_ctx.user_folder}")
        self.output(f"Items received: {len(ctx.game_ctx.received_items)}")
        self.output(f"Checks sent: {len(ctx.game_ctx.sent_checks)}")
        progress = _format_progress(ctx)
        if progress:
            self.output(progress)
        elif getattr(ctx, "_x_scenarios_threshold", None) is None:
            self.output("Final section mode: not beat_x_scenarios (no progress tracking)")

    def _cmd_scenarios(self) -> None:
        """List scenario completion status by category, with section unlock summary."""
        from ..locations.Locations import aomLocationData, aomLocationType
        from ..locations.Scenarios import aomScenarioData
        from ..items.Items import aomItemData

        ctx = self.ctx
        # Union of locally-sent and server-confirmed covers force-released locations.
        sent     = ctx.game_ctx.sent_checks | ctx.game_ctx.server_known_checks
        received = set(ctx.game_ctx.received_items)

        # Build per-scenario stats
        scenario_stats: dict = {}
        for scenario in aomScenarioData:
            scenario_stats[scenario] = {"checked": 0, "total": 0, "beaten": False}

        for loc in aomLocationData:
            if loc.type == aomLocationType.COMPLETION:
                continue
            stats = scenario_stats[loc.scenario]
            if loc.type == aomLocationType.VICTORY:
                if loc.id in sent:
                    stats["beaten"] = True
            else:
                stats["total"] += 1
                if loc.id in sent:
                    stats["checked"] += 1

        # Section unlock status
        has_greek    = aomItemData.GREEK_SCENARIOS.id    in received
        has_egyptian = aomItemData.EGYPTIAN_SCENARIOS.id in received
        has_norse    = aomItemData.NORSE_SCENARIOS.id    in received
        has_atlantis = aomItemData.ATLANTIS_KEY.id       in received
        has_na       = aomItemData.UNLOCK_NEW_ATLANTIS.id in received
        has_gg       = aomItemData.UNLOCK_GOLDEN_GIFT.id  in received
        threshold    = getattr(ctx, "_x_scenarios_threshold", None)
        beaten_count = _count_beaten_scenarios(ctx)
        if not has_atlantis and threshold is not None and beaten_count >= threshold:
            has_atlantis = True

        # Campaign IDs: 1=FOTT Greek, 2=FOTT Egyptian, 3=FOTT Norse, 5=New Atlantis, 6=Golden Gift
        disabled_ids: set[int] = getattr(ctx, "_disabled_campaign_ids", set())

        # Campaign block summary
        def block_line(name: str, unlocked: bool, extra: str = "") -> str:
            icon   = "v" if unlocked else "X"
            status = "Unlocked" if unlocked else "Locked"
            suffix = f" ({extra})" if extra else ""
            return f"  [{icon}] {name}: {status}{suffix}"

        if threshold is not None:
            final_extra = f"{beaten_count}/{threshold} missions beaten"
        elif not has_atlantis:
            final_extra = "find the Atlantis Key"
        else:
            final_extra = ""

        self.output("Campaign Blocks:")
        if 1 not in disabled_ids:
            self.output(block_line("Greek Scenarios",        has_greek))
        if 2 not in disabled_ids:
            self.output(block_line("Egyptian Scenarios",     has_egyptian))
        if 3 not in disabled_ids:
            self.output(block_line("Norse Scenarios",        has_norse))
        self.output(block_line("Final Scenarios",            has_atlantis, final_extra))
        if 5 not in disabled_ids:
            self.output(block_line("New Atlantis Scenarios", has_na))
        if 6 not in disabled_ids:
            self.output(block_line("Golden Gift Scenarios",  has_gg))

        # Sort scenarios into categories.
        # Beaten = victory sent. In Progress = any checked AND any missing (including beaten with missing).
        beaten_list    = []
        in_progress    = []
        untouched_list = []

        for scenario in aomScenarioData:
            if scenario.campaign.id in disabled_ids:
                continue
            stats    = scenario_stats[scenario]
            name     = scenario.display_name
            missing  = stats["total"] - stats["checked"]
            if stats["beaten"]:
                beaten_list.append(name)
                if missing > 0:
                    in_progress.append(f"{name} ({stats['checked']}/{stats['total']} checks — beaten, {missing} missing)")
            elif stats["checked"] > 0:
                in_progress.append(f"{name} ({stats['checked']}/{stats['total']} checks)")
            else:
                untouched_list.append(name)

        self.output(f"=== Beaten ({len(beaten_list)}) ===")
        for name in beaten_list:
            self.output(f"  {name}")

        self.output(f"=== In Progress ({len(in_progress)}) ===")
        for entry in in_progress:
            self.output(f"  {entry}")

        self.output(f"=== Not Started ({len(untouched_list)}) ===")
        for name in untouched_list:
            self.output(f"  {name}")

        # Per-scenario unlock status — only meaningful when max_keys_on_keyrings > 0.
        mk = int(getattr(ctx.game_ctx, "max_keys_on_keyrings", 0))
        if mk > 0:
            scenario_to_key_id        = getattr(ctx.game_ctx, "scenario_to_key_id", {}) or {}
            scenario_to_ring_item_id  = getattr(ctx.game_ctx, "scenario_to_ring_item_id", {}) or {}
            ring_item_id_to_scenarios = getattr(ctx.game_ctx, "ring_item_id_to_scenarios", {}) or {}
            ring_display_names        = getattr(ctx.game_ctx, "ring_display_names", {}) or {}

            if mk == 1:
                all_gate_ids    = sorted({iid for iid in scenario_to_key_id.values()})
                held_gates      = {iid for iid in all_gate_ids if iid in received}
                self.output(f"=== Scenario Keys ===")
                self.output(f"  Scenario Keys Found: {len(held_gates)}/{len(all_gate_ids)}")
            else:
                all_gate_ids    = sorted(ring_item_id_to_scenarios.keys())
                held_gates      = {iid for iid in all_gate_ids if iid in received}
                self.output(f"=== Scenario Key Rings (max keys per ring: {mk}) ===")
                self.output(f"  Key Rings Found: {len(held_gates)}/{len(all_gate_ids)}")
                self.output("  Ring legend:")
                for rid in all_gate_ids:
                    rname = ring_display_names.get(rid, f"Ring {rid}")
                    sids  = ring_item_id_to_scenarios.get(rid, [])
                    held_mark = " (held)" if rid in held_gates else ""
                    sid_to_name = {s.global_number: s.display_name for s in aomScenarioData}
                    contents = ", ".join(sid_to_name.get(s, str(s)) for s in sids)
                    self.output(f"    {rname}{held_mark}: {contents}")
            self.output(f"  You Have Keys For:")
            self.output("")

            # Collect every unlocked scenario in aomScenarioData order (which is
            # already sorted by campaign then chapter), then print as a flat list.
            for scenario in aomScenarioData:
                if scenario.campaign.id in disabled_ids:
                    continue
                if mk == 1:
                    gid = scenario_to_key_id.get(scenario.global_number)
                else:
                    gid = scenario_to_ring_item_id.get(scenario.global_number)
                if gid is None or gid not in held_gates:
                    continue
                self.output(f"  {scenario.display_name}")

    # ---------------------------------------------------------------------------
    # Civilization item commands — unit/myth unlocks and age unlocks only
    # ---------------------------------------------------------------------------

    # UNUSED: shadowed by later `_cmd_civ_items` (line ~839) and `_cmd_generic` (line ~868)
    # which use a different signature (culture: str) and don't call `_is_civ_item`.
    # The early definitions below were dead because Python class semantics let the
    # second `def` overwrite the first. Kept (commented) until the maintainer
    # decides which API to keep.
    #
    # @staticmethod
    # def _is_civ_item(item) -> bool:
    #     """True only for items whose type carries a `culture` field (age unlocks,
    #     unit unlocks, myth unit unlocks). Starting army items, hero stat boosts, hero
    #     special effects, hero action boosts, and villager items are generic and
    #     always return False regardless of the unit or hero's in-game civ."""
    #     try:
    #         from ..items.Items import (
    #             UnitUnlockProgression, UnitUnlockUseful, AgeUnlock,
    #             MythUnitUnlockProgression, MythUnitUnlockUseful, MythUnitUnlockFiller,
    #             AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful,
    #             AtlanteanMythUnitUnlock,
    #         )
    #         civ_types = (
    #             UnitUnlockProgression, UnitUnlockUseful, AgeUnlock,
    #             MythUnitUnlockProgression, MythUnitUnlockUseful, MythUnitUnlockFiller,
    #             AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful,
    #             AtlanteanMythUnitUnlock,
    #         )
    #     except ImportError:
    #         return False
    #     return isinstance(item.type, civ_types)
    #
    # def _cmd_civ_items(self, civ_label: str, civ_filter) -> None:
    #     """Generic helper: list received items matching a civ filter."""
    #     ctx = self.ctx
    #     try:
    #         from ..items.Items import aomItemData
    #     except Exception:
    #         self.output("Could not load item data.")
    #         return
    #     received_set = set(ctx.game_ctx.received_items)
    #     matched = [item.item_name for item in aomItemData
    #                if item.id in received_set and civ_filter(item)]
    #     if not matched:
    #         self.output(f"No {civ_label} items received yet.")
    #         return
    #     self.output(f"=== {civ_label} Items Received ({len(matched)}) ===")
    #     for name in matched:
    #         self.output(f"  {name}")

    def _cmd_greek(self) -> None:
        """Show Greek age progress and received civ-specific items.
        Includes: age unlocks, unit unlocks, myth unit unlocks,
        and villager carry capacity items.
        Does NOT include starting army items or hero items (those are generic — use /generic)."""
        ctx = self.ctx
        try:
            from ..items.Items import aomItemData, AgeUnlock
        except Exception:
            self.output("Could not load item data.")
            return
        received_set = set(ctx.game_ctx.received_items)
        age_item = next(
            (it for it in aomItemData
             if isinstance(it.type, AgeUnlock)
             and getattr(it.type, "culture", None) == "Greek"),
            None
        )
        age_count = ctx.game_ctx.received_items.count(age_item.id) if age_item else 0
        age_names = ["Archaic", "Classical", "Heroic", "Mythic"]
        self.output(f"Can reach the Greek {age_names[min(age_count, 3)]} Age")
        items = [it.item_name for it in aomItemData
                 if it.id in received_set
                 and "Age Unlock" not in it.item_name
                 and (
                     getattr(getattr(it, "type", None), "culture", None) == "Greek"
                     or "Greek" in getattr(getattr(it, "type", None), "unit_name", "")
                 )]
        if items:
            self.output(f"Items received ({len(items)}):")
            for name in items:
                self.output(f"  {name}")

    def _cmd_egypt(self) -> None:
        """Show Egyptian age progress and received civ-specific items.
        Includes: age unlocks, unit unlocks, myth unit unlocks,
        and villager carry capacity items.
        Does NOT include starting army items or hero items (those are generic — use /generic)."""
        ctx = self.ctx
        try:
            from ..items.Items import aomItemData, AgeUnlock
        except Exception:
            self.output("Could not load item data.")
            return
        received_set = set(ctx.game_ctx.received_items)
        age_item = next(
            (it for it in aomItemData
             if isinstance(it.type, AgeUnlock)
             and getattr(it.type, "culture", None) == "Egyptian"),
            None
        )
        age_count = ctx.game_ctx.received_items.count(age_item.id) if age_item else 0
        age_names = ["Archaic", "Classical", "Heroic", "Mythic"]
        self.output(f"Can reach the Egyptian {age_names[min(age_count, 3)]} Age")
        items = [it.item_name for it in aomItemData
                 if it.id in received_set
                 and "Age Unlock" not in it.item_name
                 and (
                     getattr(getattr(it, "type", None), "culture", None) == "Egyptian"
                     or "Egyptian" in getattr(getattr(it, "type", None), "unit_name", "")
                 )]
        if items:
            self.output(f"Items received ({len(items)}):")
            for name in items:
                self.output(f"  {name}")

    def _cmd_norse(self) -> None:
        """Show Norse age progress and received civ-specific items.
        Includes: age unlocks, unit unlocks, myth unit unlocks,
        and villager carry capacity items.
        Does NOT include starting army items or hero items (those are generic — use /generic)."""
        ctx = self.ctx
        try:
            from ..items.Items import aomItemData, AgeUnlock
        except Exception:
            self.output("Could not load item data.")
            return
        received_set = set(ctx.game_ctx.received_items)
        age_item = next(
            (it for it in aomItemData
             if isinstance(it.type, AgeUnlock)
             and getattr(it.type, "culture", None) == "Norse"),
            None
        )
        age_count = ctx.game_ctx.received_items.count(age_item.id) if age_item else 0
        age_names = ["Archaic", "Classical", "Heroic", "Mythic"]
        self.output(f"Can reach the Norse {age_names[min(age_count, 3)]} Age")
        items = [it.item_name for it in aomItemData
                 if it.id in received_set
                 and "Age Unlock" not in it.item_name
                 and (
                     getattr(getattr(it, "type", None), "culture", None) == "Norse"
                     or "Norse" in getattr(getattr(it, "type", None), "unit_name", "")
                 )]
        if items:
            self.output(f"Items received ({len(items)}):")
            for name in items:
                self.output(f"  {name}")

    def _cmd_atlantean(self) -> None:
        """Show Atlantean age progress and received civ-specific items.
        Includes: age unlocks, unit unlocks, myth unit unlocks,
        and villager carry capacity items.
        Does NOT include starting army items or hero items (those are generic — use /generic)."""
        ctx = self.ctx
        try:
            from ..items.Items import aomItemData, AgeUnlock
        except Exception:
            self.output("Could not load item data.")
            return
        received_set = set(ctx.game_ctx.received_items)
        age_item = next(
            (it for it in aomItemData
             if isinstance(it.type, AgeUnlock)
             and getattr(it.type, "culture", None) == "Atlantean"),
            None
        )
        age_count = ctx.game_ctx.received_items.count(age_item.id) if age_item else 0
        age_names = ["Archaic", "Classical", "Heroic", "Mythic"]
        self.output(f"Can reach the Atlantean {age_names[min(age_count, 3)]} Age")
        items = [it.item_name for it in aomItemData
                 if it.id in received_set
                 and "Age Unlock" not in it.item_name
                 and (
                     getattr(getattr(it, "type", None), "culture", None) == "Atlantean"
                     or "Atlantean" in getattr(getattr(it, "type", None), "unit_name", "")
                 )]
        if items:
            self.output(f"Items received ({len(items)}):")
            for name in items:
                self.output(f"  {name}")

    # UNUSED: shadowed by later `_cmd_generic` (~line 868). Kept (commented).
    # def _cmd_generic(self) -> None:
    #     """Show received generic items: resources, passive income, starting army items,
    #     hero stat boosts, hero abilities, villager discounts, starting tech items,
    #     gems, and shop info. Starting army items and hero items are generic regardless
    #     of the unit or hero's in-game civilization."""
    #     self._cmd_civ_items("Generic", lambda item: not self._is_civ_item(item))

    def _cmd_chinese(self) -> None:
        """Show Chinese age progress and received civ-specific items.
        Includes: age unlocks, unit unlocks, myth unit unlocks.
        Does NOT include starting army items or hero items (those are generic — use /generic)."""
        self._cmd_civ_progress("Chinese")

    def _cmd_japanese(self) -> None:
        """Show Japanese age progress and received civ-specific items.
        Includes: age unlocks, unit unlocks, myth unit unlocks.
        Does NOT include starting army items or hero items (those are generic — use /generic)."""
        self._cmd_civ_progress("Japanese")

    def _cmd_aztec(self) -> None:
        """Show Aztec age progress and received civ-specific items.
        Includes: age unlocks, unit unlocks, myth unit unlocks.
        Does NOT include starting army items or hero items (those are generic — use /generic)."""
        self._cmd_civ_progress("Aztec")

    def _cmd_civ_progress(self, culture: str) -> None:
        """Shared implementation for /chinese, /japanese, /aztec."""
        ctx = self.ctx
        try:
            from ..items.Items import aomItemData, AgeUnlock
        except Exception:
            self.output("Could not load item data.")
            return
        received_set = set(ctx.game_ctx.received_items)
        age_item = next(
            (it for it in aomItemData
             if isinstance(it.type, AgeUnlock)
             and getattr(it.type, "culture", None) == culture),
            None
        )
        age_count = ctx.game_ctx.received_items.count(age_item.id) if age_item else 0
        age_names = ["Archaic", "Classical", "Heroic", "Mythic"]
        self.output(f"Can reach the {culture} {age_names[min(age_count, 3)]} Age")
        items = [it.item_name for it in aomItemData
                 if it.id in received_set
                 and "Age Unlock" not in it.item_name
                 and (
                     getattr(getattr(it, "type", None), "culture", None) == culture
                     or culture in getattr(getattr(it, "type", None), "unit_name", "")
                 )]
        if items:
            self.output(f"Items received ({len(items)}):")
            for name in items:
                self.output(f"  {name}")

    # Aliases for civ commands
    _cmd_egyptian = _cmd_egypt
    _cmd_atlant   = _cmd_atlantean
    _cmd_atlantis = _cmd_atlantean
    _cmd_china    = _cmd_chinese
    _cmd_japan    = _cmd_japanese
    _cmd_aztecs   = _cmd_aztec
    _cmd_mexica   = _cmd_aztec

    # Aliases for /scenarios
    _cmd_scenario  = _cmd_scenarios
    _cmd_mission   = _cmd_scenarios
    _cmd_missions  = _cmd_scenarios
    _cmd_progress  = _cmd_scenarios



    def _cmd_new_game(self) -> None:
        """Start a fresh playthrough of the current seed+slot. Generates a new
        session UUID so received items, sent checks, shop purchases, and trap
        queue from the previous playthrough are not loaded. The previous
        session's files remain on disk under the same generation folder; use
        /purge_aom_cache to delete them. Must be connected."""
        ctx = self.ctx.game_ctx
        if not ctx.ap_seed or not ctx.ap_slot:
            self.output("Not connected — connect first, then run /new_game.")
            return
        from .GameClient import start_new_session, write_aom_state
        old = ctx.session_id
        new = start_new_session(ctx)
        # Rewrite aom_state.xs immediately so the in-game trigger sees an empty
        # item list; also clear the AI output log so stale AP_CHECK lines from
        # the previous playthrough cannot replay.
        try:
            write_aom_state(ctx)
        except Exception as ex:
            logger.warning(f"Failed to rewrite aom_state.xs after /new_game: {ex}")
        try:
            log_file = ctx.ai_output_file
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.write_bytes(b"")
        except Exception as ex:
            logger.warning(f"Failed to clear AI output log: {ex}")
        ctx.log_start_offset = 0
        self.output(f"New game started. Session {new[:8]}… (was {old[:8] if old else 'none'}…).")
        self.output("Reconnect or rejoin the AP server if items are not refreshed in-game.")

    def _cmd_purge_aom_cache(self) -> None:
        """Delete all cached session state (sent checks, shop state, trap state,
        and session pointers). The ap_randomizer_cache folder itself is kept but
        everything inside it is removed. Use /new_game instead if you only want
        to start a fresh playthrough of the current seed."""
        import shutil
        from pathlib import Path
        from .GameClient import CACHE_DIR_NAME
        cache_root = Path(self.ctx.game_ctx.user_folder) / CACHE_DIR_NAME
        if not cache_root.exists():
            self.output("Cache directory does not exist — nothing to purge.")
            return
        deleted = 0
        errors  = 0
        for child in list(cache_root.iterdir()):
            try:
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
                deleted += 1
            except Exception as ex:
                self.output(f"Failed to delete {child.name}: {ex}")
                errors += 1
        # Clear in-memory session id so the next connect creates a fresh one
        self.ctx.game_ctx.session_id = ""
        if errors == 0:
            self.output(f"Cache purged: {deleted} item(s) removed.")
        else:
            self.output(f"Cache partially purged: {deleted} removed, {errors} failed.")


    def _cmd_fix_aom_folder(self) -> None:
        """Clear the saved AoMR user folder and prompt for a new one.
        Use this if the wrong directory was selected during first-time setup
        (for example, the Steam install folder instead of the AoMR user folder).
        The correct folder is typically here:
        C:\\Users\\[YourName]\\Games\\Age of Mythology Retold\\[SteamID]
        """
        try:
            config_path = Utils.user_path(AOMR_CONFIG_FILE)
            if os.path.exists(config_path):
                os.remove(config_path)
                self.output(f"Removed saved config: {config_path}")
            else:
                self.output(f"No saved config to remove at: {config_path}")
        except Exception as e:
            self.output(f"Could not remove saved config: {e}")
            return

        self.output(
            "Pick your AoMR user folder. The correct folder is typically here: "
            "C:\\Users\\[YourName]\\Games\\Age of Mythology Retold\\[SteamID]"
        )
        folder = AoMContext._prompt_for_folder()
        if not folder:
            self.output("No folder selected. Run /fix_aom_folder again to retry.")
            return
        self.ctx.game_ctx.user_folder = folder
        self.output(f"Saved new AoMR user folder: {folder}")
        self.output("Reconnect (or restart the client) to apply the new folder.")


    def _cmd_gods(self) -> None:
        """Show the randomized major god for each active scenario.
        Only available when Random_Major_Gods is enabled.

        Output format: scenario_name (GodName)
        Example: 1. Omens (Set)
        """
        ctx = self.ctx
        if not ctx.game_ctx.random_major_gods:
            self.output("Random_Major_Gods is not enabled for this seed.")
            return

        god_names = {
            1: "Zeus",   2: "Poseidon", 3: "Hades",
            4: "Isis",   5: "Ra",       6: "Set",
            7: "Odin",   8: "Thor",     9: "Loki",
            10: "Kronos", 11: "Oranos", 12: "Gaia",
            13: "Demeter", 14: "Freyr",
            15: "Nuwa", 16: "Fuxi", 17: "Shennong",
            18: "Amaterasu", 19: "Tsukuyomi", 20: "Susanoo",
            21: "Huitzilopochtli", 22: "Tezcatlipoca", 23: "Quetzalcoatl",
        }
        # Scenario names keyed by APScenarioID.
        # FotT uses IDs 1-32, New Atlantis 501-512, Golden Gift 601-604.
        scenario_names = {
            # Fall of the Trident
            1:"1. Omens",                        2:"2. Consequences",
            3:"3. Scratching the Surface",        4:"4. A Fine Plan",
            5:"5. Just Enough Rope",              6:"6. I Hope This Works",
            7:"7. More Bandits",                  8:"8. Bad News",
            9:"9. Revelation",                    10:"10. Strangers",
            11:"11. The Lost Relic",              12:"12. Light Sleeper",
            13:"13. Tug of War",                  14:"14. Isis, Hear My Plea",
            15:"15. Let's Go",                    16:"16. Good Advice",
            17:"17. The Jackal's Stronghold",     18:"18. A Long Way From Home",
            19:"19. Watch That First Step",       20:"20. Where They Belong",
            21:"21. Old Friends",                 22:"22. North",
            23:"23. The Dwarven Forge",           24:"24. Not From Around Here",
            25:"25. Welcoming Committee",         26:"26. Union",
            27:"27. The Well of Urd",             28:"28. Beneath the Surface",
            29:"29. Unlikely Heroes",             30:"30. All Is Not Lost",
            31:"31. Welcome Back",                32:"32. A Place in My Dreams",
            # New Atlantis
            501:"NA1. A Lost People",             502:"NA2. Atlantis Reborn",
            503:"NA3. Greetings From Greece",     504:"NA4. Odin's Tower",
            505:"NA5. The Ancient Relics",        506:"NA6. Mount Olympus",
            507:"NA7. Betrayal at Sikyos",        508:"NA8. Cerberus",
            509:"NA9. Rampage",                   510:"NA10. Making Amends",
            511:"NA11. Atlantis Betrayed",        512:"NA12. War of the Titans",
            # The Golden Gift
            601:"GG1. Brokk's Journey",           602:"GG2. Eitri's Journey",
            603:"GG3. Fight at the Forge",        604:"GG4. Loki's Temples",
        }

        assignments = ctx.game_ctx.god_assignments
        if not assignments:
            self.output("No god assignments found.")
            return

        disabled_ids: set[int] = getattr(ctx, "_disabled_campaign_ids", set())

        # Group by campaign for readable output; skip disabled campaigns
        # Campaign IDs: 1-4 = FotT (Greek/Egyptian/Norse/Final), 5 = New Atlantis, 6 = Golden Gift
        # FotT scenario IDs 1-32 map to campaigns by range:
        #   1-10 → Greek (1), 11-20 → Egyptian (2), 21-30 → Norse (3), 31-32 → Final (4)
        def _fott_camp(n: int) -> int:
            if n <= 10: return 1
            if n <= 20: return 2
            if n <= 30: return 3
            return 4

        fott_ids = [n for n in range(1, 33)    if n in assignments and _fott_camp(n) not in disabled_ids]
        na_ids   = [n for n in range(501, 513) if n in assignments and 5 not in disabled_ids]
        gg_ids   = [n for n in range(601, 605) if n in assignments and 6 not in disabled_ids]

        def print_group(ids, header):
            if not ids:
                return
            self.output(header)
            for n in ids:
                god_id = assignments[n]
                god    = god_names.get(god_id, "Unknown")
                name   = scenario_names.get(n, str(n))
                self.output(f"  {name} ({god})")

        print_group(fott_ids, "=== Fall of the Trident ===")
        print_group(na_ids,   "=== The New Atlantis ===")
        print_group(gg_ids,   "=== The Golden Gift ===")

        # NOTE: Age expectation display was removed to reduce clutter.
        # To re-enable it, import _SCENARIO_DATA from rules.Rules and add:
        #   start_age_num, min_required_unlocks, _, is_exempt, _ = _SCENARIO_DATA.get(n, (1,0,0.0,True,False))
        #   no_tc     = is_exempt or n == 7
        #   floor_age = ["Archaic","Classical","Heroic","Mythic"][min(min_required_unlocks, 3)]
        #   age_label = "Starting Age Only" if (no_tc or min_required_unlocks == 0) else
        #               f"Must reach {floor_age} ({min_required_unlocks} unlocks, Mythic possible with 3)"
        # Then append f" — {age_label}" to each output line.

    # Alias for /gods
    _cmd_god = _cmd_gods


    # ---------------------------------------------------------------------------
    # Civilization item commands — show unit/myth/age unlock items per civ
    # /generic shows everything else
    # ---------------------------------------------------------------------------

    _CIV_ITEM_TYPES = None  # populated lazily

    def _get_civ_item_types(self):
        """Return the set of type classes that are civ-specific (unit/myth/age unlocks, villager items)."""
        try:
            from ..items.Items import (
                AgeUnlock, UnitUnlockProgression, UnitUnlockUseful,
                MythUnitUnlockProgression, MythUnitUnlockUseful, MythUnitUnlockFiller,
                VillagerCarryCapacity,
            )
            types = (AgeUnlock, UnitUnlockProgression, UnitUnlockUseful,
                     MythUnitUnlockProgression, MythUnitUnlockUseful, MythUnitUnlockFiller,
                     VillagerCarryCapacity)
            try:
                from ..items.Items import (
                    AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful,
                    AtlanteanMythUnitUnlock,
                )
                types = types + (AtlanteanUnitUnlockProgression,
                                 AtlanteanUnitUnlockUseful, AtlanteanMythUnitUnlock)
            except (ImportError, AttributeError):
                pass
            try:
                from ..items.Items import (
                    ChineseUnitUnlockProgression, ChineseUnitUnlockUseful,
                    ChineseMythUnitUnlock,
                )
                types = types + (ChineseUnitUnlockProgression,
                                 ChineseUnitUnlockUseful, ChineseMythUnitUnlock)
            except (ImportError, AttributeError):
                pass
            try:
                from ..items.Items import (
                    JapaneseUnitUnlockProgression, JapaneseUnitUnlockUseful,
                    JapaneseMythUnitUnlock,
                )
                types = types + (JapaneseUnitUnlockProgression,
                                 JapaneseUnitUnlockUseful, JapaneseMythUnitUnlock)
            except (ImportError, AttributeError):
                pass
            try:
                from ..items.Items import (
                    AztecUnitUnlockProgression, AztecUnitUnlockUseful,
                    AztecMythUnitUnlock,
                )
                types = types + (AztecUnitUnlockProgression,
                                 AztecUnitUnlockUseful, AztecMythUnitUnlock)
            except (ImportError, AttributeError):
                pass
            return types
        except (ImportError, AttributeError):
            return ()

    def _cmd_civ_items(self, civ_label: str, culture: str) -> None:
        """List received unit unlocks, myth unit unlocks, and age unlocks for a civ."""
        ctx = self.ctx
        try:
            from ..items.Items import aomItemData
        except Exception:
            self.output("Could not load item data.")
            return

        civ_types = self._get_civ_item_types()
        received_set = set(ctx.game_ctx.received_items)
        matched = []
        for item in aomItemData:
            if item.id not in received_set:
                continue
            t = item.type
            if not isinstance(t, civ_types):
                continue
            if hasattr(t, "culture") and t.culture == culture:
                matched.append(item.item_name)

        count = len(matched)
        self.output(f"=== {civ_label} Items Received ({count}) ===")
        if not matched:
            self.output("  (none)")
        else:
            for name in matched:
                self.output(f"  {name}")

    def _cmd_generic(self) -> None:
        """Show received items that are not unit unlocks, myth unit unlocks, age unlocks, villager items, or traps."""
        ctx = self.ctx
        try:
            from ..items.Items import aomItemData, Victory, Campaign, FinalUnlock, Trap
        except Exception:
            self.output("Could not load item data.")
            return

        civ_types = self._get_civ_item_types()
        skip_types = civ_types
        try:
            skip_types = skip_types + (Victory, Campaign, FinalUnlock, Trap)
        except Exception:
            pass

        received_ids = ctx.game_ctx.received_items
        # Count multiples using a counter
        from collections import Counter
        counts = Counter(received_ids)
        received_set = set(received_ids)

        matched = []
        for item in aomItemData:
            if item.id not in received_set:
                continue
            if isinstance(item.type, skip_types):
                continue
            n = counts[item.id]
            label = f"  {item.item_name}" if n == 1 else f"  {item.item_name} x{n}"
            matched.append(label)

        self.output(f"=== Generic Items Received ({len(matched)}) ===")
        if not matched:
            self.output("  (none)")
        else:
            for line in matched:
                self.output(line)

class AoMContext(CommonContext):
    """Per-connection AP client state.

    Inherits from `CommonContext` (the standard AP framework class).  Owns:
      * `game_ctx`            — `AoMGameContext` from GameClient.py; the half
                                that talks to the running game.
      * `_game_loop_task`     — async task running the log-tail loop and
                                state-file emission loop.
      * cached slot_data fields (random_major_gods, gem_shop, etc.) used by
        the GUI status panel and by the AP-side check tracking.

    `items_handling = 0b111` enables full item handling (received items,
    starting inventory, and items from other players).
    """
    game = AOMR
    command_processor = AoMCommandProcessor
    items_handling = 0b111

    def __init__(self, server_address: Optional[str], password: Optional[str], user_folder: str = ""):
        """Args:
            server_address: AP server URI (e.g. 'archipelago.gg:38281').
            password:       optional server password.
            user_folder:    AoMR user folder path; if empty we'll prompt the
                            user with a folder picker on first connect.
        """
        super().__init__(server_address, password)
        self.game_ctx = AoMGameContext(
            user_folder=user_folder,
            client_interface=self,
        )
        self._game_loop_task: Optional[asyncio.Task] = None

    @staticmethod
    def _prompt_for_folder() -> str:
        """Open a folder picker for the AoMR user folder and validate it.

        Opens the dialog at the standard AoMR base path when it exists, and
        re-prompts with an explanatory message if the chosen folder is not an
        AoMR per-user folder (e.g. the player picked the parent folder or the
        game install directory).  Returns "" if the player cancels."""
        base = _aomr_base_dir()
        initial_dir = str(base) if base.is_dir() else os.path.expanduser("~")

        # One-time info popup before the picker — the file dialog's title bar
        # truncates, so the full instructions go here.
        info_root = tkinter.Tk()
        info_root.withdraw()
        info_root.wm_attributes("-topmost", True)
        try:
            info_root.iconbitmap(str(_ICON_PATH))
        except Exception:
            pass  # icon is optional
        try:
            tkinter.messagebox.showinfo(
                "Select your AoMR folder",
                "Next, pick your Age of Mythology: Retold user folder.\n\n"
                "It is the folder named with a big number (your Steam ID), "
                "usually here:\n\n"
                "C:\\Users\\[YourName]\\Games\\Age of Mythology Retold\\[SteamID]\n\n"
                "It contains these subfolders as well as others:\n"
                "config, Data, Game, mods, scenario, (and more)",
            )
        finally:
            info_root.destroy()

        while True:
            root = tkinter.Tk()
            root.withdraw()
            root.wm_attributes("-topmost", True)
            try:
                root.iconbitmap(str(_ICON_PATH))
            except Exception:
                pass  # icon is optional; don't block folder selection if missing

            folder = tkinter.filedialog.askdirectory(
                title=("Select your AoMR folder with the big number. It's probably here: "
                       "C:\\Users\\[YourName]\\Games\\Age of Mythology Retold\\[SteamID]"),
                initialdir=initial_dir,
                mustexist=True,
            )

            if not folder:
                root.destroy()
                return ""

            # Normalize path separators
            folder = str(folder).replace("/", "\\")

            if _looks_like_aomr_folder(folder):
                root.destroy()
                _save_user_folder(folder)
                return folder

            # Wrong pick — guide the player.  If they selected the parent
            # folder, point them at the Steam-ID subfolder inside it.
            children = _scan_aomr_user_folders(Path(folder))
            if children:
                hint = ("\n\nThat looks like the parent folder. Open it and "
                        "select the subfolder named with your Steam ID:\n\n"
                        f"{children[0]}")
            else:
                hint = ("\n\nThe correct folder is usually:\n\n"
                        f"{base}\\<your Steam ID>\n\n"
                        "It contains these subfolders as well as others:\n"
                        "config, Data, Game, mods, scenario, (and more)")
            tkinter.messagebox.showwarning(
                "Not an AoMR user folder",
                "That folder doesn't look like an Age of Mythology: Retold "
                "user folder." + hint,
            )
            root.destroy()

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict) -> None:
        if cmd == "RoomInfo":
            # Capture seed_name directly from the RoomInfo packet rather than
            # relying on the base class attribute name, which may not yet be set
            # by the time our Connected handler runs.
            self.game_ctx.ap_seed = args.get("seed_name", "") or ""
        if cmd == "Connected":
            self._on_connected(args)
        if cmd == "ReceivedItems":
            self._handle_received_items(args)

    def _on_connected(self, args: dict) -> None:
        slot_data = args.get("slot_data", {})

        # Populate cache identity fields FIRST — cache_folder is derived from these,
        # and all disk state (sent_checks, shop state, trap state) is loaded from it.
        # Using server + seed_name + slot_name + world_id as the cache key guarantees
        # each unique session gets its own subdirectory with no cross-contamination.
        self.game_ctx.ap_server  = getattr(self, "server_address", "") or ""
        self.game_ctx.ap_slot    = getattr(self, "auth",           "") or ""
        self.game_ctx.world_id   = int(slot_data.get("world_id", 0))
        # ap_seed is set by the RoomInfo handler (on_package) before Connected fires;
        # do not overwrite it here — getattr(self, "seed_name") may return "" on
        # some AP versions and would clobber the correctly captured value.

        # Clear all in-memory game state before applying the new session.
        # Without this, received_items from the previous connection persist in
        # memory and get written into aom_state.xs before the new ReceivedItems
        # packet arrives, causing the new slot to start with the old slot's items.
        self.game_ctx.received_items      = []
        self.game_ctx.sent_checks          = set()
        self.game_ctx.server_known_checks  = set()
        self.game_ctx.locked_warning_campaigns = set()
        self.game_ctx.trap_queue           = []
        self.game_ctx.trap_ack_nonce       = 0
        self.game_ctx.purchased_slots      = set()

        server_checks = set(args.get("checked_locations", []))

        # Load persisted state for this session from disk.
        # Because cache_folder is uniquely scoped to server/seed/slot/world_id,
        # a new world always resolves to an empty (non-existent) directory,
        # so stale checks from previous sessions can never load here.
        from .GameClient import (load_sent_checks, load_shop_state,
                                  load_trap_state, load_or_create_session_id)
        # save_sent_checks removed from import — only called from inside GameClient itself.
        # Resolve which replay-session of this generation we belong to. Must
        # happen before any load_* call: cache_folder depends on session_id.
        load_or_create_session_id(self.game_ctx)
        load_sent_checks(self.game_ctx)
        load_shop_state(self.game_ctx)
        load_trap_state(self.game_ctx)

        # If we have locally-tracked checks that the server doesn't know about,
        # the send_msgs call failed previously (transient disconnect, client
        # restart, etc.). Resend them now before updating from the server's list.
        unconfirmed = self.game_ctx.sent_checks - server_checks
        if unconfirmed:
            logger.warning(
                f"Resending {len(unconfirmed)} location(s) the server hasn't acknowledged: {sorted(unconfirmed)}"
            )
            asyncio.create_task(
                self.send_msgs([{"cmd": "LocationChecks", "locations": list(unconfirmed)}])
            )

        # Store server's confirmed checks in a separate set used only for
        # in-memory deduplication. Never merged into sent_checks (which is
        # persisted) — keeping them separate ensures server-known checks are
        # never written to the local cache and cannot contaminate future sessions.
        self.game_ctx.server_known_checks = server_checks

        # Cache slot_data for UI and game state file
        final_mode  = slot_data.get("final_mode", -1)
        x_scenarios = slot_data.get("x_scenarios", 0)
        self._final_mode_value = final_mode
        self._x_scenarios_threshold = int(x_scenarios) if final_mode == 0 else None
        self.game_ctx.final_mode = final_mode
        self.game_ctx.x_scenarios_threshold = int(x_scenarios)
        self.game_ctx.random_major_gods = bool(slot_data.get("random_major_gods", False))
        raw_gods = slot_data.get("god_assignments", {})
        self.game_ctx.god_assignments = {int(k): int(v) for k, v in raw_gods.items()} if raw_gods else {}
        raw_minor = slot_data.get("minor_god_assignments", {})
        self.game_ctx.minor_god_assignments = (
            {int(k): v for k, v in raw_minor.items()} if raw_minor else {}
        )
        raw_full = slot_data.get("minor_god_full", {})
        self.game_ctx.minor_god_full = (
            {int(k): {int(t): v for t, v in tiers.items()} for k, tiers in raw_full.items()}
            if raw_full else {}
        )
        raw_forbids = slot_data.get("archaic_forbids", {})
        self.game_ctx.archaic_forbids = (
            {int(k): v for k, v in raw_forbids.items()} if raw_forbids else {}
        )
        raw_gp = slot_data.get("god_power_assignments", {})
        self.game_ctx.god_power_assignments = (
            {int(k): list(v) for k, v in raw_gp.items()} if raw_gp else {}
        )
        self.game_ctx.gem_shop_enabled      = bool(slot_data.get("gem_shop", True))
        self.game_ctx.relicsanity_enabled   = bool(slot_data.get("relicsanity", False))
        self.game_ctx.wins_to_open_shop     = int(slot_data.get("wins_to_open_shop", 4))
        self._excluded_civs: frozenset[str] = frozenset(slot_data.get("excluded_civs", []))
        self._disabled_campaign_ids: set[int] = set(slot_data.get("disabled_campaigns", []))
        self.game_ctx.shop_obelisk_assignments = slot_data.get("shop_obelisk_assignments", {})
        self.game_ctx.shop_item_details     = {int(k): v for k, v in slot_data.get("shop_item_details", {}).items()}
        self.game_ctx.shop_hint_config      = slot_data.get("shop_hint_config", {})
        # Shop E (gem sink) — list of 4 decks, each a list of card-info dicts.
        # Empty/missing when the budget gate kept E off, or for legacy slots.
        self.game_ctx.shop_e_enabled       = bool(slot_data.get("shop_e_enabled", False))
        self.game_ctx.shop_e_decks         = slot_data.get("shop_e_decks", []) or []

        # Scenario unlock items: per-scenario Scenario Keys (max==1) or Key
        # Rings (max>=2).  See aom/__init__.py::_generate_keyring_assignments.
        self.game_ctx.max_keys_on_keyrings = int(slot_data.get("max_keys_on_keyrings", 0))
        raw_s2k = slot_data.get("scenario_to_key_id", {})
        self.game_ctx.scenario_to_key_id = (
            {int(k): int(v) for k, v in raw_s2k.items()} if raw_s2k else {}
        )
        raw_s2r = slot_data.get("scenario_to_ring_item_id", {})
        self.game_ctx.scenario_to_ring_item_id = (
            {int(k): int(v) for k, v in raw_s2r.items()} if raw_s2r else {}
        )
        raw_r2s = slot_data.get("ring_item_id_to_scenarios", {})
        self.game_ctx.ring_item_id_to_scenarios = (
            {int(k): [int(x) for x in v] for k, v in raw_r2s.items()} if raw_r2s else {}
        )
        raw_rdn = slot_data.get("ring_display_names", {})
        self.game_ctx.ring_display_names = (
            {int(k): str(v) for k, v in raw_rdn.items()} if raw_rdn else {}
        )
        _starter_ring = slot_data.get("starter_ring_item_id", None)
        self.game_ctx.starter_ring_item_id = int(_starter_ring) if _starter_ring else 0
        _raw_ssk = slot_data.get("starter_scenario_key_ids", [])
        self.game_ctx.starter_scenario_key_ids = (
            [int(x) for x in _raw_ssk] if _raw_ssk else []
        )
        raw_kdl = slot_data.get("scenario_to_key_delivery_loc_id", {})
        self.game_ctx.scenario_to_key_delivery_loc_id = (
            {int(k): int(v) for k, v in raw_kdl.items()} if raw_kdl else {}
        )
        # Convenience: ApClient-local mirrors (used by the UI refresh loop).
        self._max_keys_on_keyrings = self.game_ctx.max_keys_on_keyrings
        self._scenario_to_key_id   = self.game_ctx.scenario_to_key_id
        from ..locations.Locations import SHOP_SLOT_ORDER
        self.game_ctx.shop_slot_order       = list(SHOP_SLOT_ORDER)
        _update_atlantis_ui(self)
        # Install trigger files from apworld bundle to user's trigger folder
        _install_trigger_files(self.game_ctx.user_folder)
        # Ensure user.cfg has the required lines for AI echo to function
        _ensure_user_cfg(self.game_ctx.user_folder)
        mods_local = _resolve_mods_local_dir(self.game_ctx.user_folder)
        generate_ap_ai_xs(self.game_ctx, mods_local)
        from .GameClient import write_aom_state
        write_aom_state(self.game_ctx)

        # Start each connection with a fresh AI output log so AP_CHECK lines
        # from previous worlds cannot be replayed into the new session.
        # v0.3.3 previously relied on a byte offset into the existing log,
        # which could still cause current-session checks to be missed if the
        # offset/session state became misaligned. Truncating here lets the
        # runtime parser read the recreated log from byte 0.
        log_file = self.game_ctx.ai_output_file
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.write_bytes(b"")
            logger.info(f"Cleared AI output log for new session: {log_file}")
        except Exception as ex:
            logger.warning(f"Failed to clear AI output log {log_file}: {ex}")

        # After truncating the log, always parse from the beginning of the new
        # session output.
        self.game_ctx.log_start_offset = 0
        self._start_game_loop()

    def _handle_received_items(self, args: dict) -> None:
        index: int = args.get("index", 0)
        items: list[NetworkItem] = args["items"]
        item_ids = []
        for network_item in items:
            item_id = network_item.item
            from ..items.Items import ID_TO_ITEM
            item_data = ID_TO_ITEM.get(item_id)
            if item_data is None:
                logger.warning(f"Unknown item ID received: {item_id}")
                continue
            if item_data.item_name == "Victory":
                Utils.async_start(
                    self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                )
            item_ids.append(item_id)

        # Key Ring fan-out — when a Scenario Key Ring item arrives, queue a
        # LocationChecks on every `Key for ...` virtual location for the
        # scenarios this ring carries.  The server delivers each Scenario
        # Key item back to the player and broadcasts a standard ItemSend
        # event ("test found their <Scenario> Scenario Key (Key for ...)") to
        # every player in the room — same UX as gem-shop purchases.
        # Skipped on the connect-time resend (index==0) to avoid spam; the
        # initial sweep already re-fires LocationChecks for items received
        # before the disconnect, so any keys earned earlier are still claimed.
        if index > 0:
            ring_id_to_scenarios = getattr(
                self.game_ctx, "ring_item_id_to_scenarios", {}
            ) or {}
            scenario_to_kd = getattr(
                self.game_ctx, "scenario_to_key_delivery_loc_id", {}
            ) or {}
            if ring_id_to_scenarios and scenario_to_kd:
                _kd_locs: list[int] = []
                for _rid in item_ids:
                    _sids = ring_id_to_scenarios.get(_rid)
                    if not _sids:
                        continue
                    for _sid in _sids:
                        _kd = scenario_to_kd.get(_sid)
                        # Only check locations the player hasn't already
                        # claimed (avoid duplicate-check warnings from the
                        # server when a ring is re-received during a reconnect).
                        if _kd is not None and _kd not in self.checked_locations:
                            _kd_locs.append(_kd)
                if _kd_locs:
                    Utils.async_start(
                        self.send_msgs([{"cmd": "LocationChecks", "locations": _kd_locs}])
                    )

        # Progressive Wonder notification — when a copy arrives, count the new
        # total and emit a chat line describing the cumulative state.  Tiered
        # wording so the line always reflects the strictly-best perks active.
        # Skipped on connect-time resend (index == 0) to avoid spam.
        PROGRESSIVE_WONDER_ID = 5104
        if index > 0 and PROGRESSIVE_WONDER_ID in item_ids:
            _new_count = self.game_ctx.received_items.count(PROGRESSIVE_WONDER_ID) + \
                         sum(1 for _i in item_ids if _i == PROGRESSIVE_WONDER_ID)
            _new_count = min(_new_count, 6)
            # Build cumulative wording reflecting the strictly-best perks active.
            # Tier scheme:
            #   1 build in Mythic age | 2 -20% cost | 3 +35% build speed
            #   4 build anywhere      | 5 any age   | 6 -40% cost (extra 20%)
            # The placement phrase combines WHERE (anywhere from tier 4) and
            # WHEN (any age from tier 5) — "anywhere" never replaces "any age".
            _perks: list[str] = []
            if _new_count >= 5:
                _perks.append("Wonders can be built anywhere in any age")
            elif _new_count >= 4:
                _perks.append("Wonders can be built anywhere in the Mythic age")
            elif _new_count >= 1:
                _perks.append("Wonders can be built in the Mythic age")
            if _new_count >= 6:
                _perks.append("Wonders cost 40% less")
            elif _new_count >= 2:
                _perks.append("Wonders cost 20% less")
            if _new_count >= 3:
                _perks.append("Wonders build 35% faster")
            _summary = ", ".join(_perks) if _perks else "(no perks yet)"
            logger.info(
                f"{_new_count} Wonder Item{'s' if _new_count != 1 else ''}: {_summary}"
            )

        PROG_INFO_ID = 9997
        old_info_level = self.game_ctx.received_items.count(PROG_INFO_ID)

        if index == 0:
            on_items_received(self.game_ctx, item_ids)
        else:
            combined = self.game_ctx.received_items + item_ids
            on_items_received(self.game_ctx, combined)

        new_info_level = self.game_ctx.received_items.count(PROG_INFO_ID)
        if old_info_level < 4 <= new_info_level:
            logger.info("4th Progressive Shop Info received — sending hints for 5 missions")
            self.send_mission_hints((5, 5))

        # Queue newly received traps — only for incremental updates (index > 0).
        # On full resend (index == 0), load_trap_state already holds the correct
        # persisted queue; adding everything again would inflate it.
        if index > 0:
            from ..items.Items import Trap as _Trap, ID_TO_ITEM
            from .GameClient import save_trap_state, write_aom_state
            new_traps = []
            for _item_id in item_ids:
                _item_data = ID_TO_ITEM.get(_item_id)
                if _item_data is not None and isinstance(_item_data.type, _Trap):
                    new_traps.append(_item_data.type.trap_type)
            if new_traps:
                self.game_ctx.trap_queue.extend(new_traps)
                save_trap_state(self.game_ctx)
                write_aom_state(self.game_ctx)
                logger.debug(f"Traps queued: {new_traps} (total: {len(self.game_ctx.trap_queue)})")

        _update_atlantis_ui(self)

    def send_mission_hints(self, missions_range: tuple) -> None:
        """
        Scout all unchecked locations in a random set of unbeaten scenarios.
        missions_range: (min, max) number of missions to hint.

        Candidate missions are drawn from the entire scenario table
        (`aomScenarioData`) filtered to this player's pool, so every campaign —
        FotT, New Atlantis, Golden Gift, and any future campaign (e.g. Chinese)
        added to `aomScenarioData` / `SCENARIO_TO_LOCATIONS` — is automatically
        eligible.  No campaign or scenario-number range is hardcoded here.
        """
        import random
        from ..locations.Locations import aomLocationData, aomLocationType
        from .GameClient import VICTORY_LOCATION_IDS

        # Find scenarios that haven't been beaten and have unchecked locations
        from ..locations.Scenarios import aomScenarioData
        from ..locations.Locations import SCENARIO_TO_LOCATIONS

        # Restrict to locations that actually exist in this player's pool.
        # Disabled campaigns (e.g., FotT scenarios when the player has them
        # off) are absent from missing_locations; scouting their IDs causes
        # the server to drop the connection.
        valid_loc_ids = self.missing_locations | self.checked_locations

        unbeaten = []
        for scenario in aomScenarioData:
            vic_loc = next((l for l in SCENARIO_TO_LOCATIONS.get(scenario, [])
                            if l.type == aomLocationType.VICTORY), None)
            if vic_loc is None or vic_loc.id not in valid_loc_ids:
                continue
            if vic_loc.id not in self.game_ctx.sent_checks:
                # Find unchecked objective locations for this scenario,
                # filtered to those present in the player's pool.
                unchecked = [l.id for l in SCENARIO_TO_LOCATIONS.get(scenario, [])
                             if l.type == aomLocationType.OBJECTIVE
                             and l.id in valid_loc_ids
                             and l.id not in self.game_ctx.sent_checks]
                if unchecked:
                    unbeaten.append((scenario.global_number, unchecked))

        if not unbeaten:
            logger.info("No hintable mission locations available.")
            return

        count    = random.randint(missions_range[0], missions_range[1])
        chosen   = random.sample(unbeaten, min(count, len(unbeaten)))
        hint_ids = [loc_id for _, locs in chosen for loc_id in locs]

        if not hint_ids:
            return

        async def _do_scout(ids: list[int], mission_nums: list[int]) -> None:
            try:
                await self.send_msgs([{
                    "cmd": "LocationScouts",
                    "locations": ids,
                    "create_as_hint": 2,
                }])
                logger.info(f"Hinted {len(ids)} location(s) across missions {mission_nums}")
            except Exception as ex:
                logger.error(f"Failed to send hint LocationScouts: {ex}")

        mission_nums = [n for n, _ in chosen]
        asyncio.ensure_future(_do_scout(hint_ids, mission_nums))

    async def on_location_received(self, location_id: int) -> None:
        from ..locations.Locations import aomLocationData, aomLocationType

        # Look up this location to determine its type
        loc_data = next((l for l in aomLocationData if l.id == location_id), None)

        locations_to_send = [location_id]

        if loc_data is not None and loc_data.type == aomLocationType.VICTORY:
            # When a Victory check fires, also send the paired Completion check.
            # Completion locations have local_id=1 (victory=0), so completion_id
            # is always victory_id + 1. This grants the FOTT_N Complete event
            # item in the player's AP state, which is required for:
            #   - beat_x_scenarios final section completion-count gate
            #   - always_open / atlantis_key final section tracking
            completion_id = location_id + 1
            locations_to_send.append(completion_id)

            # Print progress and update UI after a scenario victory
            if loc_data.scenario.global_number <= 30:
                progress = _format_progress(self)
                if progress:
                    logger.info(f"[AoMR] {progress}")
                _update_atlantis_ui(self)

        await self.send_msgs([{"cmd": "LocationChecks", "locations": locations_to_send}])

    async def on_locations_received_batch(self, location_ids: list[int]) -> None:
        """Send a batch of LocationChecks in a single message.

        Expands VICTORY locations to also include their paired completion id.
        Used for shop purchases that yield multiple item locations at once,
        avoiding rapid-fire individual LocationChecks messages that have caused
        server disconnects.
        """
        from ..locations.Locations import aomLocationData, aomLocationType

        locations_to_send: list[int] = []
        for loc_id in location_ids:
            locations_to_send.append(loc_id)
            loc_data = next((l for l in aomLocationData if l.id == loc_id), None)
            if loc_data is not None and loc_data.type == aomLocationType.VICTORY:
                locations_to_send.append(loc_id + 1)
                if loc_data.scenario.global_number <= 30:
                    progress = _format_progress(self)
                    if progress:
                        logger.info(f"[AoMR] {progress}")
                    _update_atlantis_ui(self)

        if not locations_to_send:
            return
        await self.send_msgs([{"cmd": "LocationChecks", "locations": locations_to_send}])

    def _start_game_loop(self) -> None:
        if self._game_loop_task is None or self._game_loop_task.done():
            self._game_loop_task = asyncio.create_task(
                game_loop(self.game_ctx), name="AoMRGameLoop"
            )
            logger.info("AoMR game loop started.")


def main(
    connect: Optional[str] = None,
    password: Optional[str] = None,
    name: Optional[str] = None,
) -> None:
    """Entry point invoked by the Archipelago Launcher (see __init__.py
    `run_client`).  Sets up logging, prompts the user for the AoMR user
    folder if not already saved, then launches the async server loop and
    Tk UI.

    Args:
        connect:  optional initial AP server URI (skips the connect prompt)
        password: optional initial server password
        name:     optional initial slot name
    """
    Utils.init_logging("Age Of Mythology Retold Client")

    # Resolve the AoMR user folder before starting the async loop.
    # Order: saved value -> auto-detect (confirmed) -> manual folder picker.
    user_folder = _load_user_folder()
    if not user_folder:
        detected = _autodetect_user_folders()
        if len(detected) == 1 and _confirm_detected_folder(detected[0]):
            user_folder = detected[0]
            _save_user_folder(user_folder)
        else:
            user_folder = AoMContext._prompt_for_folder()

    async def _main(
        connect: Optional[str],
        password: Optional[str],
        name: Optional[str],
        user_folder: str,
    ) -> None:
        parser = get_base_parser()
        args = parser.parse_args()
        ctx = AoMContext(connect or args.connect, password or args.password, user_folder=user_folder)
        ctx.auth = name

        ctx.server_task = asyncio.create_task(server_loop(ctx), name="ServerLoop")
        AoMManager.start_ap_ui(ctx)

        await ctx.exit_event.wait()

        ctx.game_ctx.running = False
        if ctx._game_loop_task and not ctx._game_loop_task.done():
            ctx._game_loop_task.cancel()

        await ctx.shutdown()

    import colorama
    colorama.init()
    asyncio.run(_main(connect, password, name, user_folder))
    colorama.deinit()