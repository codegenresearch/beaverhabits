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


async def handle_upload(e: events.UploadEventArguments, user: User):
    try:
        text = e.content.read().decode("utf-8")
        new_habit_list = await import_from_json(text)

        # Get the current user's habit list
        current_habit_list = await user_storage.get_user_habit_list(user) or DictHabitList({"habits": []})

        # Convert habits to sets for comparison
        new_habits = {habit.id for habit in new_habit_list.habits}
        current_habits = {habit.id for habit in current_habit_list.habits}

        # Determine added, merged, and unchanged habits
        added_habits = [habit for habit in new_habit_list.habits if habit.id in new_habits - current_habits]
        merged_habits = [habit for habit in new_habit_list.habits if habit.id in new_habits & current_habits]
        unchanged_habits = [habit for habit in current_habit_list.habits if habit.id in current_habits - new_habits]

        # Merge habits
        for habit in merged_habits:
            current_habit = next(h for h in current_habit_list.habits if h.id == habit.id)
            current_habit.merge(habit)

        # Add new habits
        current_habit_list.habits.extend(added_habits)

        # Save the updated habit list
        await user_storage.save_user_habit_list(user, current_habit_list)
        session_storage.save_user_habit_list(current_habit_list)

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
    except ValueError as ve:
        logger.error(f"Import failed: {ve}")
        ui.notify(f"Import failed: {ve}", color="negative", position="top")
    except Exception as error:
        logger.error(f"Import failed: {str(error)}")
        ui.notify(f"Import failed: {str(error)}", color="negative", position="top")


def import_ui_page(user: User):
    def confirm_import(e: events.UploadEventArguments):
        with ui.dialog() as dialog, ui.card().classes("w-64"):
            ui.label("Are you sure? All your current habits will be replaced.")
            with ui.row():
                ui.button("Yes", on_click=lambda: handle_upload(e, user))
                ui.button("No", on_click=dialog.close)

    menu_header("Import Habits", target=get_root_path())

    # Upload: https://nicegui.io/documentation/upload
    ui.upload(on_upload=confirm_import, max_files=1).props("accept=.json")
    return


### Key Changes:
1. **Asynchronous Functions**: Made `import_from_json` and `handle_upload` asynchronous.
2. **Error Handling**: Added specific exception handling for `ValueError` when no habits are found.
3. **Data Structures**: Used sets for comparing habits.
4. **Logging**: Ensured logging statements are consistent and clear.
5. **User Confirmation Dialog**: Improved the confirmation dialog to clearly communicate the import action.
6. **Function Naming and Structure**: Maintained consistent function naming and structure.
7. **Return Values**: Ensured proper handling of return values and storage operations.