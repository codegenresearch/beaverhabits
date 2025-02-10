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
    def star(self, value: bool) -> None: ...

    @property
    def status(self) -> str: ...

    @status.setter
    def status(self, value: str) -> None: ...

    @property
    def records(self) -> List[R]: ...

    @property
    def ticked_days(self) -> list[datetime.date]:
        return [r.day for r in self.records if r.done]

    async def tick(self, day: datetime.date, done: bool) -> R:
        record = next((r for r in self.records if r.day == day), None)
        if record:
            record.done = done
            return record
        else:
            new_record = {"day": day, "done": done}
            self.records.append(new_record)
            return new_record

    async def edit(self, name: Optional[str] = None, star: Optional[bool] = None, status: Optional[str] = None) -> None:
        if name is not None:
            self.name = name
        if star is not None:
            self.star = star
        if status is not None:
            self.status = status

    def __str__(self):
        return f"{self.name} - Status: {self.status}"

    __repr__ = __str__


class HabitList[H: Habit](Protocol):

    @property
    def habits(self) -> List[H]: ...

    @property
    def order(self) -> List[str]: ...

    @order.setter
    def order(self, value: List[str]) -> None: ...

    async def add(self, name: str, star: bool = False, status: str = "ACTIVE") -> H:
        new_habit = {"name": name, "star": star, "status": status, "records": []}
        self.habits.append(new_habit)
        return new_habit

    async def remove(self, item: H) -> H:
        self.habits.remove(item)
        return item

    async def get_habit_by(self, habit_id: str) -> Optional[H]:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        return None

    async def merge(self, other: "HabitList") -> "HabitList":
        result = set(self.habits).symmetric_difference(set(other.habits))

        for self_habit in self.habits:
            for other_habit in other.habits:
                if self_habit == other_habit:
                    new_habit = await self_habit.merge(other_habit)
                    result.add(new_habit)

        return HabitList({"habits": list(result)})


class SessionStorage[L: HabitList](Protocol):
    def get_user_habit_list(self) -> Optional[L]: ...

    def save_user_habit_list(self, habit_list: L) -> None: ...


class UserStorage[L: HabitList](Protocol):
    async def get_user_habit_list(self, user: User) -> Optional[L]: ...

    async def save_user_habit_list(self, user: User, habit_list: L) -> None: ...

    async def merge_user_habit_list(self, user: User, other: L) -> L:
        user_habit_list = await self.get_user_habit_list(user)
        if user_habit_list:
            merged_list = await user_habit_list.merge(other)
            await self.save_user_habit_list(user, merged_list)
            return merged_list
        else:
            await self.save_user_habit_list(user, other)
            return other