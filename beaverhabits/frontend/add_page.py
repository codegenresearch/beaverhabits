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


@ui.refreshable
def add_ui(habit_list: HabitList):
    with ui.column().classes("sortable"):
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


def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center"):
            add_ui(habit_list)

# JavaScript for drag-and-drop functionality
ui.add_head_html('''
<script>
document.addEventListener('DOMContentLoaded', (event) => {
    const sortable = document.querySelector('.sortable');
    new Sortable(sortable, {
        animation: 150,
        onEnd: function (evt) {
            console.log('Item moved from index', evt.oldIndex, 'to', evt.newIndex);
            // Here you can add logic to update the habit list order
        },
    });
});
</script>
''')


### Key Changes:
1. **HabitAddCard Class**: Removed the `classes` and `style` parameters from the `super().__init__()` call and applied them after the initialization.
2. **UI Structure**: Wrapped each habit item in a `ui.card` to better encapsulate the habit item.
3. **Sortable Class**: Added a `sortable` class to the column to enable drag-and-drop functionality.
4. **JavaScript Integration**: Added a script to handle drag-and-drop functionality using the Sortable library. This script logs the movement of items and can be extended to update the habit list order.
5. **Consistent Styling and Props**: Ensured that classes and props are applied consistently across components.