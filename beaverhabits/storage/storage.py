import datetime
from typing import List, Optional, Protocol, TypeVar

R = TypeVar('R', bound='CheckedRecord')
H = TypeVar('H', bound='Habit')
L = TypeVar('L', bound='HabitList')

class CheckedRecord(Protocol):
    @property
    def day(self) -> datetime.date:
        """Get the day of the record."""
        ...

    @property
    def done(self) -> bool:
        """Check if the record is marked as done."""
        ...

    @done.setter
    def done(self, value: bool) -> None:
        """Set the done status of the record."""
        ...

    def __str__(self) -> str:
        """String representation of the record."""
        return f"{self.day} {'[x]' if self.done else '[ ]'}"

    __repr__ = __str__


class Habit(Protocol[R]):
    @property
    def id(self) -> str | int:
        """Get the unique identifier of the habit."""
        ...

    @property
    def name(self) -> str:
        """Get the name of the habit."""
        ...

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the habit."""
        ...

    @property
    def star(self) -> bool:
        """Check if the habit is starred."""
        ...

    @star.setter
    def star(self, value: bool) -> None:
        """Set the star status of the habit."""
        ...

    @property
    def records(self) -> List[R]:
        """Get the list of records for the habit."""
        ...

    @property
    def ticked_days(self) -> List[datetime.date]:
        """Get the list of days the habit was marked as done."""
        return [r.day for r in self.records if r.done]

    async def tick(self, day: datetime.date, done: bool) -> None:
        """Mark the habit as done or not done for a specific day."""
        ...

    def __str__(self) -> str:
        """String representation of the habit."""
        return self.name

    __repr__ = __str__


class HabitList(Protocol[H]):
    @property
    def habits(self) -> List[H]:
        """Get the list of habits."""
        ...

    async def add(self, name: str) -> None:
        """Add a new habit to the list."""
        ...

    async def remove(self, item: H) -> None:
        """Remove a habit from the list."""
        ...

    async def get_habit_by(self, habit_id: str | int) -> Optional[H]:
        """Get a habit by its ID."""
        ...


class SessionStorage(Protocol[L]):
    def get_user_habit_list(self) -> Optional[L]:
        """Get the habit list for the current session."""
        ...

    def save_user_habit_list(self, habit_list: L) -> None:
        """Save the habit list for the current session."""
        ...


class UserStorage(Protocol[L]):
    async def get_user_habit_list(self, user: User) -> Optional[L]:
        """Get the habit list for a specific user."""
        ...

    async def save_user_habit_list(self, user: User, habit_list: L) -> None:
        """Save the habit list for a specific user."""
        ...