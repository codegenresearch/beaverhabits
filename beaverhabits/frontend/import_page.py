import json
import logging
from typing import Set

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
            imported_habit_list = import_from_json(file_content)
            current_habit_list = await user_storage.get_user_habit_list(user)

            if current_habit_list:
                merged_habit_list = await current_habit_list.merge(imported_habit_list)
                added_habits = set(habit.id for habit in imported_habit_list.habits) - set(habit.id for habit in current_habit_list.habits)
                merged_habits = set(habit.id for habit in imported_habit_list.habits).intersection(set(habit.id for habit in current_habit_list.habits))
                unchanged_habits = set(habit.id for habit in current_habit_list.habits) - set(habit.id for habit in imported_habit_list.habits)

                logger.info(f"Imported habits: {len(imported_habit_list.habits)}")
                logger.info(f"Added habits: {len(added_habits)}")
                logger.info(f"Merged habits: {len(merged_habits)}")
                logger.info(f"Unchanged habits: {len(unchanged_habits)}")

                message = (
                    f"Imported {len(imported_habit_list.habits)} habits. "
                    f"Added: {len(added_habits)}, Merged: {len(merged_habits)}, Unchanged: {len(unchanged_habits)}"
                )
            else:
                merged_habit_list = imported_habit_list
                message = f"Imported {len(imported_habit_list.habits)} new habits."

            with ui.dialog() as confirmation_dialog, ui.card().classes("w-64"):
                ui.label(message)
                with ui.row():
                    ui.button("Yes", on_click=lambda: confirmation_dialog.submit("Yes"))
                    ui.button("No", on_click=lambda: confirmation_dialog.submit("No"))

            user_response = await confirmation_dialog
            if user_response == "Yes":
                await user_storage.save_user_habit_list(user, merged_habit_list)
                ui.notify(message, position="top", color="positive")
            else:
                ui.notify("Import cancelled.", position="top", color="info")
        except json.JSONDecodeError:
            ui.notify("Import failed: Invalid JSON format.", color="negative", position="top")
        except Exception as e:
            logger.exception("An error occurred during the import process.")
            ui.notify(f"Import failed: {str(e)}", color="negative", position="top")

    menu_header("Import Habits", target=get_root_path())

    ui.upload(on_upload=handle_file_upload, max_files=1).props("accept=.json")
    return