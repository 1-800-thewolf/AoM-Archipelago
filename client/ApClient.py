import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

import Utils
import tkinter
import tkinter.filedialog
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
            f"Please add these lines manually to {cfg_path}: {missing}"
        )


AOMR = "Age Of Mythology Retold"
AOMR_CONFIG_FILE = "aomr_client.json"


def _load_user_folder() -> str:
    """Load saved user folder from dedicated config file."""
    try:
        config_path = Utils.user_path(AOMR_CONFIG_FILE)
        if os.path.exists(config_path):
            with open(config_path) as f:
                return json.load(f).get("user_folder", "")
    except Exception:
        pass
    return ""


def _save_user_folder(folder: str) -> None:
    """Persist user folder to dedicated config file."""
    try:
        config_path = Utils.user_path(AOMR_CONFIG_FILE)
        with open(config_path, "w") as f:
            json.dump({"user_folder": folder}, f, indent=2)
    except Exception as e:
        print(f"Warning: could not save config: {e}")


def _resolve_mods_local_dir(user_folder: str) -> Path:
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
    Scenarios 1-30 are non-final (global_number <= 30).
    """
    from ..locations.Locations import aomLocationData, aomLocationType
    beaten = 0
    for loc in aomLocationData:
        if loc.type == aomLocationType.VICTORY and loc.scenario.global_number <= 30:
            if loc.id in ctx.game_ctx.sent_checks:
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
        # beat_x_scenarios mode
        beaten = _count_beaten_scenarios(ctx)
        if beaten >= threshold:
            return ("You have the Atlantis Key! Atlantis is Open!", True)
        return (f"Missions Beaten for Atlantis Key: {beaten} / {threshold}", False)

    if final_mode == 2:
        # atlantis_key mode — key is somewhere in the multiworld
        return ("Atlantis Key is out in the multiworld", False)

    if final_mode == 1:
        # always_open
        return ("Atlantis is Open!", True)

    return ("", False)


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
            beaten      = len(ctx.game_ctx.sent_checks & VICTORY_LOCATION_IDS)
            if threshold == 0:
                shops_open = 4
            else:
                shops_open = 1 + min(3, beaten // threshold)
            ctx.ui.update_shop_status(gems_avail, shops_open)

    if hasattr(ctx.ui, "update_trap_status"):
        _TRAP_NAMES = {
            1: "Meteor", 2: "Lightning Storm", 3: "Locust Swarm", 4: "Bolt",
            5: "Spawn Units", 6: "Transform Drops", 7: "Restoration", 8: "Citadel",
            9: "Tornado", 10: "Earthquake", 11: "Curse", 12: "Plague of Serpents",
            13: "Implode", 14: "Tartarian Gate", 15: "Chaos", 16: "Traitor",
            17: "Carnivora", 18: "Spider Lair", 19: "Deconstruction",
            20: "Fimbulwinter", 21: "Flaming Weapons", 22: "Ancestors",
            23: "Pestilence", 25: "Nidhogg",
            26: "Shockwave",
        }
        queue = ctx.game_ctx.trap_queue
        next_name = _TRAP_NAMES.get(queue[0], f"Trap {queue[0]}") if queue else ""
        ctx.ui.update_trap_status(len(queue), next_name)


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
        return f"Scenarios beaten: {beaten} / {threshold} — Atlantis Key unlocked!"
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
        sent     = ctx.game_ctx.sent_checks
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
        threshold    = getattr(ctx, "_x_scenarios_threshold", None)
        beaten_count = _count_beaten_scenarios(ctx)
        if not has_atlantis and threshold is not None and beaten_count >= threshold:
            has_atlantis = True

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
        self.output(block_line("Greek Scenarios",    has_greek))
        self.output(block_line("Egyptian Scenarios", has_egyptian))
        self.output(block_line("Norse Scenarios",    has_norse))
        self.output(block_line("Final Scenarios",    has_atlantis, final_extra))

        # Sort scenarios into categories.
        # Beaten = victory sent. In Progress = any checked AND any missing (including beaten with missing).
        beaten_list    = []
        in_progress    = []
        untouched_list = []

        for scenario in aomScenarioData:
            stats    = scenario_stats[scenario]
            name     = scenario.display_name
            missing  = stats["total"] - stats["checked"]
            if stats["beaten"]:
                beaten_list.append(name)
                if missing > 0:
                    in_progress.append(f"{name} ({stats['checked']}/{stats['total']} objectives — beaten, {missing} missing)")
            elif stats["checked"] > 0:
                in_progress.append(f"{name} ({stats['checked']}/{stats['total']} objectives)")
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

    def _cmd_gods(self) -> None:
        """Show the randomized major god for each scenario (random_major_gods mode only)."""
        ctx = self.ctx
        if not ctx.game_ctx.random_major_gods:
            self.output("Random_Major_Gods is not enabled for this seed.")
            return
        god_names = {
            1: "Zeus",   2: "Poseidon", 3: "Hades",
            4: "Isis",   5: "Ra",       6: "Set",
            7: "Odin",   8: "Thor",     9: "Loki",
            10: "Kronos", 11: "Oranos", 12: "Gaia",
        }
        scenario_names = {
            1:"1. Omens", 2:"2. Consequences", 3:"3. Scratching the Surface",
            4:"4. A Fine Plan", 5:"5. Just Enough Rope", 6:"6. I Hope This Works",
            7:"7. More Bandits", 8:"8. Bad News", 9:"9. Revelation",
            10:"10. Strangers", 11:"11. The Lost Relic", 12:"12. Light Sleeper",
            13:"13. Tug of War", 14:"14. Isis, Hear My Plea", 15:"15. Let's Go",
            16:"16. Good Advice", 17:"17. The Jackal's Stronghold",
            18:"18. A Long Way From Home", 19:"19. Watch That First Step",
            20:"20. Where They Belong", 21:"21. Old Friends", 22:"22. North",
            23:"23. The Dwarven Forge", 24:"24. Not From Around Here",
            25:"25. Welcoming Committee", 26:"26. Union",
            27:"27. The Well of Urd", 28:"28. Beneath the Surface",
            29:"29. Unlikely Heroes", 30:"30. All Is Not Lost",
            31:"31. Welcome Back", 32:"32. A Place in My Dreams",
        }
        self.output("=== Random_Major_Gods God Assignments ===")
        for n in range(1, 33):
            god_id = ctx.game_ctx.god_assignments.get(n, 0)
            god    = god_names.get(god_id, "Unknown")
            name   = scenario_names.get(n, str(n))
            self.output(f"  {name}: {god}")


    # ---------------------------------------------------------------------------
    # Civilization item commands — unit/myth unlocks and age unlocks only
    # ---------------------------------------------------------------------------

    @staticmethod
    def _is_civ_item(item) -> bool:
        """True if item is a civ-specific unit unlock, myth unlock, or age unlock."""
        try:
            from ..items.Items import (
                UnitUnlockProgression, UnitUnlockUseful, AgeUnlock,
                MythUnitUnlockProgression, MythUnitUnlockUseful, MythUnitUnlockFiller,
            )
            civ_types = (UnitUnlockProgression, UnitUnlockUseful, AgeUnlock,
                         MythUnitUnlockProgression, MythUnitUnlockUseful, MythUnitUnlockFiller)
        except ImportError:
            return False
        try:
            from ..items.Items import (
                AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful,
                AtlanteanMythUnitUnlock,
            )
            civ_types = civ_types + (AtlanteanUnitUnlockProgression,
                                     AtlanteanUnitUnlockUseful, AtlanteanMythUnitUnlock)
        except (ImportError, AttributeError):
            pass
        return isinstance(item.type, civ_types)

    def _cmd_civ_items(self, civ_label: str, civ_filter) -> None:
        """Generic helper: list received items matching a civ filter."""
        ctx = self.ctx
        try:
            from ..items.Items import aomItemData
        except Exception:
            self.output("Could not load item data.")
            return
        received_set = set(ctx.game_ctx.received_items)
        matched = [item.item_name for item in aomItemData
                   if item.id in received_set and civ_filter(item)]
        if not matched:
            self.output(f"No {civ_label} items received yet.")
            return
        self.output(f"=== {civ_label} Items Received ({len(matched)}) ===")
        for name in matched:
            self.output(f"  {name}")

    def _cmd_greek(self) -> None:
        """Show Greek age progress and received items."""
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
        """Show Egyptian age progress and received items."""
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
        """Show Norse age progress and received items."""
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
        """Show Atlantean age progress and received items."""
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

    def _cmd_generic(self) -> None:
        """Show received non-civ items: heroes, resources, reinforcements, etc."""
        self._cmd_civ_items("Generic", lambda item: not self._is_civ_item(item))

    # Aliases for /gods
    _cmd_god = _cmd_gods

    # Aliases for civ commands
    _cmd_egyptian = _cmd_egypt
    _cmd_atlant   = _cmd_atlantean
    _cmd_atlantis = _cmd_atlantean

    # Aliases for /scenarios
    _cmd_scenario  = _cmd_scenarios
    _cmd_mission   = _cmd_scenarios
    _cmd_missions  = _cmd_scenarios
    _cmd_progress  = _cmd_scenarios



    def _cmd_purge_aom_cache(self) -> None:
        """Delete all cached session state (sent checks, shop state, trap state).
        Use this as a troubleshooting step if checks or shop items appear incorrectly
        after switching to a new world. The ap_randomizer_cache folder is kept but all
        session subdirectories and their contents are removed."""
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
            if child.is_dir():
                try:
                    shutil.rmtree(child)
                    deleted += 1
                except Exception as ex:
                    self.output(f"Failed to delete {child.name}: {ex}")
                    errors += 1
        if errors == 0:
            self.output(f"Cache purged: {deleted} session folder(s) removed.")
        else:
            self.output(f"Cache partially purged: {deleted} removed, {errors} failed.")


    def _cmd_gods(self) -> None:
        """Show the randomized major god for each scenario (random_major_gods mode only)."""
        ctx = self.ctx
        if not ctx.game_ctx.random_major_gods:
            self.output("Random_Major_Gods is not enabled for this seed.")
            return

        try:
            from ..rules.Rules import _SCENARIO_DATA
        except Exception:
            self.output("Could not load scenario logic data.")
            return

        god_names = {
            1: "Zeus",   2: "Poseidon", 3: "Hades",
            4: "Isis",   5: "Ra",       6: "Set",
            7: "Odin",   8: "Thor",     9: "Loki",
            10: "Kronos", 11: "Oranos", 12: "Gaia",
        }
        # max_unlock_count in _SCENARIO_DATA is the number of age unlocks logic requires (0-3).
        # Exempt scenarios have no age rule → No Age Expected.
        # Non-exempt: if the scenario already starts at or above the required
        # age (start_age_num - 1 >= max_unlock_count), no advancement needed.
        age_names = ["Classical", "Heroic", "Mythic"]
        scenario_names = {
            1:"1. Omens", 2:"2. Consequences", 3:"3. Scratching the Surface",
            4:"4. A Fine Plan", 5:"5. Just Enough Rope", 6:"6. I Hope This Works",
            7:"7. More Bandits", 8:"8. Bad News", 9:"9. Revelation",
            10:"10. Strangers", 11:"11. The Lost Relic", 12:"12. Light Sleeper",
            13:"13. Tug of War", 14:"14. Isis, Hear My Plea", 15:"15. Let's Go",
            16:"16. Good Advice", 17:"17. The Jackal's Stronghold",
            18:"18. A Long Way From Home", 19:"19. Watch That First Step",
            20:"20. Where They Belong", 21:"21. Old Friends", 22:"22. North",
            23:"23. The Dwarven Forge", 24:"24. Not From Around Here",
            25:"25. Welcoming Committee", 26:"26. Union",
            27:"27. The Well of Urd", 28:"28. Beneath the Surface",
            29:"29. Unlikely Heroes", 30:"30. All Is Not Lost",
            31:"31. Welcome Back", 32:"32. A Place in My Dreams",
        }
        self.output("=== Random_Major_Gods God Assignments ===")
        for n in range(1, 33):
            god_id = ctx.game_ctx.god_assignments.get(n, 0)
            god    = god_names.get(god_id, "Unknown")
            name   = scenario_names.get(n, str(n))
            data   = _SCENARIO_DATA.get(n, (1, 0, 0.0, True, False))
            start_age_num, max_unlock_count, _, is_exempt, _ = data
            if is_exempt or max_unlock_count == 0 or (start_age_num - 1) >= max_unlock_count:
                age_label = "No Age Expected"
            else:
                # tier 1→Classical, 2→Heroic, 3→Mythic (capped at start+1 and 3)
                age_tier  = min(max_unlock_count, start_age_num + 1, 3)
                age_label = f"{age_names[age_tier - 1]} Age Expected"
            self.output(f"  {name} ({god} - {age_label})")


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
                VillagerCarryCapacity, VillagerFoodCost,
            )
            types = (AgeUnlock, UnitUnlockProgression, UnitUnlockUseful,
                     MythUnitUnlockProgression, MythUnitUnlockUseful, MythUnitUnlockFiller,
                     VillagerCarryCapacity, VillagerFoodCost)
            try:
                from ..items.Items import (
                    AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful,
                    AtlanteanMythUnitUnlock,
                )
                types = types + (AtlanteanUnitUnlockProgression,
                                 AtlanteanUnitUnlockUseful, AtlanteanMythUnitUnlock)
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
    game = AOMR
    command_processor = AoMCommandProcessor
    items_handling = 0b111

    def __init__(self, server_address: Optional[str], password: Optional[str], user_folder: str = ""):
        super().__init__(server_address, password)
        self.game_ctx = AoMGameContext(
            user_folder=user_folder,
            client_interface=self,
        )
        self._game_loop_task: Optional[asyncio.Task] = None

    @staticmethod
    def _prompt_for_folder() -> str:
        """Open a folder picker dialog and save the result to host.yaml."""
        root = tkinter.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        try:
            root.iconbitmap(str(_ICON_PATH))
        except Exception:
            pass  # icon is optional; don't block folder selection if missing
        folder = tkinter.filedialog.askdirectory(
            title="Select your AoMR user folder (the folder with your Steam ID)",
            mustexist=True,
        )
        root.destroy()

        if not folder:
            return ""

        # Normalize path separators
        folder = str(folder).replace("/", "\\")

        _save_user_folder(folder)

        return folder

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
        self.game_ctx.trap_queue           = []
        self.game_ctx.trap_ack_nonce       = 0
        self.game_ctx.purchased_slots      = set()

        server_checks = set(args.get("checked_locations", []))

        # Load persisted state for this session from disk.
        # Because cache_folder is uniquely scoped to server/seed/slot/world_id,
        # a new world always resolves to an empty (non-existent) directory,
        # so stale checks from previous sessions can never load here.
        from .GameClient import load_sent_checks, save_sent_checks, load_shop_state, load_trap_state
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
        raw_forbids = slot_data.get("archaic_forbids", {})
        self.game_ctx.archaic_forbids = (
            {int(k): v for k, v in raw_forbids.items()} if raw_forbids else {}
        )
        self.game_ctx.gem_shop_enabled      = bool(slot_data.get("gem_shop", True))
        self.game_ctx.starting_gems         = int(slot_data.get("starting_gems", 0))
        self.game_ctx.wins_to_open_shop     = int(slot_data.get("wins_to_open_shop", 4))
        self.game_ctx.shop_obelisk_assignments = slot_data.get("shop_obelisk_assignments", {})
        self.game_ctx.shop_item_details     = {int(k): v for k, v in slot_data.get("shop_item_details", {}).items()}
        self.game_ctx.shop_hint_config      = slot_data.get("shop_hint_config", {})
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
        # Record the current log file size as the session start offset.
        # read_new_checks will only process bytes written after this point,
        # so AP_CHECK lines from previous sessions are never replayed.
        log_file = self.game_ctx.ai_output_file
        self.game_ctx.log_start_offset = log_file.stat().st_size if log_file.exists() else 0
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
                logger.info(f"Traps queued: {new_traps} (total: {len(self.game_ctx.trap_queue)})")

        _update_atlantis_ui(self)

    def send_mission_hints(self, missions_range: tuple) -> None:
        """
        Scout all unchecked locations in a random set of unbeaten scenarios.
        missions_range: (min, max) number of missions to hint.
        """
        import random
        from ..locations.Locations import aomLocationData, aomLocationType
        from .GameClient import VICTORY_LOCATION_IDS

        # Find scenarios that haven't been beaten and have unchecked locations
        from ..locations.Scenarios import aomScenarioData
        from ..locations.Locations import SCENARIO_TO_LOCATIONS

        unbeaten = []
        for scenario in aomScenarioData:
            vic_loc = next((l for l in SCENARIO_TO_LOCATIONS.get(scenario, [])
                            if l.type == aomLocationType.VICTORY), None)
            if vic_loc and vic_loc.id not in self.game_ctx.sent_checks:
                # Find unchecked objective locations for this scenario
                unchecked = [l.id for l in SCENARIO_TO_LOCATIONS.get(scenario, [])
                             if l.type == aomLocationType.OBJECTIVE
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

        asyncio.ensure_future(self.send_msgs([{
            "cmd": "LocationScouts",
            "locations": hint_ids,
            "create_as_hint": 2,
        }]))
        mission_nums = [n for n, _ in chosen]
        logger.info(f"Hinted {len(hint_ids)} location(s) across missions {mission_nums}")

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
            #   - beat_x_scenarios Atlantis Key logic
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
    Utils.init_logging("Age Of Mythology Retold Client")

    # Prompt for folder before starting the async loop
    user_folder = _load_user_folder()
    if not user_folder:
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