import datetime
import json
import logging
import random
import time
from typing import List, Optional

from fastapi import HTTPException
from nicegui import ui

from beaverhabits.app.db import User
from beaverhabits.storage import get_user_storage, session_storage
from beaverhabits.storage.dict import DAY_MASK, DictHabitList
from beaverhabits.storage.storage import Habit, HabitList
from beaverhabits.utils import generate_short_hash

logger = logging.getLogger(__name__)

user_storage = get_user_storage()

def dummy_habit_list(days: List[datetime.date]) -> DictHabitList:
    def pick() -> bool:
        return random.randint(0, 3) == 0

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
        logger.error("Habit list not found for session")
        raise HTTPException(status_code=404, detail="Habit list not found")

    habit = await habit_list.get_habit_by(habit_id)
    if habit is None:
        logger.error(f"Habit with ID {habit_id} not found in session")
        raise HTTPException(status_code=404, detail="Habit not found")

    return habit

def get_or_create_session_habit_list(days: List[datetime.date]) -> HabitList:
    if (habit_list := get_session_habit_list()) is not None:
        return habit_list

    habit_list = dummy_habit_list(days)
    session_storage.save_user_habit_list(habit_list)
    return habit_list

async def get_user_habit_list(user: User) -> Optional[HabitList]:
    return await user_storage.get_user_habit_list(user)

async def get_user_habit(user: User, habit_id: str) -> Habit:
    habit_list = await get_user_habit_list(user)
    if habit_list is None:
        logger.error(f"Habit list not found for user {user.id}")
        raise HTTPException(status_code=404, detail="Habit list not found")

    habit = await habit_list.get_habit_by(habit_id)
    if habit is None:
        logger.error(f"Habit with ID {habit_id} not found for user {user.id}")
        raise HTTPException(status_code=404, detail="Habit not found")

    return habit

async def get_or_create_user_habit_list(user: User, days: List[datetime.date]) -> HabitList:
    habit_list = await get_user_habit_list(user)
    if habit_list is not None:
        return habit_list

    habit_list = dummy_habit_list(days)
    await user_storage.save_user_habit_list(user, habit_list)
    return habit_list

async def merge_user_habit_lists(user: User, other_habit_list: HabitList) -> HabitList:
    try:
        merged_habit_list = await user_storage.merge_user_habit_list(user, other_habit_list)
        logger.info(f"Successfully merged habit lists for user {user.id}")
        return merged_habit_list
    except Exception as e:
        logger.error(f"Failed to merge habit lists for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to merge habit lists")

async def export_user_habit_list(habit_list: HabitList, user_identifier: str) -> None:
    if isinstance(habit_list, DictHabitList):
        data = {
            "user_email": user_identifier,
            "exported_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **habit_list.data,
        }
        binary_data = json.dumps(data).encode()
        file_name = f"habits_{int(float(time.time()))}.json"
        ui.download(binary_data, file_name)
        logger.info(f"Exported habit list for user {user_identifier} as {file_name}")
    else:
        ui.notification("Export failed, please try again later.")
        logger.error(f"Export failed for user {user_identifier}: Unsupported habit list type")