import json
import logging

from nicegui import events, ui

from beaverhabits.app.db import User
from beaverhabits.frontend.components import menu_header
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import HabitList
from beaverhabits.views import user_storage

logger = logging.getLogger(__name__)

def import_from_json(json_text: str) -> HabitList:
    data = json.loads(json_text)
    habit_list = DictHabitList(data)
    if not habit_list.habits:
        raise ValueError("No habits found in the JSON data")
    return habit_list


def import_ui_page(user: User):
    async def handle_file_upload(event: events.UploadEventArguments):
        try:
            # Get the current user's habit list
            current_habit_list = await user_storage.get_user_habit_list(user)
            if current_habit_list is None:
                current_habit_list = DictHabitList({"habits": []})

            # Convert uploaded JSON to HabitList
            file_content = event.content.read().decode("utf-8")
            new_habit_list = import_from_json(file_content)

            # Compare new habits with current habits
            new_habits = {habit.id: habit for habit in new_habit_list.habits}
            current_habits = {habit.id: habit for habit in current_habit_list.habits}

            added_habits = [habit for habit_id, habit in new_habits.items() if habit_id not in current_habits]
            merged_habits = [habit for habit_id, habit in new_habits.items() if habit_id in current_habits]
            unchanged_habits = [habit for habit_id, habit in current_habits.items() if habit_id not in new_habits]

            # Merge habits
            for habit in merged_habits:
                current_habits[habit.id].merge(habit)

            # Add new habits
            current_habits.update({habit.id: habit for habit in added_habits})

            # Update the user's habit list
            updated_habit_list = DictHabitList({"habits": list(current_habits.values())})
            await user_storage.save_user_habit_list(user, updated_habit_list)

            # Log the changes
            logger.info(f"Imported {len(added_habits)} new habits, merged {len(merged_habits)} habits, and kept {len(unchanged_habits)} unchanged habits.")

            # Notify the user
            ui.notify(
                f"Imported {len(added_habits)} new habits and merged {len(merged_habits)} existing habits",
                position="top",
                color="positive",
            )

        except json.JSONDecodeError:
            logger.error("Import failed: Invalid JSON format")
            ui.notify("Import failed: Invalid JSON format", color="negative", position="top")
        except Exception as error:
            logger.error(f"Import failed: {str(error)}")
            ui.notify(f"Import failed: {str(error)}", color="negative", position="top")

    menu_header("Import Habits", target=get_root_path())

    # Upload: https://nicegui.io/documentation/upload
    ui.upload(on_upload=handle_file_upload, max_files=1).props("accept=.json")
    return