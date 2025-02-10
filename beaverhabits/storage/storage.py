import datetime
from typing import List, Optional, Protocol
from enum import Enum

from beaverhabits.app.db import User


class HabitStatus(Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    SOFT_DELETED = "SOFT_DELETED"


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
    def star(self, value: bool) -> None: ...

    @property
    def status(self) -> HabitStatus: ...

    @status.setter
    def status(self, value: HabitStatus) -> None: ...

    @property
    def records(self) -> List[R]: ...

    @property
    def ticked_days(self) -> list[datetime.date]:
        return [r.day for r in self.records if r.done]

    async def tick(self, day: datetime.date, done: bool) -> None:
        record = next((r for r in self.records if r.day == day), None)
        if record:
            record.done = done
        else:
            new_record = {"day": day, "done": done}
            self.records.append(new_record)

    def __str__(self):
        return self.name

    __repr__ = __str__


class HabitList[H: Habit](Protocol):

    @property
    def habits(self) -> List[H]: ...

    @property
    def order(self) -> List[str]: ...

    @order.setter
    def order(self, value: List[str]) -> None: ...

    async def add(self, name: str) -> None:
        new_habit = {"name": name, "star": False, "status": HabitStatus.ACTIVE, "records": []}
        self.habits.append(new_habit)

    async def remove(self, item: H) -> None:
        self.habits.remove(item)

    async def get_habit_by(self, habit_id: str) -> Optional[H]:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        return None


class SessionStorage[L: HabitList](Protocol):
    def get_user_habit_list(self) -> Optional[L]: ...

    def save_user_habit_list(self, habit_list: L) -> None: ...


class UserStorage[L: HabitList](Protocol):
    async def get_user_habit_list(self, user: User) -> Optional[L]: ...

    async def save_user_habit_list(self, user: User, habit_list: L) -> None: ...

    async def merge_user_habit_list(self, user: User, other: L) -> L:
        user_habit_list = await self.get_user_habit_list(user)
        if user_habit_list:
            # Assuming merge logic is handled elsewhere or not needed
            await self.save_user_habit_list(user, other)
            return other
        else:
            await self.save_user_habit_list(user, other)
            return other