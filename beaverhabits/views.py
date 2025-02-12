import datetime
import json
import random
from typing import List, Optional

from fastapi import HTTPException
from nicegui import ui

from beaverhabits.app.db import User
from beaverhabits.storage import get_user_storage, session_storage
from beaverhabits.storage.dict import DAY_MASK, DictHabitList
from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList, SessionStorage
from beaverhabits.utils import generate_short_hash

user_storage = get_user_storage()

class DictHabit(Habit):
    def __init__(self, data):
        self._data = data

    @property
    def id(self) -> str:
        return self._data["id"]

    @property
    def name(self) -> str:
        return self._data["name"]

    @name.setter
    def name(self, value: str) -> None:
        self._data["name"] = value

    @property
    def star(self) -> bool:
        return self._data.get("star", False)

    @star.setter
    def star(self, value: bool) -> None:
        self._data["star"] = value

    @property
    def records(self) -> List[CheckedRecord]:
        return [DictCheckedRecord(record) for record in self._data["records"]]

    @property
    def ticked_days(self) -> list[datetime.date]:
        return super().ticked_days

    async def tick(self, day: datetime.date, done: bool) -> None:
        record = next((r for r in self.records if r.day == day), None)
        if record:
            record.done = done
        else:
            self._data["records"].append({"day": day.strftime(DAY_MASK), "done": done})

    def __str__(self):
        return f"{self.name} - {'[x]' if self.star else '[ ]'} - {len(self.ticked_days)} days completed"

    __repr__ = __str__

    def merge(self, other: 'DictHabit') -> None:
        if self.id != other.id:
            raise ValueError("Can only merge habits with the same ID")
        other_records = {r.day: r.done for r in other.records}
        for record in self.records:
            record.done = other_records.get(record.day, record.done)
        for day, done in other_records.items():
            if day not in (r.day for r in self.records):
                self._data["records"].append({"day": day.strftime(DAY_MASK), "done": done})

class DictCheckedRecord(CheckedRecord):
    def __init__(self, data):
        self._data = data

    @property
    def day(self) -> datetime.date:
        return datetime.datetime.strptime(self._data["day"], DAY_MASK).date()

    @property
    def done(self) -> bool:
        return self._data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        self._data["done"] = value

    def __str__(self):
        return f"{self.day} {'[x]' if self.done else '[ ]'}"

    __repr__ = __str__

def dummy_habit_list(days: List[datetime.date]):
    pick = lambda: random.randint(0, 3) == 0
    items = [
        {
            "id": generate_short_hash(name),
            "name": name,
            "records": [
                {"day": day.strftime(DAY_MASK), "done": pick()} for day in days
            ],
        }
        for name in ("Order pizza", "Running", "Table Tennis", "Clean", "Call mom")
    ]
    return DictHabitList({"habits": items})

def get_session_habit_list() -> Optional[HabitList]:
    return session_storage.get_user_habit_list()

async def get_session_habit(habit_id: str) -> Habit:
    habit_list = get_session_habit_list()
    if habit_list is None:
        raise HTTPException(status_code=404, detail="Habit list not found")

    habit = await habit_list.get_habit_by(habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    return habit

def get_or_create_session_habit_list(days: List[datetime.date]) -> HabitList:
    return get_session_habit_list() or _create_habit_list(days)

async def get_user_habit_list(user: User) -> Optional[HabitList]:
    return await user_storage.get_user_habit_list(user)

async def get_user_habit(user: User, habit_id: str) -> Habit:
    habit_list = await get_user_habit_list(user)
    if habit_list is None:
        raise HTTPException(status_code=404, detail="Habit list not found")

    habit = await habit_list.get_habit_by(habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    return habit

async def get_or_create_user_habit_list(user: User, days: List[datetime.date]) -> HabitList:
    return await get_user_habit_list(user) or await _create_habit_list(user, days)

async def export_user_habit_list(habit_list: HabitList, user_identify: str) -> None:
    if isinstance(habit_list, DictHabitList):
        data = {
            "user_email": user_identify,
            "exported_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **habit_list.data,
        }
        binary_data = json.dumps(data).encode()
        file_name = f"habits_{int(float(time.time()))}.json"
        ui.download(binary_data, file_name)
    else:
        ui.notification("Export failed, please try again later.")

def _create_habit_list(target, days: List[datetime.date]) -> HabitList:
    habit_list = dummy_habit_list(days)
    if isinstance(target, SessionStorage):
        session_storage.save_user_habit_list(habit_list)
    else:
        await user_storage.save_user_habit_list(target, habit_list)
    return habit_list

class DictHabitList(HabitList):
    def __init__(self, data):
        self._data = data

    @property
    def habits(self) -> List[Habit]:
        return [DictHabit(habit) for habit in self._data["habits"]]

    async def add(self, name: str) -> None:
        self._data["habits"].append({
            "id": generate_short_hash(name),
            "name": name,
            "records": [],
        })

    async def remove(self, item: Habit) -> None:
        self._data["habits"] = [h for h in self._data["habits"] if h["id"] != item.id]

    async def get_habit_by(self, habit_id: str) -> Optional[Habit]:
        habit_data = next((h for h in self._data["habits"] if h["id"] == habit_id), None)
        return DictHabit(habit_data) if habit_data else None

    def merge(self, other: 'DictHabitList') -> None:
        other_habits = {h.id: h for h in other.habits}
        for habit in self.habits:
            if habit.id in other_habits:
                habit.merge(other_habits[habit.id])
            else:
                self._data["habits"].append(habit._data)
        for habit in other.habits:
            if habit.id not in (h.id for h in self.habits):
                self._data["habits"].append(habit._data)