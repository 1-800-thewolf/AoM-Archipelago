import asyncio
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from ..locations.Locations import aomLocationData, aomLocationType, location_id_to_name
from ..items.Items import (
    aomItemData,
    AtlanteanMythUnitUnlock,
    AtlanteanUnitUnlockProgression,
    AtlanteanUnitUnlockUseful,
    MythUnitUnlockFiller,
    MythUnitUnlockProgression,
    MythUnitUnlockUseful,
    UnitUnlockProgression,
    UnitUnlockUseful,
)

logger = logging.getLogger("Client")

# -----------------------------------------------------------------------
# Item → proto unit name mapping
# Used by write_aom_state to generate APForbidItemGatedUnits().
# Only items that gate trainable units are included; resource/hero/etc.
# items have no entry here.
# -----------------------------------------------------------------------

_ITEM_TO_UNITS: dict[int, list[str]] = {}
for _item in aomItemData:
    _t = _item.type
    if isinstance(_t, (UnitUnlockProgression, UnitUnlockUseful,
                       AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful)):
        _ITEM_TO_UNITS[_item.id] = [_t.unit_name]
    elif isinstance(_t, (MythUnitUnlockProgression, MythUnitUnlockUseful,
                         MythUnitUnlockFiller, AtlanteanMythUnitUnlock)):
        _ITEM_TO_UNITS[_item.id] = list(_t.units)

# -----------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------

AI_OUTPUT_FILENAME = "MythRetoldAIOutputPlayer12.txt"

MOD_AI_DIR_NAME = "fott_ap_campaign"
APAI_FILENAME = "ap_ai.xs"

TRIGGER_FOLDER_NAME = "trigger"
AOM_STATE_FILENAME = "aom_state.xs"

AP_CHECK_PREFIX  = "AP_CHECK:"
AP_LOCKED_PREFIX = "AP_LOCKED:"


# -----------------------------------------------------------------------
# Context
# -----------------------------------------------------------------------

@dataclass
class AoMGameContext:
    running: bool = True
    user_folder: str = ""
    received_items: list[int] = field(default_factory=list)
    sent_checks: set[int] = field(default_factory=set)
    last_ai_output_mtime: float = 0.0
    client_interface: object = None
    # Slot data cached on connect for state file logic
    final_mode: int = -1           # 0=beat_x, 1=always_open, 2=atlantis_key
    x_scenarios_threshold: int = 0  # only used when final_mode == 0
    godsanity: bool = False
    god_assignments: dict = None         # scenario_id (int) → major_god int
    minor_god_assignments: dict = None   # scenario_id (int) → [tech_name, ...]
    archaic_forbids: dict = None         # scenario_id (int) → [unit_name, ...]

    @property
    def trigger_folder(self) -> Path:
        return Path(self.user_folder) / TRIGGER_FOLDER_NAME

    @property
    def ai_output_file(self) -> Path:
        # user_folder is e.g. C:/Users/Philip/Games/Age of Mythology Retold/76561198039446386
        # logs are at:         C:/Users/Philip/Games/Age of Mythology Retold/temp/Logs
        return Path(self.user_folder).parent / "temp" / "Logs" / AI_OUTPUT_FILENAME

    @property
    def aom_state_file(self) -> Path:
        return self.trigger_folder / AOM_STATE_FILENAME

    def apai_file(self, mods_local_dir: Path) -> Path:
        # apai.xs must live in the user-level Game\AI folder, not the mod folder.
        # mods_local_dir is e.g. .../76561198039446386/mods/local
        # Game\AI is at       .../76561198039446386/Game/AI
        return Path(self.user_folder) / "Game" / "AI" / APAI_FILENAME


# -----------------------------------------------------------------------
# apai.xs generation
# -----------------------------------------------------------------------

def generate_ap_ai_xs(ctx: AoMGameContext, mods_local_dir: Path) -> None:
    """
    Generate apai.xs from all non-completion location IDs.
    One function per location: APCheck_XXXXXXX() { aiEcho("AP_CHECK:XXXXXXX"); }
    Called once at client startup.
    """
    lines = []
    lines.append("void main()")
    lines.append("{")
    lines.append('    aiEcho("APAI startup.");')
    lines.append("}")
    lines.append("")
    lines.append("rule APHeartbeat")
    lines.append("minInterval 30")
    lines.append("active")
    lines.append("{")
    lines.append('    aiEcho("APAI heartbeat.");')
    lines.append("}")
    lines.append("")

    for location in aomLocationData:
        if location.type == aomLocationType.COMPLETION:
            continue
        loc_id = location.id
        lines.append(f"void APCheck_{loc_id}() {{ aiEcho(\"{AP_CHECK_PREFIX}{loc_id}\"); }}")

    # Locked campaign notification functions
    for campaign in ["Greek", "Egyptian", "Norse", "Final"]:
        lines.append(f'void APLocked_{campaign}() {{ aiEcho("AP_LOCKED:{campaign}"); }}')


    content = "\n".join(lines) + "\n"

    apai_path = ctx.apai_file(mods_local_dir)
    apai_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        apai_path.write_text(content, encoding="utf-8")
        logger.info(f"Generated {apai_path} with {len(lines) - 4} check functions.")
    except Exception as ex:
        logger.error(f"Failed to write apai.xs: {ex}")


# -----------------------------------------------------------------------
# aom_state.xs writing
# -----------------------------------------------------------------------

def _get_has_atlantis(ctx: AoMGameContext, received_set: set) -> int:
    """
    Returns 9004 if the player should have Atlantis access, 9000 otherwise.
    In beat_x_scenarios mode, derives access from the local sent_checks count
    so the game state matches the UI without relying on AP event locations.
    In atlantis_key mode, requires the actual item to be received.
    In always_open mode, always returns 9004.
    """
    ATLANTIS_KEY = 3510
    if ATLANTIS_KEY in received_set:
        return 9004
    if ctx.final_mode == 1:  # always_open
        return 9004
    if ctx.final_mode == 0 and ctx.x_scenarios_threshold > 0:  # beat_x_scenarios
        BASE_ID = 0x3B0000
        from ..locations.Locations import aomLocationData, aomLocationType
        beaten = sum(
            1 for loc in aomLocationData
            if loc.type == aomLocationType.VICTORY
            and loc.scenario.global_number <= 30
            and loc.id in ctx.sent_checks
        )
        if beaten >= ctx.x_scenarios_threshold:
            return 9004
    return 9000


def write_aom_state(ctx: AoMGameContext) -> None:

    """
    Write aom_state.xs to the trigger folder.
    Contains received item IDs, campaign ID, and civ override.
    XS reads this at scenario load time via include.
    """
    count = len(ctx.received_items)
    # XS arrays require size >= 1
    array_size = max(count, 1)

    # Derive campaign_id from the most recently received check location ID
    # location_id = BASE_ID + scenario_id * 100 + local_id
    # campaign_id = (location_id - BASE_ID) // 10000
    BASE_ID = 0x3B0000
    campaign_id = 0
    for loc_id in ctx.sent_checks:
        derived = (loc_id - BASE_ID) // 10000
        if 1 <= derived <= 4:
            campaign_id = derived
            break

    # Prepend 4 campaign unlock flags at indices 0-3:
    #   [0] = 9001 if Greek Scenarios in items,    else 9000
    #   [1] = 9002 if Egyptian Scenarios in items, else 9000
    #   [2] = 9003 if Norse Scenarios in items,    else 9000
    #   [3] = 9004 if Atlantis Key in items,       else 9000
    # Real items start at index 4.
    GREEK_SCENARIOS    = 3500
    EGYPTIAN_SCENARIOS = 3501
    NORSE_SCENARIOS    = 3502
    ATLANTIS_KEY       = 3510
    received_set = set(ctx.received_items)
    flags = [
        9001 if GREEK_SCENARIOS    in received_set else 9000,
        9002 if EGYPTIAN_SCENARIOS in received_set else 9000,
        9003 if NORSE_SCENARIOS    in received_set else 9000,
        _get_has_atlantis(ctx, received_set),
        9100 + campaign_id,  # index 4: campaign ID for age unlock logic
    ]
    items_with_flags = flags + list(ctx.received_items)
    total = len(items_with_flags)

    lines = []
    lines.append("void APInitItems()")
    lines.append("{")
    lines.append(f"    gAPItemCount = {total};")
    lines.append(f"    gAPItems = new int({total}, 0);")
    for i, item_id in enumerate(items_with_flags):
        lines.append(f"    gAPItems[{i}] = {item_id};")
    lines.append("}")

    # Godsanity — APInitGods() sets quest vars for /gods command
    lines.append("")
    lines.append("void APInitGods()")
    lines.append("{")
    for scenario_id in range(1, 33):
        if ctx.godsanity and ctx.god_assignments and scenario_id in ctx.god_assignments:
            god_val = ctx.god_assignments[scenario_id]
        else:
            god_val = 0
        lines.append(f"    trQuestVarSet(\"APGod{scenario_id}\", {god_val});")
    lines.append("}")

    # Godsanity — APInitStartingAgeTechs() grants starting age techs per scenario
    lines.append("")
    lines.append("void APInitStartingAgeTechs()")
    lines.append("{")
    lines.append("    int scenId = trQuestVarGet(\"APScenarioID\");")
    if ctx.godsanity and ctx.minor_god_assignments:
        for scenario_id in range(1, 33):
            techs = ctx.minor_god_assignments.get(scenario_id) or []
            if not techs:
                continue
            lines.append(f"    if (scenId == {scenario_id})")
            lines.append("    {")
            for tech in techs:
                lines.append(f"        trTechSetStatus(1, {tech}, 2);")
            lines.append("    }")
    lines.append("}")

    # APForbidVanillaArchaicUnits — forbids units from vanilla god/civ
    # that should not be available when the assigned god differs.
    lines.append("")
    lines.append("void APForbidVanillaArchaicUnits()")
    lines.append("{")
    lines.append("    int scenId = trQuestVarGet(\"APScenarioID\");")
    if ctx.archaic_forbids:
        for scenario_id, units in ctx.archaic_forbids.items():
            lines.append(f"    if (scenId == {scenario_id})")
            lines.append("    {")
            for unit in units:
                lines.append(f"        trForbidProtounit(1, \"{unit}\");")
            lines.append("    }")
    lines.append("}")

    # APForbidItemGatedUnits — forbids every unit whose unlock item has not yet
    # been received.  Units whose items HAVE been received are not touched at
    # all, so the game's natural civ / age / minor-god prerequisites still apply.
    lines.append("")
    lines.append("void APForbidItemGatedUnits()")
    lines.append("{")
    for item_id, units in _ITEM_TO_UNITS.items():
        if item_id not in received_set:
            for unit in units:
                lines.append(f"    trForbidProtounit(1, \"{unit}\");")
    lines.append("}")

    content = "\n".join(lines) + "\n"

    try:
        ctx.trigger_folder.mkdir(parents=True, exist_ok=True)
        ctx.aom_state_file.write_text(content, encoding="utf-8")
        logger.debug(f"Wrote aom_state.xs with {len(ctx.received_items)} items.")
    except Exception as ex:
        logger.error(f"Failed to write aom_state.xs: {ex}")


# -----------------------------------------------------------------------
# AI output file reading
# -----------------------------------------------------------------------

def read_new_checks(ctx: AoMGameContext) -> list[int]:
    """
    Check if MythRetoldAIOutputPlayer12.txt has been updated since last read.
    If so, parse all AP_CHECK: lines and return new location IDs not yet sent.
    """
    ai_file = ctx.ai_output_file

    if not ai_file.exists():
        return []

    try:
        mtime = ai_file.stat().st_mtime
    except OSError:
        return []

    if mtime <= ctx.last_ai_output_mtime:
        return []

    ctx.last_ai_output_mtime = mtime

    new_checks = []
    try:
        content = ai_file.read_text(encoding="utf-16-le", errors="ignore")
        for line in content.splitlines():
            line = line.strip()
            if AP_LOCKED_PREFIX in line:
                idx = line.find(AP_LOCKED_PREFIX)
                campaign = line[idx + len(AP_LOCKED_PREFIX):].strip()
                logger.warning(f"Archipelago: You need the {campaign} Scenarios item to play this campaign.")
                continue
            if AP_CHECK_PREFIX not in line:
                continue
            idx = line.find(AP_CHECK_PREFIX)
            raw = line[idx + len(AP_CHECK_PREFIX):].strip()
            try:
                loc_id = int(raw)
                if loc_id not in ctx.sent_checks:
                    new_checks.append(loc_id)
                    ctx.sent_checks.add(loc_id)
            except ValueError:
                logger.warning(f"Could not parse location ID from line: {line}")
    except Exception as ex:
        logger.error(f"Failed to read AI output file: {ex}")

    return new_checks


# -----------------------------------------------------------------------
# Items received
# -----------------------------------------------------------------------

def on_items_received(ctx: AoMGameContext, items: list[int]) -> None:
    """
    Called by ApClient when the AP server sends new items.
    Updates received_items and rewrites aom_state.xs.
    """
    ctx.received_items = items
    write_aom_state(ctx)


# -----------------------------------------------------------------------
# Game loop
# -----------------------------------------------------------------------

async def game_loop(ctx: AoMGameContext) -> None:
    """
    Main polling loop. Runs while the client is connected.
    Polls the AI output file every 2 seconds for new checks.
    """
    logger.info("AoMR game loop started. Watching for scenario completions...")
    logger.info(f"Watching file: {ctx.ai_output_file}")
    logger.info("Age of Mythology: Retold client commands:")
    logger.info("  /status              — show connection info and Atlantis Key progress")
    logger.info("  /scenarios (/progress) — list beaten, in-progress, and untouched scenarios")
    logger.info("  /gods                  — show randomized god per scenario (godsanity only)")
    logger.info("  /greek /egypt /norse /atlantean — show unit/myth/age unlock items for that civ")
    logger.info("  /generic               — show all other received items (heroes, resources, etc.)")

    # Seed mtime so we only react to writes that happen AFTER client starts.
    ai_file = ctx.ai_output_file
    if ai_file.exists():
        try:
            ctx.last_ai_output_mtime = ai_file.stat().st_mtime
            pass
        except OSError:
            pass
    while ctx.running:
        new_checks = read_new_checks(ctx)

        if new_checks and ctx.client_interface is not None:
            for loc_id in new_checks:
                loc_name = location_id_to_name.get(loc_id, str(loc_id))
                logger.debug(f"Check found: {loc_name}")
                ctx.client_interface.on_location_received(loc_id)

        await asyncio.sleep(2.0)