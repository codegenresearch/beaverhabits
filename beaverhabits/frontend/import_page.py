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


async def handle_upload(event: events.UploadEventArguments):
    try:
        text = event.content.read().decode("utf-8")
        to_habit_list = await import_from_json(text)

        from_habit_list = await user_storage.get_user_habit_list(event.user)
        if from_habit_list is None:
            from_habit_list = DictHabitList({"habits": []})

        # Determine added, merged, and unchanged habits
        from_ids = {habit.id for habit in from_habit_list.habits}
        to_ids = {habit.id for habit in to_habit_list.habits}
        added_ids = to_ids - from_ids
        unchanged_ids = from_ids & to_ids

        added_habits = [habit for habit in to_habit_list.habits if habit.id in added_ids]
        unchanged_habits = [habit for habit in from_habit_list.habits if habit.id in unchanged_ids]

        # Merge habits
        merged_habit_list = await from_habit_list.merge(to_habit_list)
        await user_storage.save_user_habit_list(event.user, merged_habit_list)

        # Log the operation
        logger.info(
            f"Imported {len(added_habits)} new habits, "
            f"merged {len(unchanged_habits)} existing habits for user {event.user.email}"
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
                ui.button("Yes", on_click=lambda: handle_upload(event).then(dialog.close))
                ui.button("No", on_click=dialog.close)

    menu_header("Import Habits", target=get_root_path())

    ui.upload(on_upload=show_confirmation_dialog, max_files=1).props("accept=.json")
    return