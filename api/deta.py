from deta import Deta

from .config import get_settings

settings = get_settings()
deta = Deta(settings.deta_project_key)
