import datetime
from dataclasses import dataclass, field
from typing import List

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList
from beaverhabits.utils import generate_short_hash

DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"

@dataclass(init=False)
class DictStorage:
    """
    Base class for storage classes that use a dictionary to store data.
    """
    data: dict = field(default_factory=dict, metadata={"exclude": True})

@dataclass
class DictRecord(CheckedRecord, DictStorage):
    """
    Represents a single record of a habit, including the day and whether it was completed.

    Attributes:
        data (dict): A dictionary containing the record's data.

    Example:
        >>> record = DictRecord({"day": "2023-10-01", "done": True})
        >>> record.day
        datetime.date(2023, 10, 1)
        >>> record.done
        True
    """

    @property
    def day(self) -> datetime.date:
        """
        Returns the day of the record as a datetime.date object.
        """
        return datetime.datetime.strptime(self.data["day"], DAY_MASK).date()

    @property
    def done(self) -> bool:
        """
        Returns the completion status of the record.
        """
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        """
        Sets the completion status of the record.
        """
        self.data["done"] = value

@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    """
    Represents a habit with a name, star status, and a list of records.

    Attributes:
        data (dict): A dictionary containing the habit's data.

    Example:
        >>> habit = DictHabit({"name": "Exercise", "records": [{"day": "2023-10-01", "done": True}], "id": "abc123"})
        >>> habit.name
        'Exercise'
        >>> habit.star
        False
        >>> habit.records
        [DictRecord(data={'day': '2023-10-01', 'done': True})]
    """

    @property
    def id(self) -> str:
        """
        Returns the unique identifier for the habit. Generates a new ID if it doesn't exist.
        """
        if "id" not in self.data:
            self.data["id"] = generate_short_hash(self.name)
        return self.data["id"]

    @property
    def name(self) -> str:
        """
        Returns the name of the habit.
        """
        return self.data["name"]

    @name.setter
    def name(self, value: str) -> None:
        """
        Sets the name of the habit.
        """
        self.data["name"] = value

    @property
    def star(self) -> bool:
        """
        Returns the star status of the habit.
        """
        return self.data.get("star", False)

    @star.setter
    def star(self, value: bool) -> None:
        """
        Sets the star status of the habit.
        """
        self.data["star"] = value

    @property
    def records(self) -> List[DictRecord]:
        """
        Returns a list of records associated with the habit.
        """
        return [DictRecord(d) for d in self.data["records"]]

    def __eq__(self, other: 'DictHabit') -> bool:
        """
        Checks if two habits are equal based on their IDs.
        """
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Returns the hash value of the habit based on its ID.
        """
        return hash(self.id)

    async def tick(self, day: datetime.date, done: bool) -> None:
        """
        Updates the completion status of a record for a specific day.
        """
        if record := next((r for r in self.records if r.day == day), None):
            record.done = done
        else:
            data = {"day": day.strftime(DAY_MASK), "done": done}
            self.data["records"].append(data)

    def merge(self, other: 'DictHabit') -> 'DictHabit':
        """
        Merges another habit into this one, combining records and updating star status.
        """
        records_dict = {r.day: r for r in self.records}
        for record in other.records:
            if record.day not in records_dict:
                records_dict[record.day] = record
            else:
                records_dict[record.day].done = records_dict[record.day].done or record.done
        self.data["records"] = [r.data for r in records_dict.values()]
        self.star = self.star or other.star
        return self

@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    """
    Manages a list of habits with functionalities to add, remove, and retrieve habits.

    Attributes:
        data (dict): A dictionary containing the list of habits.

    Example:
        >>> habit_list = DictHabitList({"habits": [{"name": "Exercise", "records": [{"day": "2023-10-01", "done": True}], "id": "abc123"}]})
        >>> habit_list.habits
        [DictHabit(data={'name': 'Exercise', 'records': [{'day': '2023-10-01', 'done': True}], 'id': 'abc123'})]
    """

    @property
    def habits(self) -> List[DictHabit]:
        """
        Returns a sorted list of habits, prioritizing starred habits.
        """
        habits = [DictHabit(d) for d in self.data["habits"]]
        habits.sort(key=lambda x: x.star, reverse=True)
        return habits

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        """
        Retrieves a habit by its unique ID.
        """
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        return None

    async def add(self, name: str) -> None:
        """
        Adds a new habit to the list.
        """
        d = {"name": name, "records": [], "id": generate_short_hash(name)}
        self.data["habits"].append(d)

    async def remove(self, item: DictHabit) -> None:
        """
        Removes a habit from the list based on its ID.
        """
        self.data["habits"] = [h.data for h in self.habits if h.id != item.id]