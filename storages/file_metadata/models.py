from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class StoredFile(models.Model):
    """
    Abstract base model for S3-compatible file metadata.
    To use, inherit this model in your app and add 'storages.file_metadata' to INSTALLED_APPS.
    Supports pre-signed URLs and polymorphic relations.
    """
    key = models.CharField(max_length=500, unique=True)  # object key in storage
    bucket = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True, null=True)
    size = models.BigIntegerField(blank=True, null=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Polymorphic relation: file belongs to any model (User, Employee, etc.)
    content_type_ref = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey("content_type_ref", "object_id")

    # Optional tag/label (e.g. "profile_picture", "id_card")
    tag = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.filename} ({self.key})"

    class Meta:
        abstract = True
