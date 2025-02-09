from nicegui import ui
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitStarCheckbox,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList
import logging

grid_classes = "w-full gap-0 items-center"

# Setting up logging
logger = logging.getLogger(__name__)

class HabitAddCard:
    def __init__(self, item, habit_list, refresh_callback):
        self.item = item
        self.habit_list = habit_list
        self.refresh_callback = refresh_callback

    def render(self):
        with ui.grid(columns=9, rows=1).classes(grid_classes):
            name_input = HabitNameInput(self.item)
            name_input.classes("col-span-7 break-all")
            name_input.on_value_change(self.validate_habit_name)

            star = HabitStarCheckbox(self.item, self.refresh_callback)
            star.props("flat fab-mini color=grey")
            star.classes("col-span-1")

            delete = HabitDeleteButton(self.item, self.habit_list, self.refresh_callback)
            delete.props("flat fab-mini color=grey")
            delete.classes("col-span-1")

    def validate_habit_name(self, value):
        if not validate_habit_name(value):
            ui.notify('Habit name must be 1-50 characters long.', type='negative')
        else:
            logger.info(f"Habit name updated to: {value}")

def validate_habit_name(name: str) -> bool:
    # Simple validation: name should not be empty and should not exceed 50 characters
    return 0 < len(name) <= 50

@ui.refreshable
def add_ui(habit_list: HabitList):
    # Sort habits by name for custom order
    sorted_habits = sorted(habit_list.habits, key=lambda x: x.name.lower())
    for item in sorted_habits:
        HabitAddCard(item, habit_list, add_ui.refresh).render()

def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center"):
            add_ui(habit_list)

            with ui.grid(columns=9, rows=1).classes(grid_classes):
                add = HabitAddButton(habit_list, add_ui.refresh)
                add.classes("col-span-7")