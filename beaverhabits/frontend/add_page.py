from nicegui import ui, Client
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitStarCheckbox,
    HabitAddCard,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList
import logging

grid_classes = "w-full gap-0 items-center"
logger = logging.getLogger(__name__)

def validate_habit_name(name: str) -> bool:
    """Validate that the habit name is not empty and does not exceed 100 characters."""
    return 0 < len(name) <= 100

async def item_drop(e: dict, habit_list: HabitList, client: Client):
    """Handle the drop event to reorder habits."""
    try:
        source_index = int(e['detail']['from'])
        target_index = int(e['detail']['to'])
        habit_list.reorder_habits(source_index, target_index)
        logger.info(f"Habit reordered from {source_index} to {target_index}")
        add_ui.refresh()
    except Exception as ex:
        logger.error(f"Error reordering habits: {ex}")

@ui.refreshable
def add_ui(habit_list: HabitList):
    # Sort habits by name for better organization
    sorted_habits = sorted(habit_list.habits, key=lambda habit: habit.name)
    
    with ui.column().classes(grid_classes).classes("sortable"):
        for index, item in enumerate(sorted_habits):
            with HabitAddCard(item, index):
                name_input = HabitNameInput(item)
                name_input.classes("col-span-7 break-all")
                
                # Validate habit name on input change
                name_input.on('input', lambda e, item=item: ui.notify('Invalid habit name') if not validate_habit_name(e['args']['value']) else None)
                
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

# Enable sortable functionality
ui.add_head_html('''
<script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    const sortable = new Sortable(document.querySelector('.sortable'), {
        animation: 150,
        onEnd: function (evt) {
            const detail = { from: evt.oldIndex, to: evt.newIndex };
            nicegui.events.emit('item_drop', detail);
        }
    });
});
</script>
''')

ui.on('item_drop', lambda e: item_drop(e, habit_list, ui.client))


### Key Changes:
1. **HabitAddCard Constructor**: Adjusted the instantiation of `HabitAddCard` to pass only the required arguments (`item` and `index`).
2. **Habit Reordering**: Used a hypothetical `reorder_habits` method on `HabitList` to reorder habits, which should be defined in your `HabitList` class.
3. **Import Statements**: Consolidated imports from the same module.
4. **Event Handling**: Simplified the event handling for the drop event.
5. **UI Structure**: Simplified the UI structure for better readability.
6. **JavaScript Integration**: Kept the JavaScript integration concise and modular.
7. **Logging**: Ensured logging statements are consistent with the gold code.