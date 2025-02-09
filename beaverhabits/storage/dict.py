import datetime
import logging
from dataclasses import dataclass, field
from typing import Optional, List

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList, UserStorage
from beaverhabits.utils import generate_short_hash

DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"

logger = logging.getLogger(__name__)

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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DictHabit):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    async def tick(self, day: datetime.date, done: bool) -> None:
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
        else:
            data = {"day": day.strftime(DAY_MASK), "done": done}
            self.data["records"].append(data)

    def merge(self, other: 'DictHabit') -> 'DictHabit':
        """
        Merges another habit into this one, combining records and updating star status.
        """
        merged_records = {r.day: r for r in self.records}
        for record in other.records:
            if record.day not in merged_records:
                merged_records[record.day] = record
            else:
                merged_records[record.day].done = merged_records[record.day].done or record.done
        self.data["records"] = [r.data for r in merged_records.values()]
        self.star = self.star or other.star
        return self

@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """
    Manages a list of habits with functionalities to add, remove, and retrieve habits.
    """

    @property
    def habits(self) -> list[DictHabit]:
        habits = [DictHabit(d) for d in self.data["habits"]]
        habits.sort(key=lambda x: x.star, reverse=True)
        return habits

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        return None

    async def add(self, name: str) -> None:
        d = {"name": name, "records": [], "id": generate_short_hash(name)}
        self.data["habits"].append(d)

    async def remove(self, item: DictHabit) -> None:
        self.data["habits"] = [h.data for h in self.habits if h != item]

    async def merge_user_habit_list(self, user: 'User', other: 'DictHabitList') -> 'DictHabitList':
        """
        Merges another habit list into this one, avoiding duplicates based on habit ID.
        """
        existing_habits = {habit.id: habit for habit in self.habits}
        for habit in other.habits:
            if habit.id in existing_habits:
                existing_habits[habit.id].merge(habit)
            else:
                self.data["habits"].append(habit.data)
        return self