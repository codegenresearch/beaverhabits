import datetime
from dataclasses import dataclass, field
from typing import Optional, List
import logging

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
    """\n    Manages individual habit records with day and completion status.\n    """

    @property
    def day(self) -> datetime.date:
        try:
            date = datetime.datetime.strptime(self.data["day"], DAY_MASK)
            return date.date()
        except KeyError as e:
            logger.error(f"Missing key in data: {e}")
            raise
        except ValueError as e:
            logger.error(f"Error parsing date: {e}")
            raise

    @property
    def done(self) -> bool:
        try:
            return self.data["done"]
        except KeyError as e:
            logger.error(f"Missing key in data: {e}")
            raise

    @done.setter
    def done(self, value: bool) -> None:
        self.data["done"] = value

@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    """\n    Manages a habit with a unique ID, name, star status, and a list of records.\n    """

    @property
    def id(self) -> str:
        if "id" not in self.data:
            self.data["id"] = generate_short_hash(self.name)
        return self.data["id"]

    @property
    def name(self) -> str:
        try:
            return self.data["name"]
        except KeyError as e:
            logger.error(f"Missing key in data: {e}")
            raise

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
        try:
            return [DictRecord(d) for d in self.data["records"]]
        except KeyError as e:
            logger.error(f"Missing key in data: {e}")
            raise

    async def tick(self, day: datetime.date, done: bool) -> None:
        try:
            if record := next((r for r in self.records if r.day == day), None):
                record.done = done
            else:
                data = {"day": day.strftime(DAY_MASK), "done": done}
                self.data["records"].append(data)
        except Exception as e:
            logger.error(f"Error ticking habit: {e}")
            raise

@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """\n    Manages a list of habits with methods to add, remove, and retrieve habits.\n    """

    @property
    def habits(self) -> list[DictHabit]:
        try:
            habits = [DictHabit(d) for d in self.data["habits"]]
            habits.sort(key=lambda x: x.star, reverse=True)
            return habits
        except KeyError as e:
            logger.error(f"Missing key in data: {e}")
            raise

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        logger.info(f"Habit with ID {habit_id} not found.")
        return None

    async def add(self, name: str) -> None:
        try:
            d = {"name": name, "records": [], "id": generate_short_hash(name)}
            self.data["habits"].append(d)
        except Exception as e:
            logger.error(f"Error adding habit: {e}")
            raise

    async def remove(self, item: DictHabit) -> None:
        try:
            self.data["habits"].remove(item.data)
        except ValueError as e:
            logger.error(f"Error removing habit: {e}")
            raise

    async def merge(self, other: 'DictHabitList') -> None:
        """\n        Merges another habit list into this one, ensuring no duplicate habits.\n        """
        try:
            other_habits = {habit.id: habit for habit in other.habits}
            for habit in self.habits:
                if habit.id in other_habits:
                    # Merge records
                    existing_records = {record.day: record for record in habit.records}
                    for record in other_habits[habit.id].records:
                        if record.day not in existing_records:
                            existing_records[record.day] = record
                    habit.data["records"] = [record.data for record in existing_records.values()]
                else:
                    # Add new habit
                    self.data["habits"].append(habit.data)
            # Add habits from other that are not in self
            for habit_id, habit in other_habits.items():
                if habit_id not in {h.id for h in self.habits}:
                    self.data["habits"].append(habit.data)
        except Exception as e:
            logger.error(f"Error merging habit lists: {e}")
            raise