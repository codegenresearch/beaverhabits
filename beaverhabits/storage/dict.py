import datetime
from dataclasses import dataclass, field
from typing import Optional, List

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList
from beaverhabits.utils import generate_short_hash

DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"


@dataclass(init=False)
class DictStorage:
    data: dict = field(default_factory=dict, metadata={"exclude": True})

    def save_user_habit_list(self, habit_list: 'DictHabitList') -> None:
        self.data = habit_list.data

    def get_user_habit_list(self) -> Optional['DictHabitList']:
        if self.data:
            return DictHabitList(self.data)
        return None


@dataclass
class DictRecord(CheckedRecord, DictStorage):
    """
    Represents a record of a habit check for a specific day.
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
    Represents a habit with a list of check records.
    """

    @property
    def id(self) -> str:
        if "id" not in self.data:
            self.data["id"] = generate_short_hash(self.name)
        return self.data["id"]

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
    def records(self) -> List[DictRecord]:
        return [DictRecord(d) for d in self.data["records"]]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DictHabit):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    async def tick(self, day: datetime.date, done: bool) -> None:
        """
        Marks the habit as done or not done for a specific day.
        """
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
        else:
            data = {"day": day.strftime(DAY_MASK), "done": done}
            self.data["records"].append(data)

    async def merge(self, other: 'DictHabit') -> None:
        """
        Merges another habit's records into this habit.
        """
        existing_days = {r.day for r in self.records}
        for record in other.records:
            if record.day not in existing_days:
                self.data["records"].append(record.data)


@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """
    Manages a list of habits for a user, providing methods to add, remove, and retrieve habits,
    as well as to merge another habit list into the current one.
    """

    @property
    def habits(self) -> List[DictHabit]:
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
        Adds a new habit with the given name.
        """
        if any(habit.name == name for habit in self.habits):
            return
        d = {"name": name, "records": [], "id": generate_short_hash(name)}
        self.data["habits"].append(d)

    async def remove(self, item: DictHabit) -> None:
        """
        Removes a habit from the list.
        """
        if item.data in self.data["habits"]:
            self.data["habits"].remove(item.data)

    async def merge_user_habit_list(self, other: 'DictHabitList') -> None:
        """
        Merges another habit list into this habit list.
        """
        existing_habits = {habit.id for habit in self.habits}
        for habit in other.habits:
            if habit.id in existing_habits:
                existing_habit = next(h for h in self.habits if h.id == habit.id)
                await existing_habit.merge(habit)
            else:
                self.data["habits"].append(habit.data)


This code snippet addresses the feedback by ensuring consistent inheritance, property types, method signatures, and data handling. The docstrings have been reviewed for clarity, and the overall structure has been maintained for better readability.