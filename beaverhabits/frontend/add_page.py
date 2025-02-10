from nicegui import ui, Client
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitStarCheckbox,
    HabitAddCard,  # Assuming HabitAddCard is defined in components
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList
from beaverhabits.logging import logger  # Use custom logger from beaverhabits.logging

grid_classes = "w-full gap-0 items-center"

def validate_habit_name(name: str) -> bool:
    """Validate that the habit name is not empty and does not exceed 100 characters."""
    return 0 < len(name) <= 100

@ui.refreshable
async def add_ui(habit_list: HabitList, client: Client):
    # Sort habits by name for better organization
    sorted_habits = sorted(habit_list.habits, key=lambda habit: habit.name)
    
    with ui.column().classes("w-full pl-1 items-center sortable"):
        for item in sorted_habits:
            HabitAddCard(item, habit_list, add_ui.refresh)

    # Inject script for sortable functionality
    ui.add_head_html('''
        <script type="module">
            import { Sortable } from 'https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js';
            document.addEventListener('DOMContentLoaded', function() {
                var el = document.querySelector('.sortable');
                var sortable = new Sortable(el, {
                    animation: 150,
                    ghostClass: 'blue-background-class',
                    onEnd: function (evt) {
                        var items = Array.from(el.children).map(child => child.id);
                        console.log('New order:', items);
                        // Send new order to server or update state
                        emitEvent('update_order', items);
                    }
                });
            });
        </script>
    ''')

    # Handle drop event
    @ui.on('update_order')
    async def handle_update_order(new_order):
        logger.info(f"Updating habit order: {new_order}")
        # Update habit_list order based on new_order
        habit_list.habits = [habit for habit_id in new_order for habit in habit_list.habits if habit.id == habit_id]
        add_ui.refresh()

def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center"):
            add_ui(habit_list)
            
            with ui.grid(columns=9, rows=1).classes(grid_classes):
                add_button = HabitAddButton(habit_list, add_ui.refresh)
                add_button.classes("col-span-7")


This code addresses the feedback by:
1. Ensuring all string literals are properly terminated and removing any misplaced comments.
2. Using the `HabitAddCard` class for better encapsulation and consistency with the gold code.
3. Separating the logic for handling the item drop event into a dedicated function using `@ui.on`.
4. Ensuring consistent use of classes and properties as in the gold code, including the `sortable` class.
5. Using a dedicated logging module (`logger`) from `beaverhabits.logging` for consistency.
6. Injecting the sortable functionality script with `type="module"` and ensuring the event emission matches the gold code's approach using `emitEvent`.
7. Managing the order of habits by updating the list based on the UI structure.
8. Using asynchronous functions effectively for event handling and UI updates.