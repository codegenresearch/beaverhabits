import datetime
from typing import List, Optional, Protocol, TypeVar

from beaverhabits.app.db import User
from beaverhabits.utils import log_action

R = TypeVar('R', bound='CheckedRecord')
H = TypeVar('H', bound='Habit')
L = TypeVar('L', bound='HabitList')

class CheckedRecord(Protocol):
    @property
    def day(self) -> datetime.date:
        ...

    @property
    def done(self) -> bool:
        ...

    @done.setter
    def done(self, value: bool) -> None:
        ...

    def __str__(self):
        return f"{self.day} {'[x]' if self.done else '[ ]'}"

    __repr__ = __str__


class Habit(Protocol):
    @property
    def id(self) -> str:
        ...

    @property
    def name(self) -> str:
        ...

    @name.setter
    def name(self, value: str) -> None:
        ...

    @property
    def star(self) -> bool:
        ...

    @star.setter
    def star(self, value: bool) -> None:
        ...

    @property
    def records(self) -> List[R]:
        ...

    @property
    def ticked_days(self) -> List[datetime.date]:
        return [r.day for r in self.records if r.done]

    @property
    def status(self) -> str:
        ...

    @status.setter
    def status(self, value: str) -> None:
        ...

    async def tick(self, day: datetime.date, done: bool) -> None:
        log_action(f"Ticking habit {self.id} on {day} with done={done}")

    def __str__(self):
        return self.name

    __repr__ = __str__


class HabitList(Protocol):
    @property
    def habits(self) -> List[H]:
        ...

    @property
    def order(self) -> List[str]:
        ...

    @order.setter
    def order(self, value: List[str]) -> None:
        ...

    async def add(self, name: str) -> None:
        log_action(f"Adding habit with name: {name}")

    async def remove(self, item: H) -> None:
        log_action(f"Removing habit with id: {item.id}")

    async def get_habit_by(self, habit_id: str) -> Optional[H]:
        log_action(f"Getting habit by id: {habit_id}")

    async def merge(self, other: 'HabitList') -> 'HabitList':
        log_action("Merging habit lists")


class SessionStorage(Protocol):
    def get_user_habit_list(self) -> Optional[L]:
        ...

    def save_user_habit_list(self, habit_list: L) -> None:
        log_action("Saving user habit list in session storage")


class UserStorage(Protocol):
    async def get_user_habit_list(self, user: User) -> Optional[L]:
        log_action(f"Getting user habit list for user: {user.id}")

    async def save_user_habit_list(self, user: User, habit_list: L) -> None:
        log_action(f"Saving user habit list for user: {user.id}")

    async def merge_user_habit_list(self, user: User, other: L) -> L:
        log_action(f"Merging user habit list for user: {user.id}")