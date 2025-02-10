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

    @property
    def day(self) -> datetime.date:
        return datetime.datetime.strptime(self.data["day"], DAY_MASK).date()

    @day.setter
    def day(self, value: datetime.date) -> None:
        self.data["day"] = value.strftime(DAY_MASK)

    @property
    def done(self) -> bool:
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        self.data["done"] = value


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
        self.data["name"] = self.name
        self.data["star"] = self.star
        self.data["records"] = [record.data for record in self.records]

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
        return self.data["star"]

    @star.setter
    def star(self, value: bool) -> None:
        self.data["star"] = value

    @property
    def records(self) -> list[DictRecord]:
        return [DictRecord(**d) for d in self.data["records"]]

    @records.setter
    def records(self, value: List[DictRecord]) -> None:
        self.data["records"] = [record.data for record in value]

    async def tick(self, day: datetime.date, done: bool) -> None:
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
        else:
            self.records.append(DictRecord(day=day, done=done))
        self.data["records"] = [record.data for record in self.records]

    async def merge(self, other: "DictHabit") -> "DictHabit":
        self_ticks = {r.day for r in self.records if r.done}
        other_ticks = {r.day for r in other.records if r.done}
        result = sorted(list(self_ticks | other_ticks))

        self.data["records"] = [
            {"day": day.strftime(DAY_MASK), "done": True} for day in result
        ]
        return self

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DictHabit) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self):
        return self.name


@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    habits: List[DictHabit] = field(default_factory=list)
    order: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.data["habits"] = [habit.data for habit in self.habits]
        self.data["order"] = self.order

    @property
    def habits(self) -> list[DictHabit]:
        habits = [DictHabit(**d) for d in self.data["habits"]]
        habits.sort(key=lambda x: x.star, reverse=True)
        return habits

    @habits.setter
    def habits(self, value: List[DictHabit]) -> None:
        self.data["habits"] = [habit.data for habit in value]

    @property
    def order(self) -> List[str]:
        return self.data["order"]

    @order.setter
    def order(self, value: List[str]) -> None:
        self.data["order"] = value

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit

    async def add(self, name: str) -> None:
        new_habit = DictHabit(name=name)
        self.habits.append(new_habit)
        self.data["habits"] = [habit.data for habit in self.habits]
        self.order.append(new_habit.id)
        self.data["order"] = self.order

    async def remove(self, item: DictHabit) -> None:
        self.habits = [habit for habit in self.habits if habit.id != item.id]
        self.data["habits"] = [habit.data for habit in self.habits]
        self.order = [habit_id for habit_id in self.order if habit_id != item.id]
        self.data["order"] = self.order

    async def merge(self, other: "DictHabitList") -> "DictHabitList":
        result_habits = set(self.habits).symmetric_difference(set(other.habits))

        # Merge the habit if it exists
        for self_habit in self.habits:
            for other_habit in other.habits:
                if self_habit == other_habit:
                    new_habit = await self_habit.merge(other_habit)
                    result_habits.add(new_habit)

        result_habits = list(result_habits)
        result_habits.sort(key=lambda x: x.star, reverse=True)
        result_order = [habit.id for habit in result_habits]

        return DictHabitList(habits=result_habits, order=result_order)