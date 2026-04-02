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


class AoMCommandProcessor(ClientCommandProcessor):
    ctx: "AoMContext"

    def _cmd_status(self) -> None:
        """Print current client status."""
        ctx = self.ctx
        self.output(f"User folder: {ctx.game_ctx.user_folder}")
        self.output(f"Items received: {len(ctx.game_ctx.received_items)}")
        self.output(f"Checks sent: {len(ctx.game_ctx.sent_checks)}")


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
        # Install trigger files from apworld bundle to user's trigger folder
        _install_trigger_files(self.game_ctx.user_folder)
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

    def on_location_received(self, location_id: int) -> None:
        Utils.async_start(
            self.send_msgs([{"cmd": "LocationChecks", "locations": [location_id]}])
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