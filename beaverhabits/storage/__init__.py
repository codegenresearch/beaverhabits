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

logging.basicConfig(level=logging.INFO)

async def get_sessions_storage() -> SessionStorage:
    return session_storage

async def get_user_storage() -> UserStorage:
    if settings.HABITS_STORAGE == StorageType.USER_DISK:
        return user_disk_storage

    if settings.HABITS_STORAGE == StorageType.USER_DATABASE:
        return user_database_storage

    logging.error("Storage type not implemented")
    raise NotImplementedError("Storage type not implemented")

async def merge_habit_lists(user_storage: UserStorage, user: User, other: DictHabitList) -> DictHabitList:
    try:
        current = await user_storage.get_user_habit_list(user)
        if current is None:
            return other

        merged_list = await current.merge(other)
        await user_storage.save_user_habit_list(user, merged_list)
        logging.info(f"Successfully merged habit lists for user: {user.email}")
        return merged_list
    except Exception as e:
        logging.exception(f"Failed to merge habit lists for user: {user.email}")
        raise e