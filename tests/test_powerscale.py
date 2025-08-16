import datetime
import gzip
import io
import os
import pickle
import threading
from textwrap import dedent
from unittest import mock
from unittest import skipIf
from urllib.parse import urlparse

import boto3
import boto3.s3.transfer
import botocore
from botocore.config import Config as ClientConfig
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.base import File
from django.test import TestCase
from django.test import override_settings
from django.utils.timezone import is_aware
from moto import mock_aws

from storages.backends import s3
from tests.utils import NonSeekableContentFile


class S3PowerscaleStorageTests(TestCase):
    def setUp(self):
        self.storage = s3.S3Storage()
        self.storage._connections.connection = mock.MagicMock()
        self.storage._unsigned_connections.connection = mock.MagicMock()

    @mock.patch("boto3.Session")
    def test_s3_session(self, session):
        with override_settings(AWS_S3_SESSION_PROFILE="test_profile"):
            storage = s3.S3Storage()
            _ = storage.connection
            session.assert_called_once_with(profile_name="test_profile")
            
            
    def test_pickle_with_bucket(self):
        """
        Test that the storage can be pickled with a bucket attached
        """
        # Ensure the bucket has been used
        self.storage.bucket
        self.assertIsNotNone(self.storage._bucket)

        # Can't pickle MagicMock, but you can't pickle a real Bucket object either
        p = pickle.dumps(self.storage)
        new_storage = pickle.loads(p)

        self.assertIsInstance(new_storage._connections, threading.local)
        # Put the mock connection back in
        new_storage._connections.connection = mock.MagicMock()

        self.assertIsNone(new_storage._bucket)
        new_storage.bucket
        self.assertIsNotNone(new_storage._bucket)

    def test_pickle_without_bucket(self):
        """
        Test that the storage can be pickled, without a bucket instance
        """

        # Can't pickle a threadlocal
        p = pickle.dumps(self.storage)
        new_storage = pickle.loads(p)

        self.assertIsInstance(new_storage._connections, threading.local)