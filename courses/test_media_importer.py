import io
import json
import tempfile
import zipfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .media_importer import import_media_archive, validate_media_archive
from .models import MediaAsset


def manifest_data():
    return {
        "schema_version": 1,
        "assets": [
            {
                "external_id": "a1-greeting-wave",
                "filename": "files/greeting-wave.webp",
                "title": "Greeting wave",
                "kind": "image",
                "language_code": "",
                "alt_text_sq": "Një person duke përshëndetur me dorë.",
                "creator": "Course team",
                "source_url": "",
                "license_name": "Original work",
                "license_url": "",
                "attribution_text": "",
                "acquired_on": "2026-09-30",
            },
            {
                "external_id": "a1-guten-morgen-audio",
                "filename": "files/guten-morgen.mp3",
                "title": "Guten Morgen audio",
                "kind": "audio",
                "language_code": "de",
                "alt_text_sq": "",
                "creator": "Course team",
                "source_url": "",
                "license_name": "Original work",
                "license_url": "",
                "attribution_text": "",
                "acquired_on": "2026-09-30",
            },
        ],
    }


def archive_bytes(manifest=None, extra_files=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest or manifest_data(), ensure_ascii=False),
        )
        archive.writestr("files/greeting-wave.webp", b"small-image")
        archive.writestr("files/guten-morgen.mp3", b"small-audio")
        for name, content in extra_files or []:
            archive.writestr(name, content)
    return output.getvalue()


class MediaImporterServiceTests(TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.temp_directory.name)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        self.temp_directory.cleanup()

    def write_archive(self, content=None):
        path = Path(self.temp_directory.name) / "media.zip"
        path.write_bytes(content or archive_bytes())
        return path

    def test_valid_archive_previews_and_imports_unapproved_assets(self):
        path = self.write_archive()

        validation = validate_media_archive(path)
        self.assertTrue(validation.is_valid, validation.errors)
        self.assertEqual(validation.summary["assets"], 2)
        self.assertEqual(validation.summary["images"], 1)
        self.assertEqual(validation.summary["audio"], 1)
        self.assertFalse(MediaAsset.objects.exists())

        summary = import_media_archive(path)
        self.assertEqual(summary, {"assets": 2})
        self.assertEqual(MediaAsset.objects.count(), 2)
        self.assertFalse(MediaAsset.objects.filter(is_approved=True).exists())
        audio = MediaAsset.objects.get(external_id="a1-guten-morgen-audio")
        self.assertEqual(audio.language_code, MediaAsset.Language.GERMAN)

    def test_archive_rejects_unsafe_paths(self):
        path = self.write_archive(archive_bytes(extra_files=[("../escape.jpg", b"bad")]))

        validation = validate_media_archive(path)

        self.assertFalse(validation.is_valid)
        self.assertTrue(any("unsafe file path" in error for error in validation.errors))

    def test_manifest_requires_image_alt_text_and_existing_file(self):
        manifest = manifest_data()
        manifest["assets"][0]["alt_text_sq"] = ""
        manifest["assets"][1]["filename"] = "files/missing.mp3"
        path = self.write_archive(archive_bytes(manifest))

        validation = validate_media_archive(path)

        self.assertFalse(validation.is_valid)
        self.assertTrue(any("alt_text_sq" in error for error in validation.errors))
        self.assertTrue(any("file is missing" in error for error in validation.errors))


class MediaImporterAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser(
            email="media-admin@example.com", password="secure-test-password"
        )
        cls.learner = get_user_model().objects.create_user(
            email="media-learner@example.com", password="secure-test-password"
        )

    def setUp(self):
        cache.clear()
        self.temp_directory = tempfile.TemporaryDirectory()
        self.override = override_settings(
            MEDIA_ROOT=Path(self.temp_directory.name) / "media",
            MEDIA_IMPORT_PREVIEW_ROOT=Path(self.temp_directory.name) / "previews",
        )
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        self.temp_directory.cleanup()

    def test_import_page_requires_staff(self):
        self.client.force_login(self.learner)
        response = self.client.get(reverse("admin:courses_mediaasset_import_zip"))
        self.assertEqual(response.status_code, 302)

    def test_preview_writes_nothing_and_confirmation_imports(self):
        self.client.force_login(self.staff)
        upload = SimpleUploadedFile(
            "media.zip", archive_bytes(), content_type="application/zip"
        )
        preview = self.client.post(
            reverse("admin:courses_mediaasset_import_zip"),
            {"action": "preview", "media_archive": upload},
        )
        self.assertEqual(preview.status_code, 200)
        self.assertContains(preview, "The archive is valid")
        self.assertFalse(MediaAsset.objects.exists())
        token = preview.context["confirm_form"].initial["preview_token"]

        confirmation = self.client.post(
            reverse("admin:courses_mediaasset_import_zip"),
            {"action": "import", "preview_token": token},
            follow=True,
        )
        self.assertContains(confirmation, "Imported 2 unapproved media asset")
        self.assertEqual(MediaAsset.objects.count(), 2)
        self.assertFalse(MediaAsset.objects.filter(is_approved=True).exists())
