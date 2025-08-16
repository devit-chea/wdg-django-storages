from rest_framework.response import Response
from collections.abc import Mapping, Sequence
from storages.backends.powerscale import PowerScaleS3Storage

storage = PowerScaleS3Storage()


class FileURLResponseMixin:
    """
    DRF view mixin to automatically inject presigned file URLs
    into the response for all declared file_fields.
    Works recursively for nested serializers.

    Usage:
        In your serializer's Meta, declare:
        file_fields = {
            "profile_picture": "single",
            "documents": "many",
            "nested_field": {"serializer": NestedSerializer, "many": True}
        }
    """

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if hasattr(response, "data") and response.data is not None:
            response.data = self._inject_files_recursive(
                response.data, getattr(self.get_serializer(), "Meta", None)
            )

        return response

    def _inject_files_recursive(self, data, meta):
        """
        Recursively traverse response data and inject presigned URLs.
        """
        if data is None:
            return None

        # If paginated results
        if isinstance(data, Mapping) and "results" in data:
            data["results"] = [
                self._inject_files_recursive(item, meta) for item in data["results"]
            ]
            return data

        # List of objects
        if isinstance(data, Sequence) and not isinstance(data, str):
            return [self._inject_files_recursive(item, meta) for item in data]

        # Single object
        if isinstance(data, Mapping) and meta and hasattr(meta, "file_fields"):
            file_fields = getattr(meta, "file_fields", {})

            for field_name, mode in file_fields.items():
                if field_name not in data:
                    continue

                # Nested serializer
                if isinstance(mode, dict) and "serializer" in mode:
                    nested_serializer_meta = getattr(
                        mode["serializer"].Meta, "file_fields", None
                    )
                    if nested_serializer_meta:
                        if mode.get("many", False) and isinstance(
                            data[field_name], list
                        ):
                            data[field_name] = [
                                self._inject_files_recursive(
                                    item, mode["serializer"].Meta
                                )
                                for item in data[field_name]
                            ]
                        elif not mode.get("many", False) and isinstance(
                            data[field_name], dict
                        ):
                            data[field_name] = self._inject_files_recursive(
                                data[field_name], mode["serializer"].Meta
                            )
                else:
                    # Single / many file fields
                    many = mode == "many"
                    # if many, data[field_name] is expected list of StoredFile dicts
                    if many and isinstance(data[field_name], list):
                        data[field_name] = [
                            self._inject_presigned_url(f) for f in data[field_name]
                        ]
                    elif not many and isinstance(data[field_name], dict):
                        data[field_name] = self._inject_presigned_url(data[field_name])

            return data
        return data

    def _inject_presigned_url(self, file_dict: dict) -> dict:
        """
        Inject presigned URL into file dict if it contains 'key'.
        Handles storage errors gracefully.
        """
        key = file_dict.get("key")
        if key:
            try:
                file_dict["url"] = storage.generate_presigned_download_url(key)
            except Exception:
                file_dict["url"] = None
        return file_dict
