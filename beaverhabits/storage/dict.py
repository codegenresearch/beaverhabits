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
    Base class for storage classes that use a dictionary to store data.
    """
    data: dict = field(default_factory=dict, metadata={"exclude": True})


@dataclass
class DictRecord(CheckedRecord, DictStorage):
    """
    Represents a record of a habit check with a specific day and completion status.
    """

    @property
    def day(self) -> datetime.date:
        """
        Returns the day of the record as a datetime.date object.
        """
        date = datetime.datetime.strptime(self.data["day"], DAY_MASK)
        return date.date()

    @property
    def done(self) -> bool:
        """
        Returns the completion status of the record.
        """
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        """
        Sets the completion status of the record.
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
        Returns the unique identifier of the habit.
        """
        if "id" not in self.data:
            self.data["id"] = generate_short_hash(self.name)
        return self.data["id"]

    @id.setter
    def id(self, value: str) -> None:
        """
        Sets the unique identifier of the habit.
        """
        self.data["id"] = value

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
    def star(self) -> int:
        """
        Returns the star status of the habit.
        """
        return self.data.get("star", 0)

    @star.setter
    def star(self, value: int) -> None:
        """
        Sets the star status of the habit.
        """
        self.data["star"] = value

    @property
    def records(self) -> list[DictRecord]:
        """
        Returns a list of records associated with the habit.
        """
        return [DictRecord(d) for d in self.data["records"]]

    async def tick(self, day: datetime.date, done: bool) -> None:
        """
        Updates the completion status of a record for a specific day.
        """
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
        else:
            data = {"day": day.strftime(DAY_MASK), "done": done}
            self.data["records"].append(data)

    def merge(self, other: 'DictHabit') -> 'DictHabit':
        """
        Merges another habit's records into this habit.
        """
        self_days = {record.day for record in self.records if record.done}
        other_days = {record.day for record in other.records if record.done}
        combined_days = self_days.union(other_days)
        combined_records = [
            {"day": day.strftime(DAY_MASK), "done": True} for day in combined_days
        ]
        return DictHabit({
            "name": self.name,
            "records": combined_records,
            "id": self.id,
            "star": max(self.star, other.star)
        })

    def __eq__(self, other: object) -> bool:
        """
        Checks if two habits are equal based on their unique identifiers.
        """
        if not isinstance(other, DictHabit):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Returns the hash value of the habit based on its unique identifier.
        """
        return hash(self.id)


@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """
    Represents a list of habits with methods to add, remove, and retrieve habits.
    """

    @property
    def habits(self) -> list[DictHabit]:
        """
        Returns a sorted list of habits based on their star status.
        """
        habits = [DictHabit(d) for d in self.data["habits"]]
        habits.sort(key=lambda x: x.star, reverse=True)
        return habits

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        """
        Retrieves a habit by its unique identifier.
        """
        for habit in self.habits:
            if habit.id == habit_id:
                return habit

    async def add(self, name: str) -> None:
        """
        Adds a new habit to the list.
        """
        d = {"name": name, "records": [], "id": generate_short_hash(name), "star": 0}
        self.data["habits"].append(d)

    async def remove(self, item: DictHabit) -> None:
        """
        Removes a habit from the list.
        """
        self.data["habits"].remove(item.data)

    def merge(self, other: 'DictHabitList') -> 'DictHabitList':
        """
        Merges another habit list into this habit list.
        """
        combined_habits = {habit.id: habit for habit in self.habits}
        for habit in other.habits:
            if habit.id in combined_habits:
                combined_habits[habit.id] = combined_habits[habit.id].merge(habit)
            else:
                combined_habits[habit.id] = habit
        return DictHabitList({"habits": [habit.data for habit in combined_habits.values()]})