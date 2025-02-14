import calendar
import datetime
from typing import Callable, Optional
from dataclasses import dataclass

from nicegui import events, ui
from nicegui.elements.button import Button

from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.storage.dict import DAY_MASK, MONTH_MASK
from beaverhabits.storage.storage import Habit, HabitList
from beaverhabits.utils import WEEK_DAYS

strptime = datetime.datetime.strptime


def link(text: str, target: str):
    return ui.link(text, target=target).classes(
        "dark:text-white  no-underline hover:no-underline"
    )


def menu_header(title: str, target: str):
    link = ui.link(title, target=target)
    link.classes(
        "text-semibold text-2xl dark:text-white no-underline hover:no-underline"
    )
    return link


def compat_menu(name: str, callback: Callable):
    return ui.menu_item(name, callback).props("dense").classes("items-center")


def menu_icon_button(icon_name: str, click: Optional[Callable] = None) -> Button:
    button_props = "flat=true unelevated=true padding=xs backgroup=none"
    return ui.button(icon=icon_name, color=None, on_click=click).props(button_props)


@dataclass
class HabitAddCard:
    name: str
    star: bool
    ticked_days: list[datetime.date]


class HabitCheckBox(ui.checkbox):
    def __init__(
        self,
        habit_card: HabitAddCard,
        day: datetime.date,
        text: str = "",
        *,
        value: bool = False,
    ) -> None:
        super().__init__(text, value=value, on_change=self._async_task)
        self.habit_card = habit_card
        self.day = day
        self._update_style(value)

    def _update_style(self, value: bool):
        self.props(
            f'checked-icon="{icons.DONE}" unchecked-icon="{icons.CLOSE}" keep-color'
        )
        if not value:
            self.props("color=grey-8")
        else:
            self.props("color=currentColor")

    async def _async_task(self, e: events.ValueChangeEventArguments):
        self._update_style(e.value)
        await self.habit_card.habit.tick(self.day, e.value)
        logger.info(f"Day {self.day} ticked: {e.value}")


class HabitNameInput(ui.input):
    def __init__(self, habit_card: HabitAddCard) -> None:
        super().__init__(value=habit_card.name, on_change=self._async_task)
        self.habit_card = habit_card
        self.validation = lambda value: "Too long" if len(value) > 18 else None
        self.props("dense")

    async def _async_task(self, e: events.ValueChangeEventArguments):
        self.habit_card.name = e.value
        logger.info(f"Habit Name changed to {e.value}")


class HabitStarCheckbox(ui.checkbox):
    def __init__(self, habit_card: HabitAddCard, refresh: Callable) -> None:
        super().__init__("", value=habit_card.star, on_change=self._async_task)
        self.habit_card = habit_card
        self.bind_value(habit_card.habit, "star")
        self.props(f'checked-icon="{icons.STAR_FULL}" unchecked-icon="{icons.STAR}"')
        self.props("flat fab-mini keep-color color=grey-8")
        self.refresh = refresh

    async def _async_task(self, e: events.ValueChangeEventArguments):
        self.habit_card.star = e.value
        self.refresh()
        logger.info(f"Habit Star changed to {e.value}")


class HabitDeleteButton(ui.button):
    def __init__(self, habit_card: HabitAddCard, habit_list: HabitList, refresh: Callable) -> None:
        super().__init__(on_click=self._async_task, icon=icons.DELETE)
        self.habit_card = habit_card
        self.habit_list = habit_list
        self.refresh = refresh

    async def _async_task(self):
        await self.habit_list.remove(self.habit_card.habit)
        self.refresh()
        logger.info(f"Deleted habit: {self.habit_card.name}")


class HabitAddButton(ui.input):
    def __init__(self, habit_list: HabitList, refresh: Callable) -> None:
        super().__init__("New item")
        self.habit_list = habit_list
        self.refresh = refresh
        self.on("keydown.enter", self._async_task)
        self.props("dense")

    async def _async_task(self):
        logger.info(f"Adding new habit: {self.value}")
        await self.habit_list.add(self.value)
        self.refresh()
        self.set_value("")
        logger.info(f"Added new habit: {self.value}")


TODAY = "today"


class HabitDateInput(ui.date):
    def __init__(
        self, today: datetime.date, habit_card: HabitAddCard
    ) -> None:
        self.today = today
        self.habit_card = habit_card
        self.init = True
        self.default_date = today
        super().__init__(self.ticked_days, on_change=self._async_task)

        self.props("multiple")
        self.props("minimal flat")
        self.props(f"default-year-month={self.today.strftime(MONTH_MASK)}")
        qdate_week_first_day = (settings.FIRST_DAY_OF_WEEK + 1) % 7
        self.props(f"first-day-of-week='{qdate_week_first_day}'")
        self.props("today-btn")
        self.classes("shadow-none")

        self.bind_value_from(self, "ticked_days")

    @property
    def ticked_days(self) -> list[str]:
        result = [day.strftime(DAY_MASK) for day in self.habit_card.ticked_days]
        result.append(TODAY)
        return result

    async def _async_task(self, e: events.ValueChangeEventArguments):
        old_values = set(self.habit_card.habit.ticked_days)
        new_values = {strptime(day, DAY_MASK).date() for day in e.value if day != TODAY}

        for day in new_values - old_values:
            await self.habit_card.habit.tick(day, True)
            logger.info(f"QDate day {day} ticked: True")

        for day in old_values - new_values:
            await self.habit_card.habit.tick(day, False)
            logger.info(f"QDate day {day} ticked: False")


@dataclass
class CalendarHeatmap:
    """Habit records by weeks"""

    today: datetime.date
    headers: list[str]
    data: list[list[datetime.date]]
    week_days: list[str]

    @classmethod
    def build(
        cls, today: datetime.date, weeks: int, firstweekday: int = calendar.MONDAY
    ):
        data = cls.generate_calendar_days(today, weeks, firstweekday)
        headers = cls.generate_calendar_headers(data[0])
        week_day_abbr = [calendar.day_abbr[(firstweekday + i) % 7] for i in range(7)]

        return cls(today, headers, data, week_day_abbr)

    @staticmethod
    def generate_calendar_headers(days: list[datetime.date]) -> list[str]:
        if not days:
            return []

        result = []
        month = year = None
        for day in days:
            cur_month, cur_year = day.month, day.year
            if cur_month != month:
                result.append(calendar.month_abbr[cur_month])
                month = cur_month
                continue
            if cur_year != year:
                result.append(str(cur_year))
                year = cur_year
                continue
            result.append("")

        return result

    @staticmethod
    def generate_calendar_days(
        today: datetime.date,
        total_weeks: int,
        firstweekday: int = calendar.MONDAY,  # 0 = Monday, 6 = Sunday
    ) -> list[list[datetime.date]]:
        lastweekday = (firstweekday - 1) % 7
        days_delta = (lastweekday - today.weekday()) % 7
        last_date_of_calendar = today + datetime.timedelta(days=days_delta)

        return [
            [
                last_date_of_calendar - datetime.timedelta(days=i, weeks=j)
                for j in reversed(range(total_weeks))
            ]
            for i in reversed(range(WEEK_DAYS))
        ]


class CalendarCheckBox(ui.checkbox):
    def __init__(
        self,
        habit_card: HabitAddCard,
        day: datetime.date,
        today: datetime.date,
        ticked_data: dict[datetime.date, bool],
        is_bind_data: bool = True,
    ) -> None:
        self.habit_card = habit_card
        self.day = day
        self.today = today
        self.ticked_data = ticked_data
        super().__init__("", value=self.ticked, on_change=self._async_task)

        self.classes("inline-block")
        self.props("dense")
        unchecked_icon, checked_icon = self._icon_svg()
        self.props(f'unchecked-icon="{unchecked_icon}"')
        self.props(f'checked-icon="{checked_icon}"')

        if is_bind_data:
            self.bind_value_from(self, "ticked")

    @property
    def ticked(self):
        return self.ticked_data.get(self.day, False)

    def _icon_svg(self):
        unchecked_color, checked_color = "rgb(54,54,54)", "rgb(103,150,207)"
        return (
            icons.SQUARE.format(color=unchecked_color, text=self.day.day),
            icons.SQUARE.format(color=checked_color, text=self.day.day),
        )

    async def _async_task(self, e: events.ValueChangeEventArguments):
        self.ticked_data[self.day] = e.value
        await self.habit_card.habit.tick(self.day, e.value)
        logger.info(f"Calendar Day {self.day} ticked: {e.value}")


def habit_heat_map(
    habit_card: HabitAddCard,
    habit_calendar: CalendarHeatmap,
    ticked_data: Optional[dict[datetime.date, bool]] = None,
):
    today = habit_calendar.today

    if ticked_data is None:
        ticked_data = {day: True for day in habit_card.ticked_days}

    for header in habit_calendar.headers:
        header_label = ui.label(header).classes("text-gray-300 text-center")
        header_label.style("width: 20px; line-height: 18px; font-size: 9px;")
    ui.label().style("width: 22px;")

    for i, weekday_days in enumerate(habit_calendar.data):
        with ui.row(wrap=False).classes("gap-0"):
            for day in weekday_days:
                if day <= habit_calendar.today:
                    CalendarCheckBox(habit_card, day, today, ticked_data)
                else:
                    ui.label().style("width: 20px; height: 20px;")

            week_day_abbr_label = ui.label(habit_calendar.week_days[i])
            week_day_abbr_label.classes("indent-1.5 text-gray-300")
            week_day_abbr_label.style("width: 22px; line-height: 20px; font-size: 9px;")