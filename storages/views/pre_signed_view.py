from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from storages.backends.powerscale import PowerScaleS3Storage

storage = PowerScaleS3Storage()


# -------------------------
# Pre-signed URL methods
# -------------------------
class PresignedUpload(APIView):
    """Generate a presigned upload URL."""
    def post(self, request):
        filename = request.data.get("filename")
        if not filename:
            return Response({"error": "Missing filename"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            url = storage.generate_presigned_upload_url(filename)
            return Response({"upload_url": url})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PresignedDownload(APIView):
    """Generate a presigned download URL."""
    def get(self, request):
        filename = request.query_params.get("filename")
        if not filename:
            return Response({"error": "Missing filename"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            url = storage.generate_presigned_download_url(filename)
            return Response({"download_url": url})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PresignedDelete(APIView):
    """Generate a presigned delete URL."""
    def get(self, request):
        filename = request.query_params.get("filename")
        if not filename:
            return Response({"error": "Missing filename"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            url = storage.generate_presigned_delete_url(filename)
            return Response({"delete_url": url})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PresignedPost(APIView):
    """Generate a presigned POST URL."""
    def get(self, request):
        filename = request.query_params.get("filename")
        if not filename:
            return Response({"error": "Missing filename"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            url = storage.generate_presigned_post_url(filename)
            return Response({"post_url": url})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------
# Multipart Upload Support
# -------------------------
class MultipartUploadInit(APIView):
    """Initiate a multipart upload and return the upload ID."""
    def post(self, request):
        key = request.data.get("filename")
        if not key:
            return Response({"error": "Missing filename"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            upload_id = storage.create_multipart_upload(key)
            return Response({"upload_id": upload_id})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MultipartUploadPart(APIView):
    """Generate a presigned URL for a multipart upload part."""
    def post(self, request):
        key = request.data.get("filename")
        upload_id = request.data.get("upload_id")
        part_number = request.data.get("part_number")
        if not key or not upload_id or not part_number:
            return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            url = storage.generate_presigned_part_url(key, upload_id, int(part_number))
            return Response({"url": url})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MultipartUploadComplete(APIView):
    """Complete a multipart upload."""
    def post(self, request):
        key = request.data.get("filename")
        upload_id = request.data.get("upload_id")
        parts = request.data.get("parts")
        if not key or not upload_id or not parts:
            return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = storage.complete_multipart_upload(key, upload_id, parts)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
