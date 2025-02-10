from typing import Optional

from nicegui import background_tasks, core
from nicegui.storage import observables

from beaverhabits.app import crud
from beaverhabits.app.db import User
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import UserStorage


class DatabasePersistentDict(observables.ObservableDict):
    """Observable dictionary that backs up changes to the database."""

    def __init__(self, user: User, data: dict) -> None:
        """Initialize the observable dictionary with user and data."""
        self.user = user
        super().__init__(data, on_change=self.backup)

    def backup(self) -> None:
        """Backup the dictionary to the database asynchronously."""
        async def backup():
            try:
                await crud.update_user_habit_list(self.user, self)
            except Exception as e:
                print(f"Error backing up data for user {self.user.email}: {e}")

        if core.loop:
            background_tasks.create_lazy(backup(), name=self.user.email)
        else:
            core.app.on_startup(backup())


class UserDatabaseStorage(UserStorage[DictHabitList]):
    """Storage class for user habit lists using the database."""

    async def get_user_habit_list(self, user: User) -> Optional[DictHabitList]:
        """Retrieve the user's habit list from the database."""
        try:
            user_habit_list = await crud.get_user_habit_list(user)
            if user_habit_list is None:
                return None
            d = DatabasePersistentDict(user, user_habit_list.data)
            return DictHabitList(d)
        except Exception as e:
            print(f"Error retrieving habit list for user {user.email}: {e}")
            return None

    async def save_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        """Save the user's habit list to the database."""
        try:
            await crud.update_user_habit_list(user, habit_list.data)
        except Exception as e:
            print(f"Error saving habit list for user {user.email}: {e}")

    async def merge_user_habit_list(
        self, user: User, other: DictHabitList
    ) -> DictHabitList:
        """Merge the user's current habit list with another habit list."""
        try:
            current = await self.get_user_habit_list(user)
            if current is None:
                return other
            return await current.merge(other)
        except Exception as e:
            print(f"Error merging habit list for user {user.email}: {e}")
            return other


This version of the code includes:
- Consistent formatting and spacing around return statements.
- Added comments and docstrings for better readability and maintainability.
- Basic error handling with logging for each method to handle potential exceptions gracefully.