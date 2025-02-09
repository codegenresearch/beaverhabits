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


async def import_from_json(text: str) -> HabitList:
    try:
        data = json.loads(text)
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


async def handle_upload(event: events.UploadEventArguments, user: User):
    try:
        text = event.content.read().decode("utf-8")
        new_habits = await import_from_json(text)

        current_habits = await user_storage.get_user_habit_list(user)
        if current_habits is None:
            current_habits = DictHabitList({"habits": []})

        # Determine added and unchanged habits
        current_ids = {habit.id for habit in current_habits.habits}
        new_ids = {habit.id for habit in new_habits.habits}
        added_ids = new_ids - current_ids

        added_habits = [habit for habit in new_habits.habits if habit.id in added_ids]
        unchanged_habits = [habit for habit in current_habits.habits if habit.id not in added_ids]

        # Merge habits
        merged_habits = await current_habits.merge(new_habits)
        await user_storage.save_user_habit_list(user, merged_habits)

        # Log the operation
        logger.info(
            f"Imported {len(added_habits)} new habits, "
            f"merged {len(unchanged_habits)} existing habits for user {user.email}"
        )

        # Notify the user
        ui.notify(
            f"Imported {len(added_habits)} new habits and merged {len(unchanged_habits)} existing habits",
            position="top",
            color="positive",
        )

    except json.JSONDecodeError:
        ui.notify("Import failed: Invalid JSON format", color="negative", position="top")
        logger.error("Import failed: Invalid JSON format")
    except Exception as error:
        ui.notify(f"Import failed: {str(error)}", color="negative", position="top")
        logger.error(f"Import failed: {str(error)}")


def import_ui_page(user: User):
    def show_confirmation_dialog(event: events.UploadEventArguments):
        with ui.dialog() as dialog, ui.card().classes("w-64"):
            ui.label("Are you sure? All your current habits will be replaced.")
            with ui.row():
                ui.button("Yes", on_click=lambda: handle_upload(event, user).then(dialog.close))
                ui.button("No", on_click=dialog.close)

    menu_header("Import Habits", target=get_root_path())

    ui.upload(on_upload=show_confirmation_dialog, max_files=1).props("accept=.json")
    return