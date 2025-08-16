from rest_framework import serializers
from storages.backends.powerscale import PowerScaleS3Storage
from .models import StoredFile

storage = PowerScaleS3Storage()


class FileURLMixin(serializers.ModelSerializer):
    """
    Adds presigned file URLs + metadata for declared file fields.
    Supports both flat models and nested serializers.

    Example:
        class Meta:
            file_fields = {
                "profile_picture": "single",
                "documents": "many",
                "dependents": {
                    "serializer": DependentSerializer,
                    "many": True
                }
            }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        file_fields = getattr(self.Meta, "file_fields", {})
        for field_name, mode in file_fields.items():
            if isinstance(mode, dict) and "serializer" in mode:
                # Nested serializer
                nested_serializer = mode["serializer"]
                many = mode.get("many", False)
                self.fields[field_name] = nested_serializer(many=many, context=self.context)
            else:
                # File field
                self.fields[field_name] = serializers.SerializerMethodField()

    def get_file_data(self, file: StoredFile) -> dict | None:
        if not file:
            return None
        try:
            url = storage.generate_presigned_download_url(file.key)
        except Exception:
            url = None
        return {
            "url": url,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size,
            "uploaded_at": file.created_at,
            "tag": file.tag,
        }

    def get_file_field(self, obj, field_name: str, many: bool = False) -> list | dict | None:
        files = getattr(obj, field_name, None)
        if not files:
            return [] if many else None

        if many:
            file_list = files.all() if hasattr(files, "all") else list(files)
            return [
                self.get_file_data(f.file if hasattr(f, "file") else f)
                for f in file_list
            ]
        else:
            file = files.file if hasattr(files, "file") else files
            return self.get_file_data(file)

    def __getattr__(self, name):
        """
        Dynamically resolve SerializerMethodField for file fields.
        Example: get_profile_picture, get_documents.
        """
        if name.startswith("get_"):
            field_name = name.replace("get_", "", 1)
            file_fields = getattr(self.Meta, "file_fields", {})
            if field_name in file_fields and not isinstance(file_fields[field_name], dict):
                mode = file_fields[field_name]
                many = mode == "many"
                return lambda obj: self.get_file_field(obj, field_name, many=many)
        return super().__getattr__(name)
