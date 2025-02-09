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
    data = json.loads(text)
    habit_list = DictHabitList(data)
    if not habit_list.habits:
        raise ValueError("No habits found in the imported data")
    return habit_list


def import_ui_page(user: User):
    async def handle_upload(event: events.UploadEventArguments):
        try:
            text = event.content.read().decode("utf-8")
            other = await import_from_json(text)

            current = await user_storage.get_user_habit_list(user)
            if current is None:
                current = DictHabitList({"habits": []})

            # Determine added, merged, and unchanged habits
            current_ids = {habit.id for habit in current.habits}
            other_ids = {habit.id for habit in other.habits}
            added_ids = other_ids - current_ids

            added = [habit for habit in other.habits if habit.id in added_ids]
            unchanged = [habit for habit in current.habits if habit.id not in added_ids]

            # Merge habits
            merged = await current.merge(other)
            await user_storage.save_user_habit_list(user, merged)

            # Log the operation
            logger.info(
                f"Imported {len(added)} new habits, "
                f"merged {len(unchanged)} existing habits for user {user.email}"
            )

            # Notify the user
            ui.notify(
                f"Imported {len(added)} new habits and merged {len(unchanged)} existing habits",
                position="top",
                color="positive",
            )

        except json.JSONDecodeError:
            ui.notify("Import failed: Invalid JSON format", color="negative", position="top")
            logger.error("Import failed: Invalid JSON format")
        except Exception as error:
            ui.notify(f"Import failed: {str(error)}", color="negative", position="top")
            logger.error(f"Import failed: {str(error)}")

    def show_confirmation_dialog(event: events.UploadEventArguments):
        with ui.dialog() as dialog, ui.card().classes("w-64"):
            ui.label("Are you sure? All your current habits will be replaced.")
            with ui.row():
                ui.button("Yes", on_click=lambda: handle_upload(event).then(dialog.close))
                ui.button("No", on_click=dialog.close)

    menu_header("Import Habits", target=get_root_path())

    ui.upload(on_upload=show_confirmation_dialog, max_files=1).props("accept=.json")
    return