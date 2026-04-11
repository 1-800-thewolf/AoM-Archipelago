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
AP_SHOP_PREFIX   = "AP_SHOP:"

GEM_ITEM_ID = 9998  # aomItemData.GEM
SHOP_SCENARIO_ID = 0  # reserved scenario ID for the shop

# Victory location IDs for scenarios 1-31 (scenario 32 is the goal, not a gem).
# campaign_val * 100 + chapter = scenario_id; victory = BASE_ID + scenario_id * 100
_BASE_ID = 0x3B0000
VICTORY_LOCATION_IDS: frozenset = frozenset(
    _BASE_ID + (campaign_val * 100 + chapter) * 100
    for campaign_val, chapters in [(1, range(1,11)), (2, range(1,11)), (3, range(1,11)), (4, range(1,2))]
    for chapter in chapters
)


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
    minor_god_assignments: dict = None   # scenario_id (int) → [tech_name, ...]\n
    archaic_forbids: dict = None         # scenario_id (int) → [unit_name, ...]
    # Shop state
    starting_gems: int = 0
    wins_to_open_shop: int = 5
    purchased_slots: set = field(default_factory=set)   # slot_id strings
    shop_items: dict = field(default_factory=dict)       # slot_id → [placement dicts]
    shop_hints: dict = field(default_factory=dict)       # slot_id → hint config dict
    shop_slot_order: list = field(default_factory=list)  # canonical slot order

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

    # Shop purchase signals — one function per slot, same pattern as APCheck_XXXXX
    lines.append("")
    from ..locations.Locations import SHOP_ITEM_SLOTS, SHOP_HINT_SLOTS
    for tier, slot_name, _ in SHOP_ITEM_SLOTS + SHOP_HINT_SLOTS:
        slot_id = f"{tier}_{slot_name}"
        lines.append(f'void APShopFire_{slot_id}() {{ aiEcho("{AP_SHOP_PREFIX}{slot_id}"); }}')


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

    # Prepend flags at indices 0-5:
    #   [0] = 9001 if Greek Scenarios in items,    else 9000
    #   [1] = 9002 if Egyptian Scenarios in items, else 9000
    #   [2] = 9003 if Norse Scenarios in items,    else 9000
    #   [3] = 9004 if Atlantis Key in items,       else 9000
    #   [4] = 9100 + campaign_id
    #   [5] = 9010 if godsanity is on,             else 9000
    # Real items start at index 6.
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
        9010 if ctx.godsanity else 9000,  # index 5: godsanity flag
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

    # ----------------------------------------------------------------
    # APShopStateInit — sets all shop globals in aom_state.xs.
    # The static archipelago.xs owns APIsSlotPurchased, APGetAvailableGems,
    # APShopGetLabel, and APShopPurchase; they read from these globals.
    # ----------------------------------------------------------------

    gems_earned    = sum(1 for i in ctx.received_items if i == GEM_ITEM_ID)
    gems_spent     = len(ctx.purchased_slots)
    available_gems = max(0, gems_earned - gems_spent)

    lines.append("")
    lines.append("void APShopStateInit()")
    lines.append("{")
    lines.append(f"    gAPShopAvailableGems = {available_gems};")
    lines.append(f"    gAPShopTierThreshold = {ctx.wins_to_open_shop};")
    beaten = len(ctx.sent_checks & VICTORY_LOCATION_IDS)
    lines.append(f"    trQuestVarSet(\"APBeatenScenarios\", {beaten});")
    for slot_id in ctx.shop_slot_order:
        purchased = "true" if slot_id in ctx.purchased_slots else "false"
        lines.append(f"    gAPShopPurchased_{slot_id} = {purchased};")
        # Also set quest variable for trigger condition-based kill-on-reload
        lines.append(f"    trQuestVarSet(\"APPurchased_{slot_id}\", {'1' if slot_id in ctx.purchased_slots else '0'});")
    for slot_id, placements in ctx.shop_items.items():
        if placements:
            # Group by player_name, then by classification within each player
            from collections import defaultdict
            player_cls: dict = defaultdict(lambda: defaultdict(int))
            for p in placements:
                player_cls[p["player_name"]][p["classification"]] += 1
            parts = []
            for player_name, cls_counts in player_cls.items():
                for cls, count in cls_counts.items():
                    parts.append(f"{count} {cls} item(s) for {player_name}")
            label = "\\n".join(parts)
        else:
            label = "Unknown"
        lines.append(f'    gAPShopLabel_{slot_id} = "{label}";')
    for slot_id, hint_cfg in ctx.shop_hints.items():
        player_name = hint_cfg.get("player_name", "?")
        hints_spec  = hint_cfg.get("hints", [])
        parts = []
        for cls, count in hints_spec:
            parts.append(f"{count} {cls} hint(s) for {player_name}")
        label = "\\n".join(parts)
        lines.append(f'    gAPShopLabel_{slot_id} = "{label}";')
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

def save_shop_state(ctx: AoMGameContext) -> None:
    """Persist purchased_slots to a JSON sidecar so state survives client restarts."""
    import json
    try:
        path = ctx.trigger_folder / "ap_shop_state.json"
        path.write_text(json.dumps({"purchased_slots": list(ctx.purchased_slots)}), encoding="utf-8")
    except Exception as ex:
        logger.warning(f"Failed to save shop state: {ex}")


def load_shop_state(ctx: AoMGameContext) -> None:
    """Load persisted purchased_slots from JSON sidecar if it exists."""
    import json
    try:
        path = ctx.trigger_folder / "ap_shop_state.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            ctx.purchased_slots = set(data.get("purchased_slots", []))
            logger.info(f"Loaded shop state: {len(ctx.purchased_slots)} purchased slot(s).")
    except Exception as ex:
        logger.warning(f"Failed to load shop state: {ex}")


def _resolve_shop_signal(ctx: AoMGameContext, slot_id: str) -> list[int]:
    """
    Process a shop purchase signal for the given slot_id.
    For item slots: returns AP location IDs to check.
    For hint slots: fires hint requests and returns empty list.
    Marks the slot as purchased and rewrites aom_state.xs either way.
    """
    if not slot_id:
        logger.warning("Empty shop signal slot_id.")
        return []

    if slot_id in ctx.purchased_slots:
        logger.debug(f"Shop slot {slot_id} already purchased, ignoring duplicate signal.")
        return []

    ctx.purchased_slots.add(slot_id)
    logger.info(f"Shop purchase: {slot_id}")
    save_shop_state(ctx)
    write_aom_state(ctx)
    # Update GUI gems/shops count immediately after purchase
    if ctx.client_interface is not None:
        from .ApClient import _update_atlantis_ui
        _update_atlantis_ui(ctx.client_interface)

    if "ITEM" in slot_id:
        placements = ctx.shop_items.get(slot_id, [])
        loc_ids = [p["location_id"] for p in placements]
        logger.info(f"  → checking {len(loc_ids)} item location(s)")
        return loc_ids

    if "HINT" in slot_id:
        _send_shop_hints(ctx, slot_id)
        return []

    return []


def _send_shop_hints(ctx: AoMGameContext, slot_id: str) -> None:
    """Send hint requests to the AP server for a purchased hint slot."""
    hint_cfg = ctx.shop_hints.get(slot_id)
    if not hint_cfg or ctx.client_interface is None:
        return
    target_player = hint_cfg.get("target_player", 1)
    hints_spec    = hint_cfg.get("hints", [])
    for classification, count in hints_spec:
        ctx.client_interface.request_hint(target_player, classification, count)


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
            if AP_SHOP_PREFIX in line:
                idx      = line.find(AP_SHOP_PREFIX)
                slot_id  = line[idx + len(AP_SHOP_PREFIX):].strip()
                shop_checks = _resolve_shop_signal(ctx, slot_id)
                for loc_id in shop_checks:
                    if loc_id not in ctx.sent_checks:
                        new_checks.append(loc_id)
                        ctx.sent_checks.add(loc_id)
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