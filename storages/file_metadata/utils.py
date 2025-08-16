from storages.backends.powerscale import PowerScaleS3Storage
from .models import StoredFile
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

storage = PowerScaleS3Storage()


class FileMetadataSaver:
    """
    Utility to save single or multiple file metadata records.
    Usage:
        saver = FileMetadataSaver(owner_type="user", owner_id=1, uploaded_by=user)
        saver.save_files([
            {"key": "...", "filename": "...", "content_type": "...", "size": ..., "tag": "..."},
            ...
        ])
    """

    def __init__(self, owner_type, owner_id, uploaded_by=None):
        self.owner_type = owner_type
        self.owner_id = owner_id
        self.uploaded_by = uploaded_by
        self.owner_ct = ContentType.objects.get(model=owner_type.lower())

    def validate_file_data(self, file_data: dict):
        """
        Validate required fields and uniqueness of key.
        Raises ValidationError if invalid.
        """
        required = ["key", "filename"]
        for field in required:
            if not file_data.get(field):
                raise ValidationError(f"Missing required field: {field}")

        # Check for duplicate key
        if StoredFile.objects.filter(key=file_data["key"]).exists():
            raise ValidationError(f"File with key '{file_data['key']}' already exists.")

    def save_file(self, file_data: dict) -> StoredFile:
        """
        Save a single file metadata record.
        file_data keys: key, filename, content_type, size, tag
        """
        self.validate_file_data(file_data)
        return StoredFile.objects.create(
            key=file_data.get("key"),
            bucket=storage.bucket_name,
            filename=file_data.get("filename"),
            content_type=file_data.get("content_type"),
            size=file_data.get("size"),
            uploaded_by=self.uploaded_by,
            content_type_ref=self.owner_ct,
            object_id=self.owner_id,
            tag=file_data.get("tag"),
        )

    def save_files(self, files_data: list) -> list:
        """
        Save multiple file metadata records.
        files_data: list of dicts as in save_file
        Returns list of StoredFile instances.
        """
        saved = []
        errors = []
        for file_data in files_data:
            try:
                saved.append(self.save_file(file_data))
            except ValidationError as e:
                errors.append({"file_data": file_data, "error": str(e)})
        if errors:
            # Optionally, raise or return errors
            raise ValidationError(errors)
        return saved

    def update_file(self, file_instance: StoredFile, file_data: dict) -> StoredFile:
        """
        Update an existing StoredFile instance with new metadata.
        """
        for field in ["key", "filename", "content_type", "size", "tag"]:
            if field in file_data:
                setattr(file_instance, field, file_data[field])
        file_instance.save()
        return file_instance

    def update_files(self, files_instances: list, files_data: list) -> list:
        """
        Update multiple StoredFile instances.
        files_instances: list of StoredFile objects
        files_data: list of dicts
        """
        updated = []
        for instance, data in zip(files_instances, files_data):
            updated.append(self.update_file(instance, data))
        return updated
