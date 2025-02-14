from beaverhabits.configs import StorageType, settings
from beaverhabits.storage.session_file import SessionDictStorage, KEY_NAME as SESSION_KEY_NAME
from beaverhabits.storage.storage import UserStorage
from beaverhabits.storage.user_db import UserDatabaseStorage
from beaverhabits.storage.user_file import UserDiskStorage, KEY_NAME as USER_KEY_NAME

session_storage = SessionDictStorage()
user_disk_storage = UserDiskStorage()
user_database_storage = UserDatabaseStorage()
sqlite_storage = None


def get_sessions_storage() -> SessionDictStorage:
    return session_storage


def get_user_storage() -> UserStorage:
    if settings.HABITS_STORAGE == StorageType.USER_DISK:
        return user_disk_storage
    elif settings.HABITS_STORAGE == StorageType.USER_DATABASE:
        return user_database_storage
    else:
        raise NotImplementedError("Storage type not implemented")