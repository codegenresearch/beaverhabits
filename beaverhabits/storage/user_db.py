from typing import Optional
import logging

from nicegui import background_tasks, core
from nicegui.storage import observables

from beaverhabits.app import crud
from beaverhabits.app.db import User
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import UserStorage

logger = logging.getLogger(__name__)

class DatabasePersistentDict(observables.ObservableDict):
    def __init__(self, user: User, data: dict) -> None:
        self.user = user
        super().__init__(data, on_change=self.backup)

    def backup(self) -> None:
        async def backup():
            try:
                await crud.update_user_habit_list(self.user, self)
                logger.info(f"Successfully backed up habit list for user {self.user.email}")
            except Exception as e:
                logger.error(f"Failed to backup habit list for user {self.user.email}: {e}")

        if core.loop:
            background_tasks.create_lazy(backup(), name=self.user.email)
        else:
            core.app.on_startup(backup())


class UserDatabaseStorage(UserStorage[DictHabitList]):
    async def get_user_habit_list(self, user: User) -> Optional[DictHabitList]:
        try:
            user_habit_list = await crud.get_user_habit_list(user)
            if user_habit_list is None:
                logger.info(f"No habit list found for user {user.email}")
                return None

            d = DatabasePersistentDict(user, user_habit_list.data)
            logger.info(f"Successfully retrieved habit list for user {user.email}")
            return DictHabitList(d)
        except Exception as e:
            logger.error(f"Failed to get habit list for user {user.email}: {e}")
            return None

    async def save_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        try:
            await crud.update_user_habit_list(user, habit_list.data)
            logger.info(f"Successfully saved habit list for user {user.email}")
        except Exception as e:
            logger.error(f"Failed to save habit list for user {user.email}: {e}")

    async def merge_user_habit_list(
        self, user: User, other: DictHabitList
    ) -> DictHabitList:
        try:
            current = await self.get_user_habit_list(user)
            if current is None:
                logger.info(f"No existing habit list found for user {user.email}, using provided list")
                return other

            merged = await current.merge(other)
            logger.info(f"Successfully merged habit lists for user {user.email}")
            return merged
        except Exception as e:
            logger.error(f"Failed to merge habit lists for user {user.email}: {e}")
            return other