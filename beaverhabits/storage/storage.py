import datetime
from typing import List, Optional, Protocol
from beaverhabits.app.db import User
from beaverhabits.utils import log_action

class CheckedRecord(Protocol):
    @property
    def day(self) -> datetime.date: ...

    @property
    def done(self) -> bool: ...

    @done.setter
    def done(self, value: bool) -> None: 
        log_action(f"Setting done status for {self.day} to {value}")
        ...

    def __str__(self):
        return f"{self.day} {'[x]' if self.done else '[ ]'}"

    __repr__ = __str__


class Habit[R: CheckedRecord](Protocol):
    @property
    def id(self) -> str | int: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, value: str) -> None: 
        log_action(f"Renaming habit {self.id} to {value}")
        ...

    @property
    def star(self) -> bool: ...

    @star.setter
    def star(self, value: int) -> None: 
        log_action(f"Setting star status for habit {self.id} to {value}")
        ...

    @property
    def records(self) -> List[R]: ...

    @property
    def ticked_days(self) -> list[datetime.date]:
        return [r.day for r in self.records if r.done]

    async def tick(self, day: datetime.date, done: bool) -> None: 
        log_action(f"Ticking habit {self.id} on {day} with status {done}")
        ...

    def __str__(self):
        return self.name

    __repr__ = __str__


class HabitList[H: Habit](Protocol):

    @property
    def habits(self) -> List[H]: ...

    @property
    def order(self) -> List[str]: ...

    @order.setter
    def order(self, value: List[str]) -> None: 
        log_action(f"Setting order to {value}")
        ...

    async def add(self, name: str) -> None: 
        log_action(f"Adding habit with name {name}")
        ...

    async def remove(self, item: H) -> None: 
        log_action(f"Removing habit {item.id}")
        ...

    async def get_habit_by(self, habit_id: str) -> Optional[H]: 
        log_action(f"Getting habit by id {habit_id}")
        ...


class SessionStorage[L: HabitList](Protocol):
    def get_user_habit_list(self) -> Optional[L]: 
        log_action("Getting user habit list from session")
        ...

    def save_user_habit_list(self, habit_list: L) -> None: 
        log_action("Saving user habit list to session")
        ...


class UserStorage[L: HabitList](Protocol):
    async def get_user_habit_list(self, user: User) -> Optional[L]: 
        log_action(f"Getting user habit list for user {user.id}")
        ...

    async def save_user_habit_list(self, user: User, habit_list: L) -> None: 
        log_action(f"Saving user habit list for user {user.id}")
        ...

    async def merge_user_habit_list(self, user: User, other: L) -> L: 
        log_action(f"Merging user habit list for user {user.id}")
        ...