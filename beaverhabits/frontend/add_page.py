from nicegui import ui

from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitStarCheckbox,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList

grid_classes = "w-full gap-0 items-center"

def validate_habit_name(name: str) -> bool:
    """Validate the habit name to ensure it is not empty or contains only whitespace."""
    return bool(name.strip())

@ui.refreshable
def add_ui(habit_list: HabitList):
    # Sort habits by name for better organization
    sorted_habits = sorted(habit_list.habits, key=lambda habit: habit.name)

    for item in sorted_habits:
        with ui.grid(columns=9, rows=1).classes(grid_classes):
            name = HabitNameInput(item)
            name.classes("col-span-7 break-all")
            name.on_change(lambda _, name=item.name: _validate_and_update_name(name, item))

            star = HabitStarCheckbox(item, add_ui.refresh)
            star.props("flat fab-mini color=grey")
            star.classes("col-span-1")

            delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
            delete.props("flat fab-mini color=grey")
            delete.classes("col-span-1")

def _validate_and_update_name(new_name: str, item):
    """Helper function to validate and update habit name."""
    if validate_habit_name(new_name):
        item.name = new_name
        add_ui.refresh()
    else:
        ui.notify("Habit name cannot be empty or contain only whitespace.", type="negative")

def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center"):
            add_ui(habit_list)

            with ui.grid(columns=9, rows=1).classes(grid_classes):
                add = HabitAddButton(habit_list, add_ui.refresh)
                add.classes("col-span-7")