import datetime
from dataclasses import dataclass, field
from typing import Optional, List

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList
from beaverhabits.utils import generate_short_hash

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
    Represents a record of a habit check, including the day and whether it was done.
    """
    @property
    def day(self) -> datetime.date:
        """
        Returns the day of the record as a datetime.date object.
        """
        return datetime.datetime.strptime(self.data["day"], DAY_MASK).date()

    @property
    def done(self) -> bool:
        """
        Returns whether the habit was done on the record's day.
        """
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        """
        Sets whether the habit was done on the record's day.
        """
        self.data["done"] = value

@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    """
    Represents a habit with a name, star status, and a list of records.
    """
    @property
    def id(self) -> str:
        """
        Returns the unique identifier for the habit.
        """
        if "id" not in self.data:
            self.data["id"] = generate_short_hash(self.name)
        return self.data["id"]

    @property
    def name(self) -> str:
        """
        Returns the name of the habit.
        """
        return self.data["name"]

    @name.setter
    def name(self, value: str) -> None:
        """
        Sets the name of the habit.
        """
        self.data["name"] = value

    @property
    def star(self) -> bool:
        """
        Returns the star status of the habit.
        """
        return self.data.get("star", False)

    @star.setter
    def star(self, value: bool) -> None:
        """
        Sets the star status of the habit.
        """
        self.data["star"] = value

    @property
    def records(self) -> list[DictRecord]:
        """
        Returns the list of records for the habit.
        """
        return [DictRecord(d) for d in self.data["records"]]

    async def tick(self, day: datetime.date, done: bool) -> None:
        """
        Marks the habit as done or not done for a specific day.
        """
        record_data = next((r for r in self.data["records"] if datetime.datetime.strptime(r["day"], DAY_MASK).date() == day), None)
        if record_data:
            record_data["done"] = done
        else:
            self.data["records"].append({"day": day.strftime(DAY_MASK), "done": done})

    def __eq__(self, other: object) -> bool:
        """
        Checks if two habits are equal based on their IDs.
        """
        if not isinstance(other, DictHabit):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Returns the hash of the habit based on its ID.
        """
        return hash(self.id)

    async def merge(self, other: 'DictHabit') -> 'DictHabit':
        """
        Merges another habit's records into this habit.
        """
        existing_days = {datetime.datetime.strptime(r["day"], DAY_MASK).date() for r in self.data["records"]}
        for record in other.data["records"]:
            record_day = datetime.datetime.strptime(record["day"], DAY_MASK).date()
            if record_day not in existing_days:
                self.data["records"].append(record)
        return self

@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """
    Represents a list of habits.
    """
    @property
    def habits(self) -> list[DictHabit]:
        """
        Returns the list of habits, sorted by star status.
        """
        habits = [DictHabit(d) for d in self.data["habits"]]
        habits.sort(key=lambda x: x.star, reverse=True)
        return habits

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
        self.data["habits"].append({"name": name, "records": [], "id": generate_short_hash(name)})

    async def remove(self, item: DictHabit) -> None:
        """
        Removes a habit from the list.
        """
        self.data["habits"] = [h.data for h in self.habits if h.id != item.id]

    async def merge(self, other: 'DictHabitList') -> 'DictHabitList':
        """
        Merges another habit list into this habit list.
        """
        existing_ids = {habit.id for habit in self.habits}
        for habit in other.habits:
            if habit.id not in existing_ids:
                self.data["habits"].append(habit.data)
            else:
                existing_habit = next(h for h in self.habits if h.id == habit.id)
                await existing_habit.merge(habit)
        return self