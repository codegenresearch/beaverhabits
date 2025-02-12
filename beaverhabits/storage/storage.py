import datetime
from typing import List, Optional, Protocol

from beaverhabits.app.db import User

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


class Habit[R: CheckedRecord](Protocol):
    @property
    def id(self) -> str | int: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, value: str) -> None: ...

    @property
    def star(self) -> bool: ...

    @star.setter
    def star(self, value: bool) -> None: ...  # Changed int to bool for consistency

    @property
    def records(self) -> List[R]: ...

    @property
    def ticked_days(self) -> list[datetime.date]:
        return [r.day for r in self.records if r.done]

    @property
    def status(self) -> str:  # Added status property for clarity
        ...

    @status.setter
    def status(self, value: str) -> None:  # Added status setter for clarity
        ...

    async def tick(self, day: datetime.date, done: bool) -> R:  # Changed to return the updated record
        ...

    async def edit(self, name: Optional[str] = None, star: Optional[bool] = None) -> 'Habit[R]':  # Added edit functionality
        ...

    def __str__(self):
        return f"{self.name} - {self.status}"  # Included status in string representation

    __repr__ = __str__


class HabitList[H: Habit](Protocol):
    @property
    def habits(self) -> List[H]: ...

    @property
    def order(self) -> List[str]: ...

    @order.setter
    def order(self, value: List[str]) -> None: ...

    async def add(self, name: str) -> H:  # Changed to return the added habit
        ...

    async def remove(self, item: H) -> H:  # Changed to return the removed habit
        ...

    async def get_habit_by(self, habit_id: str) -> Optional[H]: ...

    async def merge(self, other: 'HabitList[H]') -> 'HabitList[H]':  # Added merge functionality
        ...


class SessionStorage[L: HabitList](Protocol):
    def get_user_habit_list(self) -> Optional[L]: ...

    def save_user_habit_list(self, habit_list: L) -> None: ...


class UserStorage[L: HabitList](Protocol):
    async def get_user_habit_list(self, user: User) -> Optional[L]: ...

    async def save_user_habit_list(self, user: User, habit_list: L) -> None: ...

    async def merge_user_habit_list(self, user: User, other: L) -> L: ...

    async def drop_item(self, user: User, item: H) -> L:  # Added drop functionality with logging
        print(f"Dropping item {item} for user {user.id}")  # Logging drop event
        return await self.merge_user_habit_list(user, other)