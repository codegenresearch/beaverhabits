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
    try:
        data = json.loads(text)
        habit_list = DictHabitList(data)
        if not habit_list.habits:
            raise ValueError("No habits found in the imported data.")
        return habit_list
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON.")
        raise ValueError("Invalid JSON format.")
    except ValueError as e:
        logger.error(f"Failed to import habits: {e}")
        raise


def import_ui_page(user: User):
    async def handle_upload(e: events.UploadEventArguments):
        try:
            text = e.content.read().decode("utf-8")
            imported = await import_from_json(text)
            current = await user_storage.get_user_habit_list(user)

            if current:
                current_ids = {habit.id for habit in current.habits}
                imported_ids = {habit.id for habit in imported.habits}

                added = [habit for habit in imported.habits if habit.id not in current_ids]
                merged = [habit for habit in imported.habits if habit.id in current_ids]
                unchanged = [habit for habit in current.habits if habit.id not in imported_ids]

                logger.info(f"Added: {len(added)}, Merged: {len(merged)}, Unchanged: {len(unchanged)}")
                message = f"Added {len(added)}, Merged {len(merged)} habits."
            else:
                added = imported.habits
                logger.info(f"Imported {len(added)} new habits.")
                message = f"Imported {len(added)} habits."

            await user_storage.save_user_habit_list(user, imported)
            ui.notify(message, position="top", color="positive")
        except ValueError as e:
            ui.notify(str(e), color="negative", position="top")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            ui.notify("An unexpected error occurred.", color="negative", position="top")

    async def confirm_and_upload(e: events.UploadEventArguments):
        with ui.dialog() as dialog, ui.card().classes("w-64"):
            ui.label("Are you sure? Importing will replace all your current habits.")
            with ui.row():
                ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
                ui.button("No", on_click=lambda: dialog.submit("No"))
        result = await dialog
        if result == "Yes":
            await handle_upload(e)

    menu_header("Import Habits", target=get_root_path())

    ui.upload(on_upload=confirm_and_upload, max_files=1).props("accept=.json")
    return


### Changes Made:
1. **Error Handling**: Simplified the exception handling to focus on `json.JSONDecodeError` and `ValueError`.
2. **Variable Naming**: Used more concise variable names (`imported`, `current`, `added`, `merged`, `unchanged`).
3. **Set Operations**: Used set operations to determine added, merged, and unchanged habits.
4. **Logging**: Simplified logging to focus on essential information.
5. **Dialog Handling**: Integrated the confirmation dialog more seamlessly with the upload process.
6. **UI Notifications**: Streamlined notifications to be clear and concise.
7. **Code Structure**: Improved the overall structure for better readability and logical flow.