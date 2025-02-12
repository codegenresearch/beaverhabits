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
    # Implement input validation for habit names
    # Example: name should not be empty and should not exceed 50 characters
    return bool(name.strip()) and len(name.strip()) <= 50

@ui.refreshable
def add_ui(habit_list: HabitList):
    # Sort habits by a custom order, e.g., by name
    sorted_habits = sorted(habit_list.habits, key=lambda x: x.name)

    for item in sorted_habits:
        with ui.grid(columns=9, rows=1).classes(grid_classes):
            name = HabitNameInput(item, on_change=lambda name, item=item: item.name if validate_habit_name(name) else item.name)
            name.classes("col-span-7 break-all")

            star = HabitStarCheckbox(item, add_ui.refresh)
            star.props("flat fab-mini color=grey")
            star.classes("col-span-1")

            delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
            delete.props("flat fab-mini color=grey")
            delete.classes("col-span-1")

def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center"):
            add_ui(habit_list)

            with ui.grid(columns=9, rows=1).classes(grid_classes):
                add = HabitAddButton(habit_list, add_ui.refresh)
                add.classes("col-span-7")