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


class HabitAddCard(ui.card):
    def __init__(self, habit_list: HabitList, refresh_callback):
        super().__init__()
        self.habit_list = habit_list
        self.refresh_callback = refresh_callback
        self._build_ui()
        self.classes("p-3 gap-0 no-shadow items-center w-full").style("max-width: 350px")

    def _build_ui(self):
        with ui.grid(columns=9, rows=1).classes(grid_classes):
            add_button = HabitAddButton(self.habit_list, self.refresh_callback)
            add_button.classes("col-span-7")

    def __str__(self):
        return f"HabitAddCard(habit_list={self.habit_list}, refresh_callback={self.refresh_callback})"


class HabitItemCard(ui.card):
    def __init__(self, item, habit_list: HabitList, refresh_callback):
        super().__init__()
        self.item = item
        self.habit_list = habit_list
        self.refresh_callback = refresh_callback
        self._build_ui()
        self.classes("p-3 gap-0 no-shadow items-center w-full").style("max-width: 350px")

    def _build_ui(self):
        with ui.grid(columns=9, rows=1).classes(grid_classes):
            name = HabitNameInput(self.item)
            name.classes("col-span-7 break-all")

            star = HabitStarCheckbox(self.item, self.refresh_callback)
            star.props("flat fab-mini color=grey")
            star.classes("col-span-1")

            delete = HabitDeleteButton(self.item, self.habit_list, self.refresh_callback)
            delete.props("flat fab-mini color=grey")
            delete.classes("col-span-1")

    def __str__(self):
        return f"HabitItemCard(item={self.item}, habit_list={self.habit_list}, refresh_callback={self.refresh_callback})"


@ui.refreshable
def add_ui(habit_list: HabitList):
    for item in habit_list.habits:
        HabitItemCard(item, habit_list, add_ui.refresh)

    HabitAddCard(habit_list, add_ui.refresh)


def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center"):
            add_ui(habit_list)


### Changes Made:
1. **HabitAddCard Class**: Removed the `classes` and `style` arguments from the `super().__init__()` call and applied them after the initialization.
2. **HabitItemCard Class**: Created a new class `HabitItemCard` to encapsulate the habit item UI components, similar to the `HabitAddCard`.
3. **UI Structure**: Used `HabitItemCard` to wrap each habit item, improving the organization of the UI.
4. **Consistency**: Ensured that the `classes` and `style` methods are used consistently for styling components.