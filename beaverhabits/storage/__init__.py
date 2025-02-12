from beaverhabits.configs import StorageType, settings
from beaverhabits.storage.session_file import SessionDictStorage, SessionStorage
from beaverhabits.storage.storage import UserStorage
from beaverhabits.storage.user_db import UserDatabaseStorage
from beaverhabits.storage.user_file import UserDiskStorage
import logging

session_storage = SessionDictStorage()
user_disk_storage = UserDiskStorage()
user_database_storage = UserDatabaseStorage()
sqlite_storage = None

logger = logging.getLogger(__name__)

def get_sessions_storage() -> SessionStorage:
    return session_storage

async def get_user_storage() -> UserStorage:
    if settings.HABITS_STORAGE == StorageType.USER_DISK:
        return user_disk_storage

    if settings.HABITS_STORAGE == StorageType.USER_DATABASE:
        return user_database_storage

    logger.error("Storage type not implemented: %s", settings.HABITS_STORAGE)
    raise NotImplementedError("Storage type not implemented")
    # if self.STORAGE == StorageType.SQLITE:
    #     return None