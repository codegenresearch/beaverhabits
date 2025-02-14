import logging
from typing import Optional

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


def get_user_storage() -> UserStorage:
    if settings.HABITS_STORAGE == StorageType.USER_DISK:
        return user_disk_storage
    elif settings.HABITS_STORAGE == StorageType.USER_DATABASE:
        return user_database_storage
    else:
        logging.error("Storage type not implemented")
        raise NotImplementedError("Storage type not implemented")