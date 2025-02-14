import asyncio
import logging
from beaverhabits.configs import StorageType, settings
from beaverhabits.storage.session_file import SessionDictStorage, SessionStorage
from beaverhabits.storage.storage import UserStorage
from beaverhabits.storage.user_db import UserDatabaseStorage
from beaverhabits.storage.user_file import UserDiskStorage

session_storage = SessionDictStorage()
user_disk_storage = UserDiskStorage()
user_database_storage = UserDatabaseStorage()
sqlite_storage = None


def get_sessions_storage() -> SessionStorage:
    return session_storage


async def get_user_storage() -> UserStorage:
    if settings.HABITS_STORAGE == StorageType.USER_DISK:
        return user_disk_storage

    if settings.HABITS_STORAGE == StorageType.USER_DATABASE:
        return user_database_storage

    raise NotImplementedError("Storage type not implemented")

    # if self.STORAGE == StorageType.SQLITE:
    #     return None


async def async_import_json_data(json_data, user):
    try:
        habit_list = DictHabitList(json_data)
        if settings.HABITS_STORAGE == StorageType.USER_DISK:
            await user_disk_storage.save_user_habit_list(user, habit_list)
        elif settings.HABITS_STORAGE == StorageType.USER_DATABASE:
            await user_database_storage.save_user_habit_list(user, habit_list)
        else:
            raise NotImplementedError("Storage type not implemented")
    except Exception as e:
        logging.exception("Failed to import JSON data: %s", e)


async def merge_habit_lists(user, new_habit_list):
    if settings.HABITS_STORAGE == StorageType.USER_DISK:
        return await user_disk_storage.merge_user_habit_list(user, new_habit_list)
    elif settings.HABITS_STORAGE == StorageType.USER_DATABASE:
        return await user_database_storage.merge_user_habit_list(user, new_habit_list)
    else:
        raise NotImplementedError("Storage type not implemented")