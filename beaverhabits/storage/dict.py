from dataclasses import dataclass, field
import datetime
from typing import list, Optional

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
    """
    Represents a habit with records of completion.
    """

    @property
    def id(self) -> str:
        if "id" not in self.data:
            self.data["id"] = generate_short_hash(self.name)
        return self.data["id"]

    @id.setter
    def id(self, value: str) -> None:
        self.data["id"] = value

    @property
    def name(self) -> str:
        return self.data["name"]

    @name.setter
    def name(self, value: str) -> None:
        self.data["name"] = value

    @property
    def star(self) -> bool:
        return self.data.get("star", False)

    @star.setter
    def star(self, value: int) -> None:
        self.data["star"] = bool(value)

    @property
    def records(self) -> list[DictRecord]:
        return [DictRecord(d) for d in self.data["records"]]

    @property
    def status(self) -> HabitStatus:
        return self.data.get("status", HabitStatus.ACTIVE)

    @status.setter
    def status(self, value: HabitStatus) -> None:
        self.data["status"] = value

    async def tick(self, day: datetime.date, done: bool) -> None:
        """
        Marks a specific day as done or not done for this habit.
        """
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
        else:
            data = {"day": day.strftime(DAY_MASK), "done": done}
            self.data["records"].append(data)

    async def merge(self, other: "DictHabit") -> "DictHabit":
        """
        Merges this habit with another habit, combining their records.
        """
        self_ticks = {r.day for r in self.records if r.done}
        other_ticks = {r.day for r in other.records if r.done}
        result = sorted(list(self_ticks | other_ticks))

        d = {
            "name": self.name,
            "records": [
                {"day": day.strftime(DAY_MASK), "done": True} for day in result
            ],
        }
        return DictHabit(d)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DictHabit) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return f"{self.name}<{self.id}>"

    __repr__ = __str__


@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """
    Represents a list of habits with an order.
    """

    @property
    def habits(self) -> list[DictHabit]:
        """
        Returns a list of habits, filtered and sorted by status and order.
        """
        valid_statuses = {HabitStatus.ACTIVE: 1, HabitStatus.ARCHIVED: 2}
        habits = [DictHabit(d) for d in self.data["habits"] if d.get("status", HabitStatus.ACTIVE) in valid_statuses]

        # Sort by order and then by status
        o = self.order
        habits.sort(
            key=lambda x: (
                o.index(str(x.id)) if str(x.id) in o else float("inf"),
                valid_statuses.get(x.status, float("inf"))
            )
        )

        return habits

    @property
    def order(self) -> list[str]:
        return self.data.get("order", [])

    @order.setter
    def order(self, value: list[str]) -> None:
        self.data["order"] = value

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        """
        Retrieves a habit by its ID.
        """
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        return None

    async def add(self, name: str) -> None:
        """
        Adds a new habit to the list.
        """
        d = {"name": name, "records": [], "id": generate_short_hash(name)}
        self.data["habits"].append(d)

    async def remove(self, item: DictHabit) -> None:
        """
        Removes a habit from the list.
        """
        self.data["habits"].remove(item.data)

    async def merge(self, other: "DictHabitList") -> "DictHabitList":
        """
        Merges this habit list with another habit list.
        """
        result = set(self.habits).symmetric_difference(set(other.habits))

        # Merge the habit if it exists
        for self_habit in self.habits:
            for other_habit in other.habits:
                if self_habit == other_habit:
                    new_habit = await self_habit.merge(other_habit)
                    result.add(new_habit)

        return DictHabitList({"habits": [h.data for h in result]})