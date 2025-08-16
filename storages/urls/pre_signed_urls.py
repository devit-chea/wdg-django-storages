from django.urls import include, path
from rest_framework import routers

from storages.views.pre_signed_view import (
    PresignedUpload,
    PresignedDownload,
    PresignedDelete,
    PresignedPost,
    MultipartUploadInit,
    MultipartUploadPart,
    MultipartUploadComplete,
)

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    # -------------------------
    # Pre-signed URLs
    # -------------------------
    path("presigned/upload/", PresignedUpload.as_view(), name="presigned-upload"),
    path("presigned/download/", PresignedDownload.as_view(), name="presigned-download"),
    path("presigned/delete/", PresignedDelete.as_view(), name="presigned-delete"),
    path("presigned/post/", PresignedPost.as_view(), name="presigned-post"),
    # -------------------------
    # Multipart Upload URLs
    # -------------------------
    path("multipart/init/", MultipartUploadInit.as_view(), name="multipart-init"),
    path("multipart/part/", MultipartUploadPart.as_view(), name="multipart-part"),
    path(
        "multipart/complete/",
        MultipartUploadComplete.as_view(),
        name="multipart-complete",
    ),
    path("", include(router.urls)),
]
