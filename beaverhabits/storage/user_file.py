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
            from beaverhabits.storage.dict import DictHabitList
        except ImportError as e:
            logger.error(f"Import failed: {e}")
            raise

    async def get_user_habit_list(self, user: User) -> Optional[DictHabitList]:
        try:
            d = self._get_persistent_dict(user).get(KEY_NAME)
            if not d:
                return None
            return DictHabitList(d)
        except Exception as e:
            logger.error(f"Failed to get user habit list for {user.email}: {e}")
            return None

    async def save_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        try:
            d = self._get_persistent_dict(user)
            current_habit_list = await self.get_user_habit_list(user)
            if current_habit_list:
                merged_habit_list = await current_habit_list.merge(habit_list)
                d[KEY_NAME] = merged_habit_list.data
            else:
                d[KEY_NAME] = habit_list.data
        except Exception as e:
            logger.error(f"Failed to save user habit list for {user.email}: {e}")

    def _get_persistent_dict(self, user: User) -> PersistentDict:
        try:
            path = Path(f"{USER_DATA_FOLDER}/{str(user.email)}.json")
            return PersistentDict(path, encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to create persistent dict for {user.email}: {e}")
            raise