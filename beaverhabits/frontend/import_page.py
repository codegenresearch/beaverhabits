import json

from nicegui import events, ui

from beaverhabits.app.db import User
from beaverhabits.frontend.components import menu_header
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import HabitList
from beaverhabits.views import user_storage


def import_habit_list_from_json(json_text: str) -> HabitList:
    data = json.loads(json_text)
    habit_list = DictHabitList(data)
    if not habit_list.habits:
        raise ValueError("No habits found in the imported data.")
    return habit_list


def import_habit_list_ui_page(user: User):
    with ui.dialog() as confirmation_dialog, ui.card().classes("w-64"):
        ui.label("Are you sure? Importing will replace all your current habits.")
        with ui.row():
            ui.button("Yes", on_click=lambda: confirmation_dialog.submit("Yes"))
            ui.button("No", on_click=lambda: confirmation_dialog.submit("No"))

    async def handle_file_upload(event: events.UploadEventArguments):
        try:
            user_response = await confirmation_dialog
            if user_response != "Yes":
                return

            file_content = event.content.read().decode("utf-8")
            new_habit_list = import_habit_list_from_json(file_content)
            current_habit_list = await user_storage.get_user_habit_list(user)
            if current_habit_list:
                merged_habit_list = await current_habit_list.merge(new_habit_list)
                await user_storage.save_user_habit_list(user, merged_habit_list)
            else:
                await user_storage.save_user_habit_list(user, new_habit_list)
            ui.notify(
                f"Successfully imported {len(new_habit_list.habits)} habits.",
                position="top",
                color="positive",
            )
        except json.JSONDecodeError:
            ui.notify("Import failed: Invalid JSON format.", color="negative", position="top")
        except Exception as error:
            ui.notify(f"Import failed: {str(error)}", color="negative", position="top")

    menu_header("Import Habits", target=get_root_path())

    ui.upload(on_upload=handle_file_upload, max_files=1).props("accept=.json")
    return