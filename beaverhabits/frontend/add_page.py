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
    """Validate that the habit name is not empty and does not exceed 100 characters."""
    return 0 < len(name) <= 100

@ui.refreshable
def add_ui(habit_list: HabitList):
    # Sort habits by name for better organization
    sorted_habits = sorted(habit_list.habits, key=lambda habit: habit.name)
    
    for item in sorted_habits:
        with ui.grid(columns=9, rows=1).classes(grid_classes):
            name_input = HabitNameInput(item)
            name_input.classes("col-span-7 break-all")
            
            # Validate habit name on input change
            name_input.on_change(lambda e: ui.notify('Invalid habit name') if not validate_habit_name(e.value) else None)
            
            star_checkbox = HabitStarCheckbox(item, add_ui.refresh)
            star_checkbox.props("flat fab-mini color=grey")
            star_checkbox.classes("col-span-1")
            
            delete_button = HabitDeleteButton(item, habit_list, add_ui.refresh)
            delete_button.props("flat fab-mini color=grey")
            delete_button.classes("col-span-1")

def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center"):
            add_ui(habit_list)
            
            with ui.grid(columns=9, rows=1).classes(grid_classes):
                add_button = HabitAddButton(habit_list, add_ui.refresh)
                add_button.classes("col-span-7")