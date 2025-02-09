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


async def import_from_json(json_text: str) -> HabitList:
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


async def display_import_ui(user: User):
    async def handle_file_upload(event: events.UploadEventArguments):
        try:
            file_content = event.content.read().decode("utf-8")
            other = await import_from_json(file_content)

            current = await user_storage.get_user_habit_list(user)
            if current is None:
                current = DictHabitList({"habits": []})

            # Determine added, merged, and unchanged habits
            current_ids = {habit.id for habit in current.habits}
            other_ids = {habit.id for habit in other.habits}
            added_ids = other_ids - current_ids
            unchanged_ids = current_ids & other_ids

            added_habits = [habit for habit in other.habits if habit.id in added_ids]
            unchanged_habits = [habit for habit in current.habits if habit.id in unchanged_ids]

            # Merge habits
            merged_habit_list = await current.merge(other)
            await user_storage.save_user_habit_list(user, merged_habit_list)

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

    menu_header("Import Habits", target=get_root_path())

    ui.upload(on_upload=handle_file_upload, max_files=1).props("accept=.json")
    return