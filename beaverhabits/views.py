import datetime
import json
import random
import time
from typing import List

from fastapi import HTTPException
from nicegui import ui

from beaverhabits.app.db import User
from beaverhabits.storage import get_user_storage, session_storage
from beaverhabits.storage.dict import DAY_MASK, DictHabitList
from beaverhabits.storage.storage import Habit, HabitList
from beaverhabits.utils import generate_short_hash

user_storage = get_user_storage()


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
        for name in ("Order pizz", "Running", "Table Tennis", "Clean", "Call mom")
    ]
    return DictHabitList({"habits": items})


def get_session_habit_list() -> HabitList | None:
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
    if (habit_list := get_session_habit_list()) is not None:
        return habit_list

    habit_list = dummy_habit_list(days)
    session_storage.save_user_habit_list(habit_list)
    return habit_list


async def get_user_habit_list(user: User) -> HabitList | None:
    return await user_storage.get_user_habit_list(user)


async def get_user_habit(user: User, habit_id: str) -> Habit:
    habit_list = await get_user_habit_list(user)
    if habit_list is None:
        raise HTTPException(status_code=404, detail="Habit list not found")

    habit = await habit_list.get_habit_by(habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    return habit


async def get_or_create_user_habit_list(
    user: User, days: List[datetime.date]
) -> HabitList:
    habit_list = await get_user_habit_list(user)
    if habit_list is not None:
        return habit_list

    habit_list = dummy_habit_list(days)
    await user_storage.save_user_habit_list(user, habit_list)
    return habit_list


async def export_user_habit_list(habit_list: HabitList, user_identify: str) -> None:
    # json to binary
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


# Adding merge functionality for HabitList
class DictHabit(Habit):
    def merge(self, other: "DictHabit") -> "DictHabit":
        merged_records = self.records + other.records
        return DictHabit(
            {"id": self.id, "name": self.name, "records": merged_records, "star": self.star}
        )

    def __str__(self):
        return f"{self.name} ({', '.join([str(r) for r in self.records])})"

    __repr__ = __str__


class DictHabitList(HabitList):
    def __init__(self, data: dict):
        self.data = data

    @property
    def habits(self) -> List[DictHabit]:
        return [DictHabit(**habit) for habit in self.data["habits"]]

    async def add(self, name: str) -> None:
        new_habit = DictHabit({"id": generate_short_hash(name), "name": name, "records": [], "star": False})
        self.data["habits"].append(new_habit)

    async def remove(self, item: DictHabit) -> None:
        self.data["habits"] = [habit for habit in self.data["habits"] if habit["id"] != item.id]

    async def get_habit_by(self, habit_id: str) -> Optional[DictHabit]:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        return None

    def __str__(self):
        return f"HabitList with {len(self.habits)} habits"

    __repr__ = __str__


# Updating session_storage and user_storage to use DictHabit and DictHabitList
class SessionStorage:
    def get_user_habit_list(self) -> Optional[DictHabitList]:
        return session_storage.get_user_habit_list()

    def save_user_habit_list(self, habit_list: DictHabitList) -> None:
        session_storage.save_user_habit_list(habit_list)


class UserStorage:
    async def get_user_habit_list(self, user: User) -> Optional[DictHabitList]:
        return await user_storage.get_user_habit_list(user)

    async def save_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        await user_storage.save_user_habit_list(user, habit_list)

    async def merge_user_habit_list(self, user: User, other: DictHabitList) -> DictHabitList:
        user_habit_list = await self.get_user_habit_list(user)
        if user_habit_list is None:
            return other

        merged_habit_list = DictHabitList({"habits": []})
        for habit in user_habit_list.habits:
            other_habit = await other.get_habit_by(habit.id)
            if other_habit:
                merged_habit = habit.merge(other_habit)
                merged_habit_list.data["habits"].append(merged_habit)
            else:
                merged_habit_list.data["habits"].append(habit)

        for habit in other.habits:
            if habit.id not in [h.id for h in merged_habit_list.habits]:
                merged_habit_list.data["habits"].append(habit)

        await self.save_user_habit_list(user, merged_habit_list)
        return merged_habit_list