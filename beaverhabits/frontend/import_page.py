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


def import_from_json(json_text: str) -> HabitList:
    try:
        data = json.loads(json_text)
        habit_list = DictHabitList(data)
        if not habit_list.habits:
            raise ValueError("No habits found in the imported data.")
        return habit_list
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON: %s", e)
        raise
    except Exception as e:
        logger.error("An error occurred while importing habits: %s", e)
        raise


def import_ui_page(user: User):
    async def handle_file_upload(event: events.UploadEventArguments):
        try:
            file_content = event.content.read().decode("utf-8")
            new_habit_list = import_from_json(file_content)
            current_habit_list = await user_storage.get_user_habit_list(user)

            if current_habit_list:
                merged_habit_list = await current_habit_list.merge(new_habit_list)
                added_habits = len(merged_habit_list.habits) - len(current_habit_list.habits)
                logger.info(f"Merged {added_habits} new habits with existing habits.")
                message = f"Merged {added_habits} new habits with your existing habits."
            else:
                merged_habit_list = new_habit_list
                logger.info(f"Imported {len(new_habit_list.habits)} new habits.")
                message = f"Imported {len(new_habit_list.habits)} new habits."

            await user_storage.save_user_habit_list(user, merged_habit_list)
            ui.notify(message, position="top", color="positive")
        except json.JSONDecodeError:
            ui.notify("Import failed: Invalid JSON format.", color="negative", position="top")
            logger.error("Import failed due to invalid JSON format.")
        except Exception as e:
            ui.notify(f"Import failed: {str(e)}", color="negative", position="top")
            logger.error(f"Import failed with an error: {str(e)}")

    def show_confirmation_dialog():
        with ui.dialog() as confirmation_dialog, ui.card().classes("w-64"):
            ui.label("Are you sure? Importing will replace all your current habits.")
            with ui.row():
                ui.button("Yes", on_click=lambda: confirmation_dialog.submit("Yes"))
                ui.button("No", on_click=lambda: confirmation_dialog.submit("No"))
        return confirmation_dialog

    menu_header("Import Habits", target=get_root_path())

    ui.upload(on_upload=handle_file_upload, max_files=1).props("accept=.json")
    return