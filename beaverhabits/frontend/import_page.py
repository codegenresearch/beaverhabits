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
            to_habit_list = await import_from_json(text)
            from_habit_list = await user_storage.get_user_habit_list(user)

            if from_habit_list:
                merged_habit_list = await from_habit_list.merge(to_habit_list)
                added_habits = set(to_habit_list.habits) - set(from_habit_list.habits)
                merged_habits = set(to_habit_list.habits) & set(from_habit_list.habits)
                unchanged_habits = set(from_habit_list.habits) - set(to_habit_list.habits)
                logger.info(f"Added habits: {len(added_habits)}, Merged habits: {len(merged_habits)}, Unchanged habits: {len(unchanged_habits)}")
            else:
                merged_habit_list = to_habit_list
                added_habits = set(to_habit_list.habits)
                logger.info(f"Added habits: {len(added_habits)}")

            with ui.dialog() as dialog, ui.card().classes("w-64"):
                ui.label(f"Are you sure? This will add {len(added_habits)} new habits and merge {len(merged_habits)} existing habits.")
                with ui.row():
                    ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
                    ui.button("No", on_click=lambda: dialog.submit("No"))

            result = await dialog
            if result != "Yes":
                return

            await user_storage.save_user_habit_list(user, merged_habit_list)
            ui.notify(
                f"Imported {len(to_habit_list.habits)} habits",
                position="top",
                color="positive",
            )
        except json.JSONDecodeError:
            logger.exception("Import failed: Invalid JSON")
            ui.notify("Import failed: Invalid JSON", color="negative", position="top")
        except Exception as error:
            logger.exception(f"Import failed: {str(error)}")
            ui.notify(str(error), color="negative", position="top")

    menu_header("Import", target=get_root_path())

    # Upload: https://nicegui.io/documentation/upload
    ui.upload(on_upload=handle_upload, max_files=1).props("accept=.json")
    return