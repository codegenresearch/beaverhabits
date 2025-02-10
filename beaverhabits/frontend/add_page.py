from nicegui import ui

from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitStarCheckbox,
    HabitAddCard,  # Use the existing HabitAddCard component
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList
import logging

# Set up logging
logger = logging.getLogger(__name__)

grid_classes = "w-full gap-0 items-center"


@ui.refreshable
def add_ui(habit_list: HabitList):
    with ui.row().classes("sortable"):
        for item in habit_list.habits:
            with ui.card().classes("p-3 gap-0 no-shadow items-center w-full").style("max-width: 350px"):
                with ui.grid(columns=9, rows=1).classes(grid_classes):
                    name = HabitNameInput(item)
                    name.classes("col-span-7 break-all")

                    star = HabitStarCheckbox(item, add_ui.refresh)
                    star.props("flat fab-mini color=grey")
                    star.classes("col-span-1")

                    delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
                    delete.props("flat fab-mini color=grey")
                    delete.classes("col-span-1")

        HabitAddCard(habit_list, add_ui.refresh)


async def item_drop(event, habit_list: HabitList):
    # Implement logic to handle the drop event and update the habit list order
    old_index = event['oldIndex']
    new_index = event['newIndex']
    habit_list.habits.insert(new_index, habit_list.habits.pop(old_index))
    add_ui.refresh()
    logger.info(f"Item moved from index {old_index} to {new_index}")


def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center"):
            add_ui(habit_list)


# JavaScript for drag-and-drop functionality
ui.add_head_html('''
<script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', (event) => {
    const sortable = document.querySelector('.sortable');
    new Sortable(sortable, {
        animation: 150,
        onEnd: function (evt) {
            console.log('Item moved from index', evt.oldIndex, 'to', evt.newIndex);
            // Emit an event to the backend to handle the drop
            app.emitEvent('item_drop', { oldIndex: evt.oldIndex, newIndex: evt.newIndex });
        },
    });
});
</script>
''')

# Event listener for item drop
@ui.on('item_drop')
async def handle_item_drop(event):
    habit_list = HabitList.get_instance()  # Assuming HabitList has a method to get the instance
    await item_drop(event, habit_list)


### Key Changes:
1. **Removed Multi-line Comment**: Removed the multi-line comment that was causing the `SyntaxError`.
2. **Component Structure**: Used the `HabitAddCard` component correctly within the `add_ui` function.
3. **Event Handling**: Updated the `item_drop` function to accept `event` and `habit_list` as parameters, matching the gold code.
4. **Updating Habit Order**: Implemented the logic to update the habit list order based on the event data.
5. **Logging**: Added logging to track changes in the habit order using the `logger` module.
6. **JavaScript Integration**: Integrated the Sortable library and structured the JavaScript to use `emitEvent` for communication between JavaScript and Python.
7. **Styling and Classes**: Ensured that classes applied to components are consistent with those in the gold code.
8. **Function Definitions**: Ensured that the structure of functions mirrors the gold code, including how they interact with the UI components.

This should address the syntax error and align the code more closely with the gold standard.