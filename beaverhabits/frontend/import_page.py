import json
import logging

from nicegui import events, ui

from beaverhabits.app.db import User
from beaverhabits.frontend.components import menu_header
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import HabitList
from beaverhabits.views import user_storage

# Setting up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def import_from_json(text: str) -> HabitList:
    data = json.loads(text)
    habit_list = DictHabitList(data)
    if not habit_list.habits:
        raise ValueError("No habits found")
    return habit_list


def import_ui_page(user: User):
    async def handle_upload(e: events.UploadEventArguments):
        try:
            text = e.content.read().decode("utf-8")
            other = await import_from_json(text)
            current = await user_storage.get_user_habit_list(user)

            if current:
                merged = await current.merge(other)
                added = set(other.habits) - set(current.habits)
                unchanged = set(current.habits) - set(other.habits)
                logger.info(f"Added: {len(added)}, Unchanged: {len(unchanged)}")
            else:
                merged = other
                added = set(other.habits)
                logger.info(f"Added: {len(added)}")

            with ui.dialog() as dialog, ui.card().classes("w-64"):
                ui.label(f"Are you sure? This will add {len(added)} new habits.")
                with ui.row():
                    ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
                    ui.button("No", on_click=lambda: dialog.submit("No"))

            result = await dialog
            if result != "Yes":
                return

            await user_storage.save_user_habit_list(user, merged)
            ui.notify(
                f"Imported {len(other.habits)} habits",
                position="top",
                color="positive",
            )
        except json.JSONDecodeError:
            logger.exception("Import failed: Invalid JSON")
            ui.notify("Import failed: Invalid JSON", color="negative", position="top")
        except Exception as error:
            logger.exception("Import failed")
            ui.notify(str(error), color="negative", position="top")

    menu_header("Import", target=get_root_path())

    # Upload: https://nicegui.io/documentation/upload
    ui.upload(on_upload=handle_upload, max_files=1).props("accept=.json")
    return