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
    ("ap_init.xs",     "trigger"),   # scenario trigger include
    ("archipelago.xs", "trigger"),   # main AP logic
    ("ap_ai.xs",       "Game\\AI"),  # AI log poller — different destination
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
    """Push the current Atlantis status to the UI label if the UI is ready."""
    if not (hasattr(ctx, "ui") and ctx.ui and hasattr(ctx.ui, "update_atlantis_status")):
        return
    text, green = _get_atlantis_status(ctx)
    ctx.ui.update_atlantis_status(text, green)


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
        if cmd == "Connected":
            self._on_connected(args)
        if cmd == "ReceivedItems":
            self._handle_received_items(args)

    def _on_connected(self, args: dict) -> None:
        # Seed sent_checks so already-found locations aren't re-reported
        self.game_ctx.sent_checks = set(args.get("checked_locations", []))
        # Cache slot_data for UI and game state file
        slot_data = args.get("slot_data", {})
        final_mode  = slot_data.get("final_mode", -1)
        x_scenarios = slot_data.get("x_scenarios", 0)
        self._final_mode_value = final_mode
        self._x_scenarios_threshold = int(x_scenarios) if final_mode == 0 else None
        # Also store on game_ctx so write_aom_state can use them
        self.game_ctx.final_mode = final_mode
        self.game_ctx.x_scenarios_threshold = int(x_scenarios)
        _update_atlantis_ui(self)
        # Install trigger files from apworld bundle to user's trigger folder
        _install_trigger_files(self.game_ctx.user_folder)
        # Ensure user.cfg has the required lines for AI echo to function
        _ensure_user_cfg(self.game_ctx.user_folder)
        mods_local = _resolve_mods_local_dir(self.game_ctx.user_folder)
        generate_ap_ai_xs(self.game_ctx, mods_local)
        from .GameClient import write_aom_state
        write_aom_state(self.game_ctx)
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

        if index == 0:
            # Full resend from server — replace entire list
            on_items_received(self.game_ctx, item_ids)
        else:
            # Incremental — append new items to existing list
            combined = self.game_ctx.received_items + item_ids
            on_items_received(self.game_ctx, combined)
        _update_atlantis_ui(self)

    def on_location_received(self, location_id: int) -> None:
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

        Utils.async_start(
            self.send_msgs([{"cmd": "LocationChecks", "locations": locations_to_send}])
        )

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