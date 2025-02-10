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
        try:
            date = datetime.datetime.strptime(self.data["day"], DAY_MASK)
            return date.date()
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing day from data: {self.data}. Error: {e}")
            raise

    @property
    def done(self) -> bool:
        try:
            return self.data["done"]
        except KeyError as e:
            logger.error(f"Error accessing 'done' in data: {self.data}. Error: {e}")
            raise

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

    @property
    def name(self) -> str:
        try:
            return self.data["name"]
        except KeyError as e:
            logger.error(f"Error accessing 'name' in data: {self.data}. Error: {e}")
            raise

    @name.setter
    def name(self, value: str) -> None:
        self.data["name"] = value

    @property
    def star(self) -> bool:
        return self.data.get("star", False)

    @star.setter
    def star(self, value: bool) -> None:  # Changed from int to bool
        self.data["star"] = value

    @property
    def records(self) -> List[DictRecord]:
        try:
            return [DictRecord(d) for d in self.data["records"]]
        except KeyError as e:
            logger.error(f"Error accessing 'records' in data: {self.data}. Error: {e}")
            raise

    async def tick(self, day: datetime.date, done: bool) -> None:
        try:
            if record := next((r for r in self.records if r.day == day), None):
                record.done = done
            else:
                data = {"day": day.strftime(DAY_MASK), "done": done}
                self.data["records"].append(data)
        except Exception as e:
            logger.error(f"Error ticking habit: {self.name} on day: {day}. Error: {e}")
            raise

@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """
    Manages a list of habits with functionalities to add, remove, and retrieve habits.
    """

    @property
    def habits(self) -> List[DictHabit]:
        try:
            habits = [DictHabit(d) for d in self.data["habits"]]
            habits.sort(key=lambda x: x.star, reverse=True)
            return habits
        except KeyError as e:
            logger.error(f"Error accessing 'habits' in data: {self.data}. Error: {e}")
            raise

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        logger.warning(f"Habit with id {habit_id} not found.")
        return None

    async def add(self, name: str) -> None:
        try:
            d = {"name": name, "records": [], "id": generate_short_hash(name)}
            self.data["habits"].append(d)
        except Exception as e:
            logger.error(f"Error adding habit: {name}. Error: {e}")
            raise

    async def remove(self, item: DictHabit) -> None:
        try:
            self.data["habits"].remove(item.data)
        except ValueError as e:
            logger.error(f"Error removing habit: {item.name}. Error: {e}")
            raise

    async def merge(self, other: 'DictHabitList') -> None:
        """
        Merges another habit list into this one, avoiding duplicates based on habit id.
        """
        try:
            existing_ids = {habit.id for habit in self.habits}
            for habit in other.habits:
                if habit.id not in existing_ids:
                    self.data["habits"].append(habit.data)
                else:
                    logger.info(f"Habit with id {habit.id} already exists and will not be merged.")
        except Exception as e:
            logger.error(f"Error merging habit lists. Error: {e}")
            raise