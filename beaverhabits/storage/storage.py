import datetime
from typing import List, Optional, Protocol, TypeVar
from beaverhabits.app.db import User
import logging

# Setting up basic configuration for logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


class Habit(Protocol):
    @property
    def id(self) -> str:
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

    async def merge(self, other: 'Habit') -> 'Habit':
        """Merge the records of two habits."""
        try:
            self_ticks = {r.day for r in self.records if r.done}
            other_ticks = {r.day for r in other.records if r.done}
            merged_ticks = sorted(list(self_ticks | other_ticks))

            new_records = [{"day": day.strftime("%Y-%m-%d"), "done": True} for day in merged_ticks]
            return type(self)(id=self.id, name=self.name, records=new_records, star=self.star)
        except Exception as e:
            logger.error(f"Error merging habits: {e}")
            raise

    def __str__(self) -> str:
        """String representation of the habit."""
        return self.name

    __repr__ = __str__


class HabitList(Protocol):
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

    async def get_habit_by(self, habit_id: str) -> Optional[H]:
        """Get a habit by its ID."""
        ...

    async def merge(self, other: 'HabitList') -> 'HabitList':
        """Merge the habits of two lists."""
        try:
            result = set(self.habits).symmetric_difference(set(other.habits))

            for self_habit in self.habits:
                for other_habit in other.habits:
                    if self_habit == other_habit:
                        new_habit = await self_habit.merge(other_habit)
                        result.add(new_habit)

            return type(self)(habits=[h for h in result])
        except Exception as e:
            logger.error(f"Error merging habit lists: {e}")
            raise


class SessionStorage(Protocol):
    def get_user_habit_list(self) -> Optional[L]:
        """Get the habit list for the current session."""
        ...

    def save_user_habit_list(self, habit_list: L) -> None:
        """Save the habit list for the current session."""
        ...


class UserStorage(Protocol):
    async def get_user_habit_list(self, user: User) -> Optional[L]:
        """Get the habit list for a specific user."""
        ...

    async def save_user_habit_list(self, user: User, habit_list: L) -> None:
        """Save the habit list for a specific user."""
        ...