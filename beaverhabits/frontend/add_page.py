from nicegui import ui
from beaverhabits.frontend.components import HabitAddButton, HabitDeleteButton, HabitNameInput, HabitStarCheckbox
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

@ui.refreshable
async def add_ui(habit_list: HabitList):
    # Sort habits by name for custom order
    sorted_habits = sorted(habit_list.habits, key=lambda x: x.name.lower())
    for item in sorted_habits:
        with ui.row().classes(grid_classes).classes("sortable-item").style(f'id: {item.id}'):
            name_input = HabitNameInput(item)
            name_input.classes("col-span-7 break-all")
            name_input.on_value_change(lambda value, item=item: asyncio.create_task(validate_and_log_habit_name(value, item)))

            star = HabitStarCheckbox(item, add_ui.refresh)
            star.props("flat fab-mini color=grey")
            star.classes("col-span-1")

            delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
            delete.props("flat fab-mini color=grey")
            delete.classes("col-span-1")

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

async def validate_and_log_habit_name(value, item):
    if not validate_habit_name(value):
        ui.notify('Habit name must be 1-50 characters long.', type='negative')
    else:
        logger.info(f"Habit name updated to: {value}")
        item.name = value  # Assuming the item's name can be updated directly

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

            with ui.row().classes(grid_classes):
                add_button = HabitAddButton(habit_list, add_ui.refresh)
                add_button.classes("col-span-7")