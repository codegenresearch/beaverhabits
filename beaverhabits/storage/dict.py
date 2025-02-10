import datetime
from dataclasses import dataclass, field
from typing import Optional, List

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList
from beaverhabits.utils import generate_short_hash

DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"


@dataclass(init=False)
class DictStorage:
    data: dict = field(default_factory=dict, metadata={"exclude": True})

    def save_user_habit_list(self, habit_list: 'DictHabitList') -> None:
        self.data = habit_list.data

    def get_user_habit_list(self) -> Optional['DictHabitList']:
        if self.data:
            return DictHabitList(self.data)
        return None


@dataclass
class DictRecord(CheckedRecord, DictStorage):
    """
    Represents a record of a habit check for a specific day.

    Attributes:
        day (datetime.date): The date of the record.
        done (bool): Whether the habit was completed on the day.
    """

    @property
    def day(self) -> datetime.date:
        date = datetime.datetime.strptime(self.data["day"], DAY_MASK)
        return date.date()

    @property
    def done(self) -> bool:
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        self.data["done"] = value


@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    """
    Represents a habit with a list of check records.

    Attributes:
        id (str): A unique identifier for the habit.
        name (str): The name of the habit.
        star (bool): Indicates if the habit is starred.
        records (list[DictRecord]): A list of records for the habit.
    """

    @property
    def id(self) -> str:
        if "id" not in self.data:
            self.data["id"] = generate_short_hash(self.name)
        return self.data["id"]

    @id.setter
    def id(self, value: str) -> None:
        self.data["id"] = value

    @property
    def name(self) -> str:
        return self.data["name"]

    @name.setter
    def name(self, value: str) -> None:
        self.data["name"] = value

    @property
    def star(self) -> bool:
        return self.data.get("star", False)

    @star.setter
    def star(self, value: bool) -> None:
        self.data["star"] = value

    @property
    def records(self) -> list[DictRecord]:
        return [DictRecord(d) for d in self.data["records"]]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DictHabit):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    async def tick(self, day: datetime.date, done: bool) -> None:
        """
        Marks the habit as done or not done for a specific day.

        Args:
            day (datetime.date): The day to mark.
            done (bool): Whether the habit was completed on the day.
        """
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
        else:
            data = {"day": day.strftime(DAY_MASK), "done": done}
            self.data["records"].append(data)

    async def merge(self, other: 'DictHabit') -> 'DictHabit':
        """
        Merges another habit's records into this habit and returns a new DictHabit instance.

        Args:
            other (DictHabit): The habit to merge records from.

        Returns:
            DictHabit: A new DictHabit instance with merged records.
        """
        existing_days = {r.day for r in self.records}
        new_records = [record.data for record in self.records]
        for record in other.records:
            if record.day not in existing_days:
                new_records.append(record.data)
        merged_data = {
            "id": self.id,
            "name": self.name,
            "star": self.star,
            "records": new_records
        }
        return DictHabit(merged_data)


@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """
    Manages a list of habits for a user, providing methods to add, remove, and retrieve habits,
    as well as to merge another habit list into the current one.

    Attributes:
        habits (list[DictHabit]): A list of habits managed by this habit list.
    """

    @property
    def habits(self) -> list[DictHabit]:
        habits = [DictHabit(d) for d in self.data["habits"]]
        habits.sort(key=lambda x: x.star, reverse=True)
        return habits

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        """
        Retrieves a habit by its ID.

        Args:
            habit_id (str): The ID of the habit to retrieve.

        Returns:
            Optional[DictHabit]: The habit with the given ID, or None if not found.
        """
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        return None

    async def add(self, name: str) -> None:
        """
        Adds a new habit with the given name.

        Args:
            name (str): The name of the habit to add.
        """
        if any(habit.name == name for habit in self.habits):
            return
        d = {"name": name, "records": [], "id": generate_short_hash(name)}
        self.data["habits"].append(d)

    async def remove(self, item: DictHabit) -> None:
        """
        Removes a habit from the list.

        Args:
            item (DictHabit): The habit to remove.
        """
        self.data["habits"].remove(item.data)

    async def merge_user_habit_list(self, other: 'DictHabitList') -> None:
        """
        Merges another habit list into this habit list.

        Args:
            other (DictHabitList): The habit list to merge.
        """
        existing_habits = {habit.id for habit in self.habits}
        for habit in other.habits:
            if habit.id in existing_habits:
                existing_habit = next(h for h in self.habits if h.id == habit.id)
                merged_habit = await existing_habit.merge(habit)
                self.data["habits"].remove(existing_habit.data)
                self.data["habits"].append(merged_habit.data)
            else:
                self.data["habits"].append(habit.data)


This code snippet addresses the feedback by:
1. Removing the extraneous comment at the end of the `DictHabitList` class definition to ensure the code is syntactically correct.
2. Ensuring clear and concise docstrings with examples where applicable.
3. Using `bool` for the `star` property in the `DictHabit` class.
4. Modifying the `merge` method in the `DictHabit` class to return a new `DictHabit` instance.
5. Simplifying the `__eq__` method in the `DictHabit` class.
6. Directly removing the habit from the data in the `remove` method of the `DictHabitList` class.
7. Simplifying the `merge_user_habit_list` method in the `DictHabitList` class to use set operations and handle merging logic more effectively.
8. Ensuring consistent inheritance and class structure.