import datetime
from dataclasses import dataclass, field
from typing import Optional, List
from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList
from beaverhabits.utils import generate_short_hash
from pydantic import BaseModel, validator

DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"

@dataclass(init=False)
class DictStorage:
    data: dict = field(default_factory=dict, metadata={"exclude": True})

@dataclass
class DictRecord(CheckedRecord, DictStorage):
    """
    Manages individual habit records with day and completion status.
    """

    @property
    def day(self) -> datetime.date:
        return datetime.datetime.strptime(self.data["day"], DAY_MASK).date()

    @property
    def done(self) -> bool:
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        self.data["done"] = value

@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    """
    Represents a habit with a name, star status, and a list of records.
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
    def star(self, value: bool) -> None:
        self.data["star"] = value

    @property
    def records(self) -> list[DictRecord]:
        return [DictRecord(d) for d in self.data["records"]]

    async def tick(self, day: datetime.date, done: bool) -> None:
        if (record := next((r for r in self.records if r.day == day), None)) is not None:
            record.done = done
        else:
            self.data["records"].append({"day": day.strftime(DAY_MASK), "done": done})

    def __str__(self):
        return self.name

    __repr__ = __str__

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DictHabit) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """
    Manages a list of habits with order and provides methods to add, remove, and merge habits.
    """

    @property
    def habits(self) -> list[DictHabit]:
        ordered_habits = sorted([DictHabit(d) for d in self.data["habits"]], key=lambda x: self.order.index(x.id) if x.id in self.order else float('inf'))
        return ordered_habits

    @property
    def order(self) -> list[str]:
        return self.data.get("order", [])

    @order.setter
    def order(self, value: list[str]) -> None:
        self.data["order"] = value

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        return next((habit for habit in self.habits if habit.id == habit_id), None)

    async def add(self, name: str) -> None:
        if not name.strip():
            raise ValueError("Habit name cannot be empty.")
        new_habit = {
            "name": name,
            "records": [],
            "id": generate_short_hash(name)
        }
        self.data["habits"].append(new_habit)
        self.data["order"].append(new_habit["id"])

    async def remove(self, item: DictHabit) -> None:
        self.data["habits"].remove(item.data)
        self.data["order"].remove(item.id)

    async def merge(self, other: "DictHabitList") -> "DictHabitList":
        result = set(self.habits).symmetric_difference(set(other.habits))
        for self_habit in self.habits:
            for other_habit in other.habits:
                if self_habit == other_habit:
                    new_habit = await self_habit.merge(other_habit)
                    result.add(new_habit)
        return DictHabitList({"habits": [h.data for h in result], "order": self.order + other.order})

class HabitCreate(BaseModel):
    name: str

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Habit name cannot be empty.')
        return v