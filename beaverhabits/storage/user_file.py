from pathlib import Path
from typing import Optional
import logging

from nicegui.storage import PersistentDict

from beaverhabits.app.db import User
from beaverhabits.configs import USER_DATA_FOLDER
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import UserStorage

KEY_NAME = "data"
logger = logging.getLogger(__name__)

class UserDiskStorage(UserStorage[DictHabitList]):
    def __init__(self):
        try:
            from beaverhabits.app.db import User
            from beaverhabits.configs import USER_DATA_FOLDER
            from beaverhabits.storage.dict import DictHabitList
            from beaverhabits.storage.storage import UserStorage
        except ImportError as e:
            logger.error(f"Import error: {e}")
            raise

    async def get_user_habit_list(self, user: User) -> Optional[DictHabitList]:
        try:
            d = self._get_persistent_dict(user).get(KEY_NAME)
            if not d:
                return None
            return DictHabitList(d)
        except Exception as e:
            logger.error(f"Error retrieving user habit list: {e}")
            return None

    async def save_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        try:
            d = self._get_persistent_dict(user)
            current_habit_list = d.get(KEY_NAME, {})
            merged_habit_list = await self._merge_habit_lists(current_habit_list, habit_list.data)
            d[KEY_NAME] = merged_habit_list
        except Exception as e:
            logger.error(f"Error saving user habit list: {e}")

    async def _merge_habit_lists(self, current: dict, other: dict) -> dict:
        try:
            current_habit_list = DictHabitList(current)
            other_habit_list = DictHabitList(other)
            merged_habit_list = await current_habit_list.merge(other_habit_list)
            return merged_habit_list.data
        except Exception as e:
            logger.error(f"Error merging habit lists: {e}")
            return current

    def _get_persistent_dict(self, user: User) -> PersistentDict:
        try:
            path = Path(f"{USER_DATA_FOLDER}/{str(user.email)}.json")
            return PersistentDict(path, encoding="utf-8")
        except Exception as e:
            logger.error(f"Error creating persistent dict: {e}")
            raise