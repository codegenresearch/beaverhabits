from nicegui import ui

from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitStarCheckbox,
    HabitOrderCard,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.logging import logger
from beaverhabits.storage.storage import HabitList
from beaverhabits.storage.enums import HabitStatus  # Assuming HabitStatus is defined in enums


async def item_drop(e, habit_list: HabitList):
    # Move element
    elements = ui.context.client.elements
    dragged = elements[int(e.args["id"][1:])]
    dragged.move(target_index=e.args["new_index"])

    # Update habit order
    assert dragged.parent_slot is not None
    habits = [
        x.habit
        for x in dragged.parent_slot.children
        if isinstance(x, HabitOrderCard) and x.habit
    ]
    habit_list.order = [str(x.id) for x in habits]

    # Determine the status of the dragged habit based on neighboring habits
    dragged_index = habit_list.order.index(str(dragged.habit.id))
    if dragged_index == 0 or (dragged_index > 0 and habits[dragged_index - 1].status == HabitStatus.ACTIVE):
        dragged.habit.status = HabitStatus.ACTIVE
    else:
        dragged.habit.status = HabitStatus.INACTIVE

    logger.info(f"Dropped habit {dragged.habit.id} to index {e.args['new_index']}")
    add_ui.refresh()


@ui.refreshable
def add_ui(habit_list: HabitList):
    with ui.column().classes("sortable gap-3"):
        for item in sorted(habit_list.habits, key=lambda x: (x.star, x.status == HabitStatus.INACTIVE)):
            with HabitOrderCard(item):
                with ui.grid(columns=12, rows=1).classes("gap-0 items-center"):
                    name = HabitNameInput(item) if item.status == HabitStatus.ACTIVE else ui.label(item.name)
                    name.classes("col-span-3 col-3 break-all")
                    name.props("borderless")

                    ui.space().classes("col-span-7")

                    star = HabitStarCheckbox(item, add_ui.refresh)
                    star.classes("col-span-1")

                    delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
                    delete.classes("col-span-1")


def order_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center gap-3"):
            with ui.column().classes("sortable"):
                add_ui(habit_list)

            with HabitOrderCard():
                with ui.grid(columns=12, rows=1).classes("gap-0 items-center"):
                    add = HabitAddButton(habit_list, add_ui.refresh)
                    add.classes("col-span-12")
                    add.props("borderless")

    ui.add_body_html(
        r"""
        <script type="module">
        import '/statics/libs/sortable.min.js';
        document.addEventListener('DOMContentLoaded', () => {
            Sortable.create(document.querySelector('.sortable'), {
                animation: 150,
                ghostClass: 'opacity-50',
                onEnd: (evt) => emitEvent("item_drop", {id: evt.item.id, new_index: evt.newIndex }),
            });
        });
        </script>
    """
    )
    ui.on("item_drop", lambda e: item_drop(e, habit_list))