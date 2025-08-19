from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class FileMetadataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'storages.file_metadata'
    verbose_name = _("File Metadata")
