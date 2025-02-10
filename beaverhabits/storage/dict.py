import datetime
from dataclasses import dataclass, field
from typing import Optional, List
from pydantic import BaseModel, validator

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList
from beaverhabits.utils import generate_short_hash

DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"


@dataclass(init=False)
class DictStorage:
    data: dict = field(default_factory=dict, metadata={"exclude": True})


@dataclass
class DictRecord(CheckedRecord, DictStorage):
    day: datetime.date
    done: bool

    def __post_init__(self):
        self.data["day"] = self.day.strftime(DAY_MASK)
        self.data["done"] = self.done


@dataclass
class HabitAddCard(BaseModel):
    name: str

    @validator('name')
    def name_must_be_valid(cls, v):
        if not v:
            raise ValueError('Name cannot be empty')
        return v


@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    name: str
    star: bool = False
    records: List[DictRecord] = field(default_factory=list)

    def __post_init__(self):
        self.data["id"] = generate_short_hash(self.name)
        self.data["name"] = self.name
        self.data["star"] = self.star
        self.data["records"] = [record.data for record in self.records]

    @property
    def id(self) -> str:
        return self.data["id"]

    @property
    def records(self) -> list[DictRecord]:
        return [DictRecord(**d) for d in self.data["records"]]

    async def tick(self, day: datetime.date, done: bool) -> None:
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
        else:
            self.records.append(DictRecord(day=day, done=done))
        self.data["records"] = [record.data for record in self.records]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DictHabit) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    habits: List[DictHabit] = field(default_factory=list)

    def __post_init__(self):
        self.data["habits"] = [habit.data for habit in self.habits]

    @property
    def habits(self) -> list[DictHabit]:
        habits = [DictHabit(**d) for d in self.data["habits"]]
        habits.sort(key=lambda x: x.star, reverse=True)
        return habits

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit

    async def add(self, name: str) -> None:
        new_habit = DictHabit(name=name)
        self.habits.append(new_habit)
        self.data["habits"] = [habit.data for habit in self.habits]

    async def remove(self, item: DictHabit) -> None:
        self.habits.remove(item)
        self.data["habits"] = [habit.data for habit in self.habits]