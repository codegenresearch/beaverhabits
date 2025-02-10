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
            raise ValueError("No habits found in the imported data.")
        return habit_list
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON.")
        raise ValueError("Invalid JSON format.")
    except Exception as e:
        logger.error("An error occurred while importing habits: %s", e)
        raise ValueError("Failed to import habits.")


def import_ui_page(user: User):
    async def handle_upload(event: events.UploadEventArguments):
        try:
            text = event.content.read().decode("utf-8")
            other = await import_from_json(text)
            current = await user_storage.get_user_habit_list(user)

            if current:
                merged = await current.merge(other)
                added = set(habit.id for habit in other.habits) - set(habit.id for habit in current.habits)
                merged_count = len(set(habit.id for habit in other.habits).intersection(set(habit.id for habit in current.habits)))
                unchanged = set(habit.id for habit in current.habits) - set(habit.id for habit in other.habits)

                logger.info(f"Imported habits: {len(other.habits)}")
                logger.info(f"Added: {len(added)}, Merged: {merged_count}, Unchanged: {len(unchanged)}")

                message = (
                    f"Imported {len(other.habits)} habits. "
                    f"Added: {len(added)}, Merged: {merged_count}, Unchanged: {len(unchanged)}"
                )
            else:
                merged = other
                message = f"Imported {len(other.habits)} new habits."

            with ui.dialog() as dialog, ui.card().classes("w-64"):
                ui.label("Are you sure? This will replace your current habits.")
                with ui.row():
                    ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
                    ui.button("No", on_click=lambda: dialog.submit("No"))

            response = await dialog
            if response != "Yes":
                ui.notify("Import cancelled.", position="top", color="info")
                return

            await user_storage.save_user_habit_list(user, merged)
            ui.notify(message, position="top", color="positive")
        except ValueError as ve:
            ui.notify(str(ve), color="negative", position="top")
        except Exception as e:
            logger.exception("An error occurred during the import process.")
            ui.notify("Import failed: An unexpected error occurred.", color="negative", position="top")

    menu_header("Import Habits", target=get_root_path())

    ui.upload(on_upload=handle_upload, max_files=1).props("accept=.json")
    return