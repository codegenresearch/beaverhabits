from dataclasses import dataclass, field
import datetime
from typing import List
from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList, HabitStatus
from beaverhabits.utils import generate_short_hash

DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"


@dataclass(init=False)
class DictStorage:
    data: dict = field(default_factory=dict, metadata={"exclude": True})


@dataclass
class DictRecord(CheckedRecord, DictStorage):
    """
    # Read (d1~d3)
    persistent    ->     memory      ->     view
    d0: [x]              d0: [x]
                                            d1: [ ]
    d2: [x]              d2: [x]            d2: [x]
                                            d3: [ ]

    # Update:
    view(update)  ->     memory      ->     persistent
    d1: [ ]
    d2: [ ]              d2: [ ]            d2: [x]
    d3: [x]              d3: [x]            d3: [ ]
    """

    @property
    def day(self) -> datetime.date:
        date = datetime.datetime.strptime(self.data["day"], DAY_MASK)
        return date.date()

    @property
    def done(self) -> bool:
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        self.data["done"] = value


@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    def __init__(self, name: str, status: HabitStatus = HabitStatus.ACTIVE):
        self.data = {
            "name": name,
            "status": status.value,
            "records": [],
            "id": generate_short_hash(name),
            "star": False
        }

    @property
    def id(self) -> str:
        return self.data["id"]

    @property
    def name(self) -> str:
        return self.data["name"]

    @name.setter
    def name(self, value: str) -> None:
        self.data["name"] = value

    @property
    def star(self) -> bool:
        return self.data["star"]

    @star.setter
    def star(self, value: bool) -> None:
        self.data["star"] = value

    @property
    def records(self) -> list[DictRecord]:
        return [DictRecord(d) for d in self.data["records"]]

    @property
    def status(self) -> HabitStatus:
        return HabitStatus(self.data["status"])

    @status.setter
    def status(self, value: HabitStatus) -> None:
        self.data["status"] = value.value

    async def tick(self, day: datetime.date, done: bool) -> None:
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
        else:
            data = {"day": day.strftime(DAY_MASK), "done": done}
            self.data["records"].append(data)

    async def merge(self, other: "DictHabit") -> "DictHabit":
        self_ticks = {r.day for r in self.records if r.done}
        other_ticks = {r.day for r in other.records if r.done}
        result = sorted(list(self_ticks | other_ticks))

        d = {
            "name": self.name,
            "status": self.status.value,
            "records": [
                {"day": day.strftime(DAY_MASK), "done": True} for day in result
            ],
            "id": self.id,
            "star": self.star
        }
        return DictHabit(d.name, HabitStatus(d["status"]))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DictHabit) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        status_label = f"({self.status.name})" if self.status != HabitStatus.ACTIVE else ""
        return f"{self.name}<{self.id}>{status_label}"

    __repr__ = __str__


@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    def __init__(self, habits: List[DictHabit] = None, order: List[str] = None):
        self.data = {
            "habits": [habit.data for habit in habits] if habits else [],
            "order": order if order else []
        }

    @property
    def habits(self) -> list[DictHabit]:
        habits = [DictHabit(d["name"], HabitStatus(d["status"])) for d in self.data["habits"]]

        # Sort by order
        if self.order:
            habits.sort(
                key=lambda x: (
                    self.order.index(str(x.id))
                    if str(x.id) in self.order
                    else float("inf")
                )
            )

        return habits

    @property
    def order(self) -> List[str]:
        return self.data["order"]

    @order.setter
    def order(self, value: List[str]) -> None:
        self.data["order"] = value

    async def get_habit_by(self, habit_id: str) -> DictHabit:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        raise ValueError(f"Habit with id {habit_id} not found")

    async def add(self, name: str, status: HabitStatus = HabitStatus.ACTIVE) -> None:
        d = {
            "name": name,
            "status": status.value,
            "records": [],
            "id": generate_short_hash(name),
            "star": False
        }
        self.data["habits"].append(d)

    async def remove(self, item: DictHabit) -> None:
        self.data["habits"] = [h for h in self.data["habits"] if h["id"] != item.id]

    async def merge(self, other: "DictHabitList") -> "DictHabitList":
        result = set(self.habits).symmetric_difference(set(other.habits))

        # Merge the habit if it exists
        for self_habit in self.habits:
            for other_habit in other.habits:
                if self_habit == other_habit:
                    new_habit = await self_habit.merge(other_habit)
                    result.add(new_habit)

        return DictHabitList(list(result))