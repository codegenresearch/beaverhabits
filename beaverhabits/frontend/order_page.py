from nicegui import ui

from beaverhabits.frontend import components
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitStarCheckbox,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.logging import logger
from beaverhabits.storage.storage import HabitList


async def item_drop(e, habit_list: HabitList):
    # Move element
    elements = ui.context.client.elements
    dragged = elements[int(e.args["id"][1:])]
    dragged.move(target_index=e.args["new_index"])

    # Update habit order and status
    assert dragged.parent_slot is not None
    habits = [
        x.habit
        for x in dragged.parent_slot.children
        if isinstance(x, components.HabitOrderCard) and x.habit
    ]
    habit_list.order = [str(x.id) for x in habits]
    for index, habit in enumerate(habits):
        habit.status = 'active' if index < 5 else 'inactive'
    logger.info(f"New order and status: {[(habit.name, habit.status) for habit in habits]}")


@ui.refreshable
def add_ui(habit_list: HabitList):
    with ui.column().classes("sortable").classes("gap-3"):
        filtered_habits = sorted(habit_list.habits, key=lambda x: (x.status != 'active', x.star), reverse=True)
        for item in filtered_habits:
            with components.HabitOrderCard(item):
                with ui.grid(columns=12, rows=1).classes("gap-0 items-center"):
                    name = HabitNameInput(item)
                    name.classes("col-span-3 col-3")
                    name.props("borderless")

                    ui.space().classes("col-span-7")

                    star = HabitStarCheckbox(item, add_ui.refresh)
                    star.classes("col-span-1")

                    delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
                    delete.classes("col-span-1")


def order_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center gap-3"):
            add_ui(habit_list)

            with components.HabitOrderCard():
                with ui.grid(columns=12, rows=1).classes("gap-0 items-center"):
                    add = HabitAddButton(habit_list, add_ui.refresh)
                    add.classes("col-span-12")
                    add.props("borderless")

    ui.add_body_html(
        r"""\n        <script type="module">\n        import '/statics/libs/sortable.min.js';\n        document.addEventListener('DOMContentLoaded', () => {\n            Sortable.create(document.querySelector('.sortable'), {\n                animation: 150,\n                ghostClass: 'opacity-50',\n                onEnd: (evt) => emitEvent("item_drop", {id: evt.item.id, new_index: evt.newIndex }),\n            });\n        });\n        </script>\n    """
    )
    ui.on("item_drop", lambda e: item_drop(e, habit_list))