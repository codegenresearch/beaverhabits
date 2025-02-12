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
logger = logging.getLogger(__name__)


async def get_sessions_storage() -> SessionStorage:
    logger.info("Retrieving session storage.")
    return session_storage


async def get_user_storage() -> UserStorage:
    logger.info("Retrieving user storage based on settings.")
    if settings.HABITS_STORAGE == StorageType.USER_DISK:
        logger.info("Using UserDiskStorage.")
        return user_disk_storage

    if settings.HABITS_STORAGE == StorageType.USER_DATABASE:
        logger.info("Using UserDatabaseStorage.")
        return user_database_storage

    logger.error("Storage type not implemented.")
    raise NotImplementedError("Storage type not implemented")
    # if self.STORAGE == StorageType.SQLITE:
    #     return None

async def merge_habit_lists_intelligently(user_storage: UserStorage, other_habit_list: DictHabitList) -> DictHabitList:
    logger.info("Merging habit lists intelligently.")
    current_habit_list = await user_storage.get_user_habit_list()
    if current_habit_list is None:
        logger.info("No current habit list found, using the other habit list.")
        return other_habit_list

    merged_habit_list = await current_habit_list.merge(other_habit_list)
    logger.info("Habit lists merged successfully.")
    return merged_habit_list