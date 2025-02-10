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

    @property
    def star(self) -> bool:
        return self.data.get("star", False)

    @star.setter
    def star(self, value: bool) -> None:
        self.data["star"] = value

    @property
    def records(self) -> List[DictRecord]:
        return [DictRecord(d) for d in self.data["records"]]

    async def tick(self, day: datetime.date, done: bool) -> bool:
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
            return True
        else:
            data = {"day": day.strftime(DAY_MASK), "done": done}
            self.data["records"].append(data)
            return True

    async def merge(self, other: 'DictHabit') -> bool:
        for record in other.records:
            if not any(r.day == record.day for r in self.records):
                self.data["records"].append(record.data)
        return True


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
                return habit
        return None

    async def add(self, name: str) -> bool:
        if any(habit.name == name for habit in self.habits):
            return False
        d = {"name": name, "records": [], "id": generate_short_hash(name)}
        self.data["habits"].append(d)
        return True

    async def remove(self, item: DictHabit) -> bool:
        if item.data in self.data["habits"]:
            self.data["habits"].remove(item.data)
            return True
        return False

    async def merge_user_habit_list(self, other: 'DictHabitList') -> bool:
        for habit in other.habits:
            existing_habit = next((h for h in self.habits if h.id == habit.id), None)
            if existing_habit:
                await existing_habit.merge(habit)
            else:
                self.data["habits"].append(habit.data)
        return True