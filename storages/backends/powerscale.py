import boto3
from django.conf import settings
from storages.base import BaseStorage
from botocore.exceptions import ClientError


class PowerScaleS3Storage(BaseStorage):
    """
    Dell PowerScale S3 Storage backend with pre-signed URL and multipart upload support.
    """

    # -------------------------
    # Load defaults from Django settings
    # -------------------------
    @classmethod
    def get_default_settings(cls):
        return {
            "bucket_name": getattr(settings, "POWERSCALE_BUCKET_NAME", None),
            "access_key": getattr(settings, "POWERSCALE_ACCESS_KEY_ID", None),
            "secret_key": getattr(settings, "POWERSCALE_SECRET_ACCESS_KEY", None),
            "endpoint_url": getattr(settings, "POWERSCALE_ENDPOINT_URL", None),
            "region_name": getattr(settings, "POWERSCALE_REGION_NAME", None),
        }

    def __init__(self, *args, **kwargs):
        # Merge defaults with any explicit kwargs
        defaults = self.get_default_settings()
        for key, value in defaults.items():
            kwargs.setdefault(key, value)

        bucket_name = kwargs.pop("bucket_name")
        access_key = kwargs.pop("access_key")
        secret_key = kwargs.pop("secret_key")
        endpoint_url = kwargs.pop("endpoint_url")
        region_name = kwargs.pop("region_name")

        # call S3Boto3Storage init (it expects bucket_name)
        super().__init__(bucket_name=bucket_name, *args, **kwargs)

        # override boto3 client with PowerScale config
        self.client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            region_name=region_name,
        )
        self.bucket_name = bucket_name  # Store as instance variable

        
    # -------------------------
    # Pre-signed URL methods
    # -------------------------
    def generate_presigned_upload_url(self, key, expires=3600, content_type="application/octet-stream"):
        """Generate URL to upload a file (PUT). Raises ClientError on failure."""
        try:
            return self.client.generate_presigned_url(
                ClientMethod="put_object",
                Params={"Bucket": self.bucket_name, "Key": key, "ContentType": content_type},
                ExpiresIn=expires,
            )
        except ClientError as e:
            # Log or handle error as needed
            raise e

    def generate_presigned_download_url(self, key, expires=3600):
        """Generate URL to download a file (GET). Raises ClientError on failure."""
        try:
            return self.client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires,
            )
        except ClientError as e:
            raise e

    def generate_presigned_delete_url(self, key, expires=3600):
        """Generate URL to delete a file (DELETE). Raises ClientError on failure."""
        try:
            return self.client.generate_presigned_url(
                ClientMethod="delete_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires,
            )
        except ClientError as e:
            raise e

    def generate_presigned_post_url(self, key, expires=3600, conditions=None, fields=None):
        """
        Generate a presigned POST form (HTML direct upload).
        Good for browsers uploading large files without PUT.
        Raises ClientError on failure.
        """
        try:
            return self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=key,
                Fields=fields or {},
                Conditions=conditions or [],
                ExpiresIn=expires,
            )
        except ClientError as e:
            raise e

    # -------------------------
    # Multipart Upload Support
    # -------------------------

    def create_multipart_upload(self, key, content_type="application/octet-stream"):
        """Start multipart upload and return UploadId. Raises ClientError on failure."""
        try:
            response = self.client.create_multipart_upload(
                Bucket=self.bucket_name,
                Key=key,
                ContentType=content_type,
            )
            return response["UploadId"]
        except ClientError as e:
            raise e

    def generate_presigned_part_url(self, key, upload_id, part_number, expires=3600):
        """Generate presigned URL for uploading a specific part. Raises ClientError on failure."""
        try:
            return self.client.generate_presigned_url(
                ClientMethod="upload_part",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key,
                    "UploadId": upload_id,
                    "PartNumber": part_number,
                },
                ExpiresIn=expires,
            )
        except ClientError as e:
            raise e

    def complete_multipart_upload(self, key, upload_id, parts):
        """
        Complete multipart upload.
        parts should be a list of dicts:
        [{"ETag": "<etag1>", "PartNumber": 1}, {"ETag": "<etag2>", "PartNumber": 2}, ...]
        Raises ClientError on failure.
        """
        try:
            response = self.client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            return response
        except ClientError as e:
            raise e

    def abort_multipart_upload(self, key, upload_id):
        """Abort multipart upload. Raises ClientError on failure."""
        try:
            self.client.abort_multipart_upload(
                Bucket=self.bucket_name,
                Key=key,
                UploadId=upload_id,
            )
            return True
        except ClientError as e:
            raise e

    # -------------------------
    # Extra helpers (not presignable)
    # -------------------------

    def list_files(self, prefix=""):
        """List files using direct API call (not presignable). Raises ClientError on failure."""
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]
        except ClientError as e:
            raise e

    def copy_file(self, source_key, dest_key):
        """Copy file within the bucket using API call. Raises ClientError on failure."""
        try:
            copy_source = {"Bucket": self.bucket_name, "Key": source_key}
            self.client.copy(copy_source, self.bucket_name, dest_key)
            return dest_key
        except ClientError as e:
            raise e