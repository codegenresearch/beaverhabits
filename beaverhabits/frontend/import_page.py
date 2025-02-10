import json
import logging

from nicegui import events, ui

from beaverhabits.app.db import User
from beaverhabits.frontend.components import menu_header
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import HabitList
from beaverhabits.views import user_storage, session_storage

logger = logging.getLogger(__name__)

async def import_from_json(json_text: str) -> HabitList:
    data = json.loads(json_text)
    habit_list = DictHabitList(data)
    if not habit_list.habits:
        raise ValueError("No habits found in the JSON data")
    return habit_list


def import_ui_page(user: User):
    async def handle_upload(e: events.UploadEventArguments):
        try:
            text = e.content.read().decode("utf-8")
            other = await import_from_json(text)

            # Get the current user's habit list
            current = await user_storage.get_user_habit_list(user) or DictHabitList({"habits": []})

            # Convert habits to sets for comparison
            other_ids = {habit.id for habit in other.habits}
            current_ids = {habit.id for habit in current.habits}

            # Determine added, merged, and unchanged habits
            added_ids = other_ids - current_ids
            merged_ids = other_ids & current_ids

            # Merge habits
            for habit in other.habits:
                if habit.id in merged_ids:
                    current_habit = next(h for h in current.habits if h.id == habit.id)
                    current_habit.merge(habit)

            # Add new habits
            current.habits.extend(habit for habit in other.habits if habit.id in added_ids)

            # Save the updated habit list
            await user_storage.save_user_habit_list(user, current)
            session_storage.save_user_habit_list(current)

            # Log the changes
            logger.info(f"Imported {len(added_ids)} new habits, merged {len(merged_ids)} habits.")

            # Notify the user
            ui.notify(
                f"Imported {len(added_ids)} new habits and merged {len(merged_ids)} existing habits",
                position="top",
                color="positive",
            )

        except json.JSONDecodeError:
            logger.error("Import failed: Invalid JSON format")
            ui.notify("Import failed: Invalid JSON format", color="negative", position="top")
        except ValueError as ve:
            logger.error(f"Import failed: {ve}")
            ui.notify(f"Import failed: {ve}", color="negative", position="top")
        except Exception as error:
            logger.error(f"Import failed: {str(error)}", exc_info=True)
            ui.notify(f"Import failed: {str(error)}", color="negative", position="top")

    def confirm_import(e: events.UploadEventArguments):
        with ui.dialog() as dialog, ui.card().classes("w-64"):
            ui.label("Are you sure? All your current habits will be replaced.")
            with ui.row():
                ui.button("Yes", on_click=lambda: handle_upload(e))
                ui.button("No", on_click=dialog.close)

    menu_header("Import Habits", target=get_root_path())

    # Upload: https://nicegui.io/documentation/upload
    ui.upload(on_upload=confirm_import, max_files=1).props("accept=.json")
    return


### Key Changes:
1. **Function Structure**: Moved `handle_upload` inside `import_ui_page` for better encapsulation.
2. **Variable Naming**: Used more concise and meaningful variable names (`other`, `current`, `other_ids`, `current_ids`).
3. **Set Operations**: Used set operations directly to determine added and merged habits.
4. **Logging**: Ensured logging statements are consistent and clear.
5. **User Confirmation Dialog**: Improved the confirmation dialog to clearly communicate the import action.
6. **Error Handling**: Enhanced error logging to capture the context of the failure.
7. **Return Values**: Ensured proper handling of return values and storage operations.