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
            imported_habits = await import_from_json(text)
            current_habits = await user_storage.get_user_habit_list(user)

            if current_habits:
                merged_habits = await user_storage.merge_user_habit_list(user, imported_habits)
                added_habits = set(imported_habits.habits) - set(current_habits.habits)
                merged_count = len(set(imported_habits.habits) & set(current_habits.habits))
                unchanged_habits = set(current_habits.habits) - set(imported_habits.habits)

                logger.info(f"Added habits: {len(added_habits)}")
                logger.info(f"Merged habits: {merged_count}")
                logger.info(f"Unchanged habits: {len(unchanged_habits)}")
            else:
                merged_habits = imported_habits
                added_habits = set(imported_habits.habits)
                logger.info(f"Added habits: {len(added_habits)}")

            message = f"Are you sure? This will add {len(added_habits)} new habits."
            if current_habits:
                message += f" {merged_count} existing habits will be merged."

            with ui.dialog() as dialog, ui.card().classes("w-64"):
                ui.label(message)
                with ui.row():
                    ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
                    ui.button("No", on_click=lambda: dialog.submit("No"))

            result = await dialog
            if result != "Yes":
                return

            await user_storage.save_user_habit_list(user, merged_habits)
            ui.notify(
                f"Imported {len(imported_habits.habits)} habits",
                position="top",
                color="positive",
            )
        except json.JSONDecodeError:
            logger.error("Import failed: Invalid JSON")
            ui.notify("Import failed: Invalid JSON", color="negative", position="top")
        except Exception as error:
            logger.error(f"Import failed: {str(error)}")
            ui.notify(str(error), color="negative", position="top")

    menu_header("Import", target=get_root_path())

    # Upload: https://nicegui.io/documentation/upload
    ui.upload(on_upload=handle_upload, max_files=1).props("accept=.json")
    return