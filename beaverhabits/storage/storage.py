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

    def __str__(self):
        return self.name

    __repr__ = __str__


class HabitList(Protocol):
    @property
    def habits(self) -> List[Habit]: ...

    async def add(self, name: str) -> None: ...

    async def remove(self, item: Habit) -> None: ...

    async def get_habit_by(self, habit_id: str) -> Optional[Habit]: ...

    async def merge(self, other: 'HabitList') -> 'HabitList': ...


class SessionStorage(Protocol):
    def get_user_habit_list(self) -> Optional[HabitList]: ...

    def save_user_habit_list(self, habit_list: HabitList) -> None: ...


class UserStorage(Protocol):
    async def get_user_habit_list(self, user: User) -> Optional[HabitList]: ...

    async def save_user_habit_list(self, user: User, habit_list: HabitList) -> None: ...

    async def merge_user_habit_list(self, user: User, other: HabitList) -> HabitList: ...


class EnhancedCheckedRecord(CheckedRecord):
    def __init__(self, day: datetime.date, done: bool):
        self._day = day
        self._done = done

    @property
    def day(self) -> datetime.date:
        return self._day

    @property
    def done(self) -> bool:
        return self._done

    @done.setter
    def done(self, value: bool) -> None:
        self._done = value


class EnhancedHabit(Habit):
    def __init__(self, name: str, records: List[CheckedRecord] = None, star: bool = False):
        self._id = generate_short_hash(name)
        self._name = name
        self._star = star
        self._records = records if records is not None else []

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        self._id = generate_short_hash(value)

    @property
    def star(self) -> bool:
        return self._star

    @star.setter
    def star(self, value: bool) -> None:
        self._star = value

    @property
    def records(self) -> List[CheckedRecord]:
        return self._records

    async def tick(self, day: datetime.date, done: bool) -> None:
        if record := next((r for r in self._records if r.day == day), None):
            record.done = done
        else:
            self._records.append(EnhancedCheckedRecord(day, done))


class EnhancedHabitList(HabitList):
    def __init__(self, habits: List[Habit] = None, order: List[str] = None):
        self._habits = habits if habits is not None else []
        self._order = order if order is not None else []

    @property
    def habits(self) -> List[Habit]:
        habits = self._habits.copy()
        if self._order:
            habits.sort(
                key=lambda x: (
                    self._order.index(str(x.id))
                    if str(x.id) in self._order
                    else float("inf")
                )
            )
        else:
            habits.sort(key=lambda x: x.star, reverse=True)
        return habits

    @property
    def order(self) -> List[str]:
        return self._order

    @order.setter
    def order(self, value: List[str]) -> None:
        self._order = value

    async def add(self, name: str) -> None:
        new_habit = EnhancedHabit(name)
        self._habits.append(new_habit)

    async def remove(self, item: Habit) -> None:
        self._habits.remove(item)

    async def get_habit_by(self, habit_id: str) -> Optional[Habit]:
        for habit in self._habits:
            if habit.id == habit_id:
                return habit

    async def merge(self, other: 'EnhancedHabitList') -> 'EnhancedHabitList':
        result = set(self._habits).symmetric_difference(set(other._habits))

        for self_habit in self._habits:
            for other_habit in other._habits:
                if self_habit.id == other_habit.id:
                    new_habit = await self_habit.merge(other_habit)
                    result.add(new_habit)

        return EnhancedHabitList(list(result), self._order)


class EnhancedSessionStorage(SessionStorage):
    def __init__(self):
        self._user_habit_list = None

    def get_user_habit_list(self) -> Optional[HabitList]:
        return self._user_habit_list

    def save_user_habit_list(self, habit_list: HabitList) -> None:
        self._user_habit_list = habit_list


class EnhancedUserStorage(UserStorage):
    def __init__(self):
        self._user_habit_lists = {}

    async def get_user_habit_list(self, user: User) -> Optional[HabitList]:
        return self._user_habit_lists.get(user.id)

    async def save_user_habit_list(self, user: User, habit_list: HabitList) -> None:
        self._user_habit_lists[user.id] = habit_list

    async def merge_user_habit_list(self, user: User, other: HabitList) -> HabitList:
        current_list = await self.get_user_habit_list(user)
        if current_list:
            return await current_list.merge(other)
        return other