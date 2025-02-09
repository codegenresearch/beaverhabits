import datetime
from dataclasses import dataclass, field
from typing import Optional, List
import logging

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList
from beaverhabits.utils import generate_short_hash

DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"

logging.basicConfig(level=logging.INFO)

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
        logging.info(f"Updated record for day {self.day} to done={value}")

@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
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
        logging.info(f"Updated habit name to {value}")

    @property
    def star(self) -> bool:
        return self.data.get("star", False)

    @star.setter
    def star(self, value: int) -> None:
        self.data["star"] = value
        logging.info(f"Updated habit star to {value}")

    @property
    def records(self) -> List[DictRecord]:
        return [DictRecord(d) for d in self.data["records"]]

    async def tick(self, day: datetime.date, done: bool) -> None:
        try:
            if record := next((r for r in self.records if r.day == day), None):
                record.done = done
            else:
                data = {"day": day.strftime(DAY_MASK), "done": done}
                self.data["records"].append(data)
            logging.info(f"Ticked habit {self.name} for day {day} with done={done}")
        except Exception as e:
            logging.error(f"Failed to tick habit {self.name} for day {day}: {e}")

@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    @property
    def habits(self) -> List[DictHabit]:
        habits = [DictHabit(d) for d in self.data["habits"]]
        habits.sort(key=lambda x: x.star, reverse=True)
        return habits

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        for habit in self.habits:
            if habit.id == habit_id:
                logging.info(f"Retrieved habit with id {habit_id}")
                return habit
        logging.info(f"No habit found with id {habit_id}")
        return None

    async def add(self, name: str) -> None:
        try:
            d = {"name": name, "records": [], "id": generate_short_hash(name)}
            self.data["habits"].append(d)
            logging.info(f"Added new habit with name {name}")
        except Exception as e:
            logging.error(f"Failed to add habit with name {name}: {e}")

    async def remove(self, item: DictHabit) -> None:
        try:
            self.data["habits"].remove(item.data)
            logging.info(f"Removed habit with id {item.id}")
        except Exception as e:
            logging.error(f"Failed to remove habit with id {item.id}: {e}")