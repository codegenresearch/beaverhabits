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


def import_from_json(json_text: str) -> HabitList:
    try:
        data = json.loads(json_text)
        habit_list = DictHabitList(data)
        if not habit_list.habits:
            raise ValueError("No habits found in the JSON data")
        return habit_list
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred while importing habits: {e}")
        raise


def display_import_ui(user: User):
    with ui.dialog() as dialog, ui.card().classes("w-64"):
        ui.label("Are you sure? All your current habits will be replaced.")
        with ui.row():
            ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
            ui.button("No", on_click=lambda: dialog.submit("No"))

    async def handle_file_upload(event: events.UploadEventArguments):
        try:
            user_response = await dialog
            if user_response != "Yes":
                return

            file_content = event.content.read().decode("utf-8")
            imported_habit_list = import_from_json(file_content)

            current_habit_list = await user_storage.get_user_habit_list(user)
            if current_habit_list is None:
                current_habit_list = DictHabitList({"habits": []})

            merged_habit_list = await current_habit_list.merge(imported_habit_list)
            await user_storage.save_user_habit_list(user, merged_habit_list)

            ui.notify(
                f"Successfully imported {len(imported_habit_list.habits)} habits",
                position="top",
                color="positive",
            )
            logger.info(f"Imported {len(imported_habit_list.habits)} habits for user {user.email}")

        except json.JSONDecodeError:
            ui.notify("Import failed: Invalid JSON format", color="negative", position="top")
            logger.error("Import failed: Invalid JSON format")
        except Exception as error:
            ui.notify(f"Import failed: {str(error)}", color="negative", position="top")
            logger.error(f"Import failed: {str(error)}")

    menu_header("Import Habits", target=get_root_path())

    ui.upload(on_upload=handle_file_upload, max_files=1).props("accept=.json")
    return