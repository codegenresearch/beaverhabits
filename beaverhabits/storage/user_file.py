from pathlib import Path
from typing import Optional
import logging
import asyncio

from nicegui.storage import PersistentDict

from beaverhabits.app.db import User
from beaverhabits.configs import USER_DATA_FOLDER
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import UserStorage

KEY_NAME = "data"
LOGGER = logging.getLogger(__name__)


class UserDiskStorage(UserStorage[DictHabitList]):
    async def get_user_habit_list(self, user: User) -> Optional[DictHabitList]:
        try:
            d = await self._get_persistent_dict(user).get(KEY_NAME)
            if not d:
                return None
            return DictHabitList(d)
        except Exception as e:
            LOGGER.error(f"Error retrieving user habit list for {user.email}: {e}")
            return None

    async def save_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        try:
            d = await self._get_persistent_dict(user)
            d[KEY_NAME] = habit_list.data
        except Exception as e:
            LOGGER.error(f"Error saving user habit list for {user.email}: {e}")

    async def merge_user_habit_list(
        self, user: User, other: DictHabitList
    ) -> DictHabitList:
        try:
            current = await self.get_user_habit_list(user)
            if current is None:
                return other

            merged_habit_list = await current.merge(other)
            await self.save_user_habit_list(user, merged_habit_list)
            return merged_habit_list
        except Exception as e:
            LOGGER.error(f"Error merging user habit list for {user.email}: {e}")
            return other

    async def _get_persistent_dict(self, user: User) -> PersistentDict:
        path = Path(f"{USER_DATA_FOLDER}/{str(user.email)}.json")
        return PersistentDict(path, encoding="utf-8")