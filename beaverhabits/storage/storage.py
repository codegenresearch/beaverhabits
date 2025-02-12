import datetime
from typing import List, Optional, Protocol, TypeVar

from beaverhabits.app.db import User
from beaverhabits.utils import generate_short_hash

R = TypeVar('R', bound='CheckedRecord')
H = TypeVar('H', bound='Habit')
L = TypeVar('L', bound='HabitList')

class CheckedRecord(Protocol):
    @property
    def day(self) -> datetime.date: ...

    @property
    def done(self) -> bool: ...

    @done.setter
    def done(self, value: bool) -> None: ...

    def __str__(self):
        return f"{self.day} {'[x]' if self.done else '[ ]'}"

    __repr__ = __str__

    def __eq__(self, other: 'CheckedRecord') -> bool:
        return self.day == other.day and self.done == other.done


class Habit(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, value: str) -> None: ...

    @property
    def star(self) -> bool: ...

    @star.setter
    def star(self, value: bool) -> None: ...

    @property
    def records(self) -> List[CheckedRecord]: ...

    @property
    def ticked_days(self) -> list[datetime.date]:
        return [r.day for r in self.records if r.done]

    async def tick(self, day: datetime.date, done: bool) -> None: ...

    async def merge(self, other: 'Habit') -> 'Habit': ...

    def __str__(self):
        return self.name

    __repr__ = __str__

    def __eq__(self, other: 'Habit') -> bool:
        return self.id == other.id


class HabitList(Protocol):
    @property
    def habits(self) -> List[Habit]: ...

    async def add(self, name: str) -> None: ...

    async def remove(self, item: Habit) -> None: ...

    async def get_habit_by(self, habit_id: str) -> Optional[Habit]: ...

    async def merge(self, other: 'HabitList') -> 'HabitList': ...

    def __eq__(self, other: 'HabitList') -> bool:
        return all(h in other.habits for h in self.habits) and all(h in self.habits for h in other.habits)


class SessionStorage(Protocol):
    def get_user_habit_list(self) -> Optional[HabitList]: ...

    def save_user_habit_list(self, habit_list: HabitList) -> None: ...


class UserStorage(Protocol):
    async def get_user_habit_list(self, user: User) -> Optional[HabitList]: ...

    async def save_user_habit_list(self, user: User, habit_list: HabitList) -> None: ...

    async def merge_user_habit_list(self, user: User, other: HabitList) -> HabitList: ...


# Enhanced CheckedRecord implementation with drag-and-drop support
@dataclass
class EnhancedCheckedRecord(CheckedRecord, DictStorage):
    id: str = field(default_factory=lambda: generate_short_hash(str(datetime.datetime.now())))

    @property
    def day(self) -> datetime.date:
        return datetime.datetime.strptime(self.data["day"], DAY_MASK).date()

    @property
    def done(self) -> bool:
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        self.data["done"] = value


# Enhanced Habit implementation with improved data handling and organization
@dataclass
class EnhancedHabit(Habit, DictStorage):
    id: str = field(default_factory=lambda: generate_short_hash(str(datetime.datetime.now())))
    name: str
    star: bool = False
    records: List[EnhancedCheckedRecord] = field(default_factory=list)

    def __post_init__(self):
        if "id" not in self.data:
            self.data["id"] = self.id
        if "name" not in self.data:
            self.data["name"] = self.name
        if "star" not in self.data:
            self.data["star"] = self.star
        if "records" not in self.data:
            self.data["records"] = [record.data for record in self.records]

    @property
    def id(self) -> str:
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
    def records(self) -> List[EnhancedCheckedRecord]:
        return [EnhancedCheckedRecord(d) for d in self.data["records"]]

    async def tick(self, day: datetime.date, done: bool) -> None:
        record = next((r for r in self.records if r.day == day), None)
        if record:
            record.done = done
        else:
            data = {"day": day.strftime(DAY_MASK), "done": done}
            self.data["records"].append(data)

    async def merge(self, other: 'EnhancedHabit') -> 'EnhancedHabit':
        self_ticks = {r.day for r in self.records if r.done}
        other_ticks = {r.day for r in other.records if r.done}
        result = sorted(list(self_ticks | other_ticks))

        d = {
            "name": self.name,
            "records": [
                {"day": day.strftime(DAY_MASK), "done": True} for day in result
            ],
        }
        return EnhancedHabit(d)


# Enhanced HabitList implementation with improved data handling and organization
@dataclass
class EnhancedHabitList(HabitList, DictStorage):
    habits: List[EnhancedHabit] = field(default_factory=list)
    order: List[str] = field(default_factory=list)

    def __post_init__(self):
        if "habits" not in self.data:
            self.data["habits"] = [habit.data for habit in self.habits]
        if "order" not in self.data:
            self.data["order"] = self.order

    @property
    def habits(self) -> List[EnhancedHabit]:
        habits = [EnhancedHabit(d) for d in self.data["habits"]]
        if self.order:
            habits.sort(
                key=lambda x: (
                    self.order.index(str(x.id))
                    if str(x.id) in self.order
                    else float("inf")
                )
            )
        else:
            habits.sort(key=lambda x: x.star, reverse=True)

        return habits

    @property
    def order(self) -> List[str]:
        return self.data.get("order", [])

    @order.setter
    def order(self, value: List[str]) -> None:
        self.data["order"] = value

    async def add(self, name: str) -> None:
        d = {"name": name, "records": [], "id": generate_short_hash(name)}
        self.data["habits"].append(d)

    async def remove(self, item: EnhancedHabit) -> None:
        self.data["habits"] = [h.data for h in self.habits if h.id != item.id]

    async def get_habit_by(self, habit_id: str) -> Optional[EnhancedHabit]:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit

    async def merge(self, other: 'EnhancedHabitList') -> 'EnhancedHabitList':
        result = set(self.habits).symmetric_difference(set(other.habits))

        # Merge the habit if it exists
        for self_habit in self.habits:
            for other_habit in other.habits:
                if self_habit == other_habit:
                    new_habit = await self_habit.merge(other_habit)
                    result.add(new_habit)

        return EnhancedHabitList({"habits": [h.data for h in result], "order": self.order})