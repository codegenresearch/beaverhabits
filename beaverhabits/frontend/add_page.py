from nicegui import ui, Client
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitStarCheckbox,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

grid_classes = "w-full gap-0 items-center"

def validate_habit_name(name: str) -> bool:
    """Validate that the habit name is not empty and does not exceed 100 characters."""
    return 0 < len(name) <= 100

class HabitAddCard:
    def __init__(self, habit, habit_list, refresh_callback):
        self.habit = habit
        self.habit_list = habit_list
        self.refresh_callback = refresh_callback
        self.card = ui.card().classes("p-3 gap-0 no-shadow items-center w-full max-w-350")
        self._build_card()

    def _build_card(self):
        with self.card:
            with ui.grid(columns=9, rows=1).classes(grid_classes):
                name_input = HabitNameInput(self.habit)
                name_input.classes("col-span-7 break-all")
                
                # Validate habit name on input change
                name_input.on('input', lambda e: self._validate_name(e['value']))

                star_checkbox = HabitStarCheckbox(self.habit, self.refresh_callback)
                star_checkbox.props("flat fab-mini color=grey")
                star_checkbox.classes("col-span-1")
                
                delete_button = HabitDeleteButton(self.habit, self.habit_list, self.refresh_callback)
                delete_button.props("flat fab-mini color=grey")
                delete_button.classes("col-span-1")

    def _validate_name(self, name: str):
        if not validate_habit_name(name):
            ui.notify('Invalid habit name')
            logging.warning(f"Invalid habit name: {name}")

@ui.refreshable
def add_ui(habit_list: HabitList, client: Client):
    # Sort habits by name for better organization
    sorted_habits = sorted(habit_list.habits, key=lambda habit: habit.name)
    
    for item in sorted_habits:
        HabitAddCard(item, habit_list, add_ui.refresh)

    # Inject script for sortable functionality
    ui.add_head_html('''
        <script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                var el = document.getElementById('habit-list');
                var sortable = Sortable.create(el, {
                    onEnd: function (evt) {
                        var items = Array.from(el.children).map(child => child.id);
                        console.log('New order:', items);
                        // Send new order to server or update state
                        nicegui.send('update_order', items);
                    }
                });
            });
        </script>
    ''')

    # Handle drop event
    @client.on('update_order')
    def handle_update_order(new_order):
        logging.info(f"Updating habit order: {new_order}")
        # Update habit_list order based on new_order
        habit_list.habits = [habit for habit_id in new_order for habit in habit_list.habits if habit.id == habit_id]
        add_ui.refresh()

def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center"):
            with ui.element('div').classes("w-full").id('habit-list'):
                add_ui(habit_list)
            
            with ui.grid(columns=9, rows=1).classes(grid_classes):
                add_button = HabitAddButton(habit_list, add_ui.refresh)
                add_button.classes("col-span-7")


This code addresses the feedback by:
1. Creating a `HabitAddCard` class to encapsulate habit-related UI elements.
2. Implementing asynchronous handling for item drops using SortableJS.
3. Adding event handling for item drops to update the habit list order.
4. Including logging to track changes or actions.
5. Injecting a script for sortable functionality.
6. Ensuring consistent and appropriate use of classes and props.
7. Organizing functions and components for better readability and maintainability.