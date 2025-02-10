from pathlib import Path
from typing import Optional

from nicegui.storage import PersistentDict

from beaverhabits.app.db import User
from beaverhabits.configs import USER_DATA_FOLDER
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import UserStorage

KEY_NAME = "data"


class UserDiskStorage(UserStorage[DictHabitList]):
    async def get_user_habit_list(self, user: User) -> Optional[DictHabitList]:
        d = self._get_persistent_dict(user).get(KEY_NAME)
        if not d:
            return None
        return DictHabitList(d)

    async def save_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        current_habit_list = await self.get_user_habit_list(user)
        if current_habit_list:
            merged_habit_list = await self.merge_user_habit_list(current_habit_list, habit_list)
            d = self._get_persistent_dict(user)
            d[KEY_NAME] = merged_habit_list.data
        else:
            d = self._get_persistent_dict(user)
            d[KEY_NAME] = habit_list.data

    async def merge_user_habit_list(
        self, user_habit_list: DictHabitList, other: DictHabitList
    ) -> DictHabitList:
        return await user_habit_list.merge(other)

    def _get_persistent_dict(self, user: User) -> PersistentDict:
        path = Path(f"{USER_DATA_FOLDER}/{str(user.email)}.json")
        return PersistentDict(path, encoding="utf-8")