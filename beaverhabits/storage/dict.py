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
    """
    Base class for storage using a dictionary.
    """
    data: dict = field(default_factory=dict, metadata={"exclude": True})

@dataclass
class DictRecord(CheckedRecord, DictStorage):
    """
    Represents a single record of a habit with a specific day and completion status.

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
        """Returns the day of the record as a datetime.date object."""
        return datetime.datetime.strptime(self.data["day"], DAY_MASK).date()

    @property
    def done(self) -> bool:
        """Returns the completion status of the record."""
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        """Sets the completion status of the record."""
        self.data["done"] = value

@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    """
    Represents a habit with a name, star status, and a list of records.
    """

    @property
    def id(self) -> str:
        """Returns the unique identifier of the habit."""
        if "id" not in self.data:
            self.data["id"] = generate_short_hash(self.name)
        return self.data["id"]

    @id.setter
    def id(self, value: str) -> None:
        """Sets the unique identifier of the habit."""
        self.data["id"] = value

    @property
    def name(self) -> str:
        """Returns the name of the habit."""
        return self.data["name"]

    @name.setter
    def name(self, value: str) -> None:
        """Sets the name of the habit."""
        self.data["name"] = value

    @property
    def star(self) -> bool:
        """Returns the star status of the habit."""
        return self.data.get("star", False)

    @star.setter
    def star(self, value: bool) -> None:
        """Sets the star status of the habit."""
        self.data["star"] = value

    @property
    def records(self) -> List[DictRecord]:
        """Returns the list of records associated with the habit."""
        return [DictRecord(d) for d in self.data["records"]]

    async def tick(self, day: datetime.date, done: bool) -> None:
        """
        Updates the completion status of a record for a specific day.
        If the record does not exist, it creates a new one.
        """
        if (record := next((r for r in self.records if r.day == day), None)) is not None:
            record.done = done
        else:
            self.data["records"].append({"day": day.strftime(DAY_MASK), "done": done})

    async def merge(self, other: "DictHabit") -> "DictHabit":
        """
        Merges records from another habit into this habit.
        """
        self_ticks = {r.day for r in self.records if r.done}
        other_ticks = {r.day for r in other.records if r.done}
        merged_ticks = sorted(list(self_ticks | other_ticks))
        return DictHabit({
            "name": self.name,
            "records": [{"day": day.strftime(DAY_MASK), "done": True} for day in merged_ticks]
        })

    def __eq__(self, other: object) -> bool:
        """Checks if two habits are equal based on their IDs."""
        return isinstance(other, DictHabit) and self.id == other.id

    def __hash__(self) -> int:
        """Returns the hash of the habit based on its ID."""
        return hash(self.id)

    def __str__(self) -> str:
        """Returns the string representation of the habit including its ID."""
        return f"{self.name}<{self.id}>"

    __repr__ = __str__

@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """
    Manages a list of habits with methods to add, remove, and merge habits.
    """

    @property
    def habits(self) -> List[DictHabit]:
        """
        Returns the list of habits sorted by star status and order.
        """
        habits = [DictHabit(d) for d in self.data["habits"]]
        if self.order:
            habits.sort(key=lambda x: (not x.star, self.order.index(x.id)))
        else:
            habits.sort(key=lambda x: not x.star)
        return habits

    @property
    def order(self) -> List[str]:
        """Returns the order of habits."""
        return self.data.get("order", [])

    @order.setter
    def order(self, value: List[str]) -> None:
        """Sets the order of habits."""
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
        new_habit = {
            "name": name,
            "records": [],
            "id": generate_short_hash(name)
        }
        self.data["habits"].append(new_habit)
        self.data["order"].append(new_habit["id"])

    async def remove(self, item: DictHabit) -> None:
        """
        Removes a habit from the list.
        """
        self.data["habits"].remove(item.data)
        if item.id in self.data["order"]:
            self.data["order"].remove(item.id)

    async def merge(self, other: "DictHabitList") -> "DictHabitList":
        """
        Merges another habit list into this habit list.
        """
        result = set(self.habits).symmetric_difference(set(other.habits))
        for self_habit in self.habits:
            for other_habit in other.habits:
                if self_habit == other_habit:
                    new_habit = await self_habit.merge(other_habit)
                    result.add(new_habit)
        return DictHabitList({"habits": [h.data for h in result], "order": self.order})

class HabitCreate(BaseModel):
    name: str

    @validator('name')
    def name_must_not_be_empty(cls, v: str) -> str:
        """Validates that the habit name is not empty."""
        if not v.strip():
            raise ValueError('Habit name cannot be empty.')
        return v