import datetime
from dataclasses import dataclass, field
from typing import Optional
import logging
import asyncio

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
    """\n    # Read (d1~d3)\n    persistent    ->     memory      ->     view\n    d0: [x]              d0: [x]\n                                            d1: [ ]\n    d2: [x]              d2: [x]            d2: [x]\n                                            d3: [ ]\n\n    # Update:\n    view(update)  ->     memory      ->     persistent\n    d1: [ ]\n    d2: [ ]              d2: [ ]            d2: [x]\n    d3: [x]              d3: [x]            d3: [ ]\n    """

    @property
    def day(self) -> datetime.date:
        try:
            date = datetime.datetime.strptime(self.data["day"], DAY_MASK)
            return date.date()
        except Exception as e:
            logging.error(f"Error parsing date: {e}")
            raise

    @property
    def done(self) -> bool:
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        self.data["done"] = value
        logging.info(f"Updated record for {self.day} to {'done' if value else 'not done'}")


@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    @property
    def id(self) -> str:
        if "id" not in self.data:
            self.data["id"] = generate_short_hash(self.name)
            logging.info(f"Generated new habit ID: {self.data['id']}")
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
    def star(self, value: bool) -> None:
        self.data["star"] = value
        logging.info(f"Updated habit star to {value}")

    @property
    def records(self) -> list[DictRecord]:
        return [DictRecord(d) for d in self.data["records"]]

    async def tick(self, day: datetime.date, done: bool) -> None:
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
            logging.info(f"Ticked day {day} for habit {self.name} to {'done' if done else 'not done'}")
        else:
            data = {"day": day.strftime(DAY_MASK), "done": done}
            self.data["records"].append(data)
            logging.info(f"Added new record for day {day} to habit {self.name} with status {'done' if done else 'not done'}")


@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    @property
    def habits(self) -> list[DictHabit]:
        habits = [DictHabit(d) for d in self.data["habits"]]
        habits.sort(key=lambda x: x.star, reverse=True)
        return habits

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        logging.info(f"Habit with ID {habit_id} not found")
        return None

    async def add(self, name: str) -> None:
        d = {"name": name, "records": [], "id": generate_short_hash(name)}
        self.data["habits"].append(d)
        logging.info(f"Added new habit with name {name} and ID {d['id']}")

    async def remove(self, item: DictHabit) -> None:
        try:
            self.data["habits"].remove(item.data)
            logging.info(f"Removed habit with ID {item.id}")
        except ValueError:
            logging.error(f"Habit with ID {item.id} not found in the list to remove")
            raise