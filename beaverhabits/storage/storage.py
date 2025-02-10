from typing import List, Optional, Protocol

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
    def records(self) -> List['CheckedRecord']: ...

    @property
    def ticked_days(self) -> List[datetime.date]:
        return [r.day for r in self.records if r.done]

    async def tick(self, day: datetime.date, done: bool) -> None: ...

    def __str__(self):
        return self.name

    __repr__ = __str__


class HabitList(Protocol):
    @property
    def habits(self) -> List['Habit']: ...

    async def add(self, name: str) -> None: ...

    async def remove(self, item: 'Habit') -> None: ...

    async def get_habit_by(self, habit_id: str) -> Optional['Habit']: ...

    async def merge(self, other: 'HabitList') -> 'HabitList': ...


class SessionStorage(Protocol):
    def get_user_habit_list(self) -> Optional['HabitList']: ...

    def save_user_habit_list(self, habit_list: 'HabitList') -> None: ...


class UserStorage(Protocol):
    async def get_user_habit_list(self, user: 'User') -> Optional['HabitList']: ...

    async def save_user_habit_list(self, user: 'User', habit_list: 'HabitList') -> None: ...

    async def merge_user_habit_list(self, user: 'User', other_habit_list: 'HabitList') -> 'HabitList': ...