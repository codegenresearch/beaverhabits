from pathlib import Path
from typing import Optional, Dict

from nicegui.storage import PersistentDict

from beaverhabits.app.db import User
from beaverhabits.configs import USER_DATA_FOLDER
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import UserStorage

KEY_NAME = "data"


class UserDiskStorage(UserStorage[DictHabitList]):
    async def get_user_dict_storage(self, user: User) -> Optional[DictHabitList]:
        d = self._get_persistent_dict(user).get(KEY_NAME)
        if not d:
            return None
        return DictHabitList(d)

    async def save_user_dict_storage(self, user: User, habit_list: DictHabitList) -> Dict[str, str]:
        current_habit_list = await self.get_user_dict_storage(user)
        if current_habit_list:
            merged_habit_list = await current_habit_list.merge(habit_list)
            d = self._get_persistent_dict(user)
            d[KEY_NAME] = merged_habit_list.data
            return {"status": "success", "message": "Habit list merged and saved successfully."}
        else:
            d = self._get_persistent_dict(user)
            d[KEY_NAME] = habit_list.data
            return {"status": "success", "message": "New habit list saved successfully."}

    def _get_persistent_dict(self, user: User) -> PersistentDict:
        path = Path(f"{USER_DATA_FOLDER}/{str(user.email)}.json")
        return PersistentDict(path, encoding="utf-8")