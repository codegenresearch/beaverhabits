from nicegui import ui

from beaverhabits.frontend import components
from beaverhabits.frontend.layout import layout
from beaverhabits.logging import logger
from beaverhabits.storage.storage import HabitList
from beaverhabits.storage.enums import HabitStatus  # Assuming HabitStatus is defined in enums


async def item_drop(e, habit_list: HabitList):
    # Move element
    elements = ui.context.client.elements
    dragged = elements[int(e.args["id"][1:])]
    dragged.move(target_index=e.args["new_index"])

    # Determine the status of the dragged habit based on neighboring habits
    assert dragged.parent_slot is not None
    habits = [
        x.habit
        for x in dragged.parent_slot.children
        if isinstance(x, components.HabitOrderCard) and x.habit
    ]
    dragged_index = habits.index(dragged.habit)

    if dragged_index == 0 or (dragged_index > 0 and habits[dragged_index - 1].status == HabitStatus.ACTIVE):
        dragged.habit.status = HabitStatus.ACTIVE
    else:
        dragged.habit.status = HabitStatus.INACTIVE

    # Update habit order
    habit_list.order = [str(x.id) for x in habits]
    logger.info(f"Dropped habit {dragged.habit.id} to index {e.args['new_index']}")
    add_ui.refresh()


@ui.refreshable
def add_ui(habit_list: HabitList):
    with ui.column().classes("sortable gap-3"):
        for item in sorted(habit_list.habits, key=lambda x: (x.star, x.status == HabitStatus.INACTIVE)):
            with components.HabitOrderCard(item):
                with ui.grid(columns=12, rows=1).classes("gap-0 items-center"):
                    if item.status == HabitStatus.ACTIVE:
                        name = components.HabitNameInput(item)
                    else:
                        name = ui.label(item.name)
                    name.classes("col-span-6 break-all")
                    name.props("borderless")

                    ui.space().classes("col-span-5")

                    star = components.HabitStarCheckbox(item, add_ui.refresh)
                    star.classes("col-span-1")

                    delete = components.HabitDeleteButton(item, habit_list, add_ui.refresh)
                    delete.classes("col-span-1")


def order_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center gap-3"):
            with ui.column().classes("sortable"):
                add_ui(habit_list)

            with components.HabitOrderCard():
                with ui.grid(columns=12, rows=1).classes("gap-0 items-center"):
                    add = components.HabitAddButton(habit_list, add_ui.refresh)
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