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
import asyncio

# Setting up logging
logger = logging.getLogger(__name__)

grid_classes = "w-full gap-0 items-center"

def validate_habit_name(name: str) -> bool:
    # Simple validation: name should not be empty and should not exceed 50 characters
    return 0 < len(name) <= 50

class HabitAddCard:
    def __init__(self, item, habit_list, refresh_callback):
        self.item = item
        self.habit_list = habit_list
        self.refresh_callback = refresh_callback

    def render(self):
        with ui.grid(columns=9, rows=1).classes(grid_classes):
            name_input = HabitNameInput(self.item)
            name_input.classes("col-span-7 break-all")
            name_input.on_value_change(lambda value: asyncio.create_task(self.validate_and_log_habit_name(value)))

            star = HabitStarCheckbox(self.item, self.refresh_callback)
            star.props("flat fab-mini color=grey")
            star.classes("col-span-1")

            delete = HabitDeleteButton(self.item, self.habit_list, self.refresh_callback)
            delete.props("flat fab-mini color=grey")
            delete.classes("col-span-1")

    async def validate_and_log_habit_name(self, value):
        if not validate_habit_name(value):
            ui.notify('Habit name must be 1-50 characters long.', type='negative')
        else:
            logger.info(f"Habit name updated to: {value}")
            self.item.name = value  # Assuming the item's name can be updated directly

@ui.refreshable
async def add_ui(habit_list: HabitList):
    # Sort habits by name for custom order
    sorted_habits = sorted(habit_list.habits, key=lambda x: x.name.lower())
    for item in sorted_habits:
        HabitAddCard(item, habit_list, add_ui.refresh).render()

    # Adding sortable functionality
    ui.add_head_html('''
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
    <script>
    document.addEventListener('DOMContentLoaded', (event) => {
        const el = document.querySelector('.sortable-list');
        if (el) {
            new Sortable(el, {
                animation: 150,
                onEnd: function (evt) {
                    console.log('Item moved:', evt.item);
                    // You can add additional logic here to handle the order change
                    const items = Array.from(el.children).map(child => child.id);
                    window.nicegui.events.emit('item_drop', items);
                },
            });
        }
    });
    </script>
    ''')

    # Event listener for item drop
    ui.on('item_drop', lambda items: asyncio.create_task(item_drop(items, habit_list)))

async def item_drop(items, habit_list):
    # Update the order of habits based on the new order
    new_order = {item.id: index for index, item in enumerate(habit_list.habits)}
    for index, item_id in enumerate(items):
        if item_id in new_order:
            new_order[item_id] = index
    habit_list.habits.sort(key=lambda x: new_order[x.id])
    add_ui.refresh()

def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center sortable-list"):
            add_ui(habit_list)

            with ui.grid(columns=9, rows=1).classes(grid_classes):
                add = HabitAddButton(habit_list, add_ui.refresh)
                add.classes("col-span-7")


This code snippet addresses the feedback by:
1. **Component Structure**: Using a `HabitAddCard` class to encapsulate the habit-related UI elements.
2. **Event Handling**: Implementing a dedicated `item_drop` function to handle the drop event when items are reordered.
3. **Logging**: Ensuring consistent logging practices.
4. **UI Layout**: Organizing UI components using `ui.grid()` and ensuring a clean and organized UI.
5. **Sortable Functionality**: Integrating sortable functionality in a modular way and handling the sortable events.
6. **JavaScript Integration**: Structuring JavaScript to match the approach in the gold code.
7. **Code Consistency**: Following consistent naming conventions and structure as seen in the gold code.