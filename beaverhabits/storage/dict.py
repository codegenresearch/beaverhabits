import datetime
from dataclasses import dataclass, field
from typing import Optional, List
from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList
from beaverhabits.utils import generate_short_hash
from pydantic import ValidationError, validator

DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"

@dataclass(init=False)
class DictStorage:
    data: dict = field(default_factory=dict, metadata={"exclude": True})

@dataclass
class DictRecord(CheckedRecord, DictStorage):
    """\n    Manages individual habit records with properties for the day and completion status.\n    """

    @property
    def day(self) -> datetime.date:
        try:
            date = datetime.datetime.strptime(self.data["day"], DAY_MASK)
            return date.date()
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")

    @property
    def done(self) -> bool:
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        self.data["done"] = value

@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    """\n    Represents a habit with properties like id, name, star status, and a list of records.\n    """

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
        if not value.strip():
            raise ValueError("Habit name cannot be empty or contain only whitespace.")
        self.data["name"] = value

    @property
    def star(self) -> bool:
        return self.data.get("star", False)

    @star.setter
    def star(self, value: bool) -> None:
        self.data["star"] = value

    @property
    def records(self) -> List[DictRecord]:
        return [DictRecord(d) for d in self.data.get("records", [])]

    async def tick(self, day: datetime.date, done: bool) -> None:
        record = next((r for r in self.records if r.day == day), None)
        if record:
            record.done = done
        else:
            self.data["records"].append({"day": day.strftime(DAY_MASK), "done": done})

    async def merge(self, other: "DictHabit") -> "DictHabit":
        self_ticks = {r.day for r in self.records if r.done}
        other_ticks = {r.day for r in other.records if r.done}
        merged_ticks = sorted(list(self_ticks | other_ticks))

        merged_records = [{"day": day.strftime(DAY_MASK), "done": True} for day in merged_ticks]
        return DictHabit({"name": self.name, "records": merged_records})

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DictHabit) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """\n    Manages a list of habits, allowing for operations like adding, removing, and merging habits.\n    """

    @property
    def habits(self) -> List[DictHabit]:
        habits = [DictHabit(d) for d in self.data.get("habits", [])]
        habits.sort(key=lambda x: x.star, reverse=True)
        return habits

    @property
    def order(self) -> List[str]:
        return [habit.id for habit in self.habits]

    @order.setter
    def order(self, value: List[str]) -> None:
        ordered_habits = {habit.id: habit for habit in self.habits}
        self.data["habits"] = [ordered_habits[id] for id in value if id in ordered_habits]

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        return next((habit for habit in self.habits if habit.id == habit_id), None)

    async def add(self, name: str) -> None:
        if not self.data.get("habits"):
            self.data["habits"] = []
        new_habit_data = {"name": name, "records": [], "id": generate_short_hash(name)}
        new_habit = DictHabit(new_habit_data)
        if new_habit not in self.habits:
            self.data["habits"].append(new_habit_data)

    async def remove(self, item: DictHabit) -> None:
        self.data["habits"] = [h.data for h in self.habits if h.id != item.id]

    async def merge(self, other: "DictHabitList") -> "DictHabitList":
        result = set(self.habits).symmetric_difference(set(other.habits))

        for self_habit in self.habits:
            for other_habit in other.habits:
                if self_habit == other_habit:
                    new_habit = await self_habit.merge(other_habit)
                    result.add(new_habit)

        return DictHabitList({"habits": [h.data for h in result]})