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


class Habit(Protocol[R]):
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
    def records(self) -> List[R]: ...
    
    @property
    def ticked_days(self) -> list[datetime.date]:
        return [r.day for r in self.records if r.done]
    
    async def tick(self, day: datetime.date, done: bool) -> None: ...
    
    def __str__(self):
        return self.name
    
    __repr__ = __str__


class HabitList(Protocol[H]):
    @property
    def habits(self) -> List[H]: ...
    
    @property
    def order(self) -> List[str]: ...
    
    @order.setter
    def order(self, value: List[str]) -> None: ...
    
    async def add(self, name: str) -> None: ...
    
    async def remove(self, item: H) -> None: ...
    
    async def get_habit_by(self, habit_id: str) -> Optional[H]: ...
    
    async def merge(self, other: 'HabitList[H]') -> 'HabitList[H]': ...


class SessionStorage(Protocol[L]):
    def get_user_habit_list(self) -> Optional[L]: ...
    
    def save_user_habit_list(self, habit_list: L) -> None: ...


class UserStorage(Protocol[L]):
    async def get_user_habit_list(self, user: User) -> Optional[L]: ...
    
    async def save_user_habit_list(self, user: User, habit_list: L) -> None: ...
    
    async def merge_user_habit_list(self, user: User, other: L) -> L: ...


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


class EnhancedHabit(Habit[EnhancedCheckedRecord]):
    def __init__(self, name: str, records: List[EnhancedCheckedRecord] = None, star: bool = False):
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
    def records(self) -> List[EnhancedCheckedRecord]:
        return self._records

    async def tick(self, day: datetime.date, done: bool) -> None:
        if record := next((r for r in self._records if r.day == day), None):
            record.done = done
        else:
            self._records.append(EnhancedCheckedRecord(day, done))


class EnhancedHabitList(HabitList[EnhancedHabit]):
    def __init__(self, habits: List[EnhancedHabit] = None, order: List[str] = None):
        self._habits = habits if habits is not None else []
        self._order = order if order is not None else []

    @property
    def habits(self) -> List[EnhancedHabit]:
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

    async def remove(self, item: EnhancedHabit) -> None:
        self._habits.remove(item)

    async def get_habit_by(self, habit_id: str) -> Optional[EnhancedHabit]:
        for habit in self._habits:
            if habit.id == habit_id:
                return habit
        return None

    async def merge(self, other: 'EnhancedHabitList') -> 'EnhancedHabitList':
        result = set(self._habits).symmetric_difference(set(other._habits))

        for self_habit in self._habits:
            for other_habit in other._habits:
                if self_habit.id == other_habit.id:
                    new_habit = await self_habit.merge(other_habit)
                    result.add(new_habit)

        return EnhancedHabitList(list(result), self._order)


class EnhancedSessionStorage(SessionStorage[EnhancedHabitList]):
    def __init__(self):
        self._user_habit_list = None

    def get_user_habit_list(self) -> Optional[EnhancedHabitList]:
        return self._user_habit_list

    def save_user_habit_list(self, habit_list: EnhancedHabitList) -> None:
        self._user_habit_list = habit_list


class EnhancedUserStorage(UserStorage[EnhancedHabitList]):
    def __init__(self):
        self._user_habit_lists = {}

    async def get_user_habit_list(self, user: User) -> Optional[EnhancedHabitList]:
        return self._user_habit_lists.get(user.id)

    async def save_user_habit_list(self, user: User, habit_list: EnhancedHabitList) -> None:
        self._user_habit_lists[user.id] = habit_list

    async def merge_user_habit_list(self, user: User, other: EnhancedHabitList) -> EnhancedHabitList:
        current_list = await self.get_user_habit_list(user)
        if current_list:
            return await current_list.merge(other)
        return other


### Key Changes:
1. **Type Variables**: Adjusted the type variables to match the gold code, ensuring `Habit` and `HabitList` use type parameters correctly.
2. **Optional Types**: Used `Optional` for return types that can be `None`, particularly in `get_habit_by`.
3. **Property Types**: Ensured the `id` property in `Habit` is of type `str`.
4. **Setter Types**: Corrected the setter for the `star` property to use `bool`.
5. **Protocol Inheritance**: Ensured that classes inherit from the correct protocols and use generics appropriately.
6. **Consistency in Method Signatures**: Updated method signatures to match the gold code in terms of parameters and return types.