import json
import zipfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import PurePosixPath

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

from .models import MediaAsset

IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".png", ".webp"}
AUDIO_EXTENSIONS = {".m4a", ".mp3", ".mp4", ".ogg", ".wav", ".webm"}


@dataclass
class MediaImportValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict[str, int] = field(
        default_factory=lambda: {"assets": 0, "images": 0, "audio": 0, "total_bytes": 0}
    )
    manifest: dict | None = None

    @property
    def is_valid(self):
        return not self.errors


class MediaImportError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("Media import validation failed.")


def _safe_archive_name(name):
    path = PurePosixPath(name.replace("\\", "/"))
    return bool(name) and not path.is_absolute() and ".." not in path.parts


def _required_text(item, field_name, path, result):
    value = item.get(field_name)
    if not isinstance(value, str) or not value.strip():
        result.errors.append(f"{path}.{field_name}: a non-empty string is required.")
        return ""
    return value.strip()


def _optional_text(item, field_name, path, result):
    value = item.get(field_name, "")
    if not isinstance(value, str):
        result.errors.append(f"{path}.{field_name}: must be a string.")
        return ""
    return value.strip()


def validate_media_archive(archive_path):
    result = MediaImportValidationResult()
    try:
        archive = zipfile.ZipFile(archive_path)
    except (OSError, zipfile.BadZipFile):
        result.errors.append("Upload a valid ZIP archive.")
        return result

    with archive:
        members = [member for member in archive.infolist() if not member.is_dir()]
        names = [member.filename for member in members]
        unsafe_names = [name for name in names if not _safe_archive_name(name)]
        if unsafe_names:
            result.errors.append("The archive contains an unsafe file path.")
        if len(names) != len(set(names)):
            result.errors.append("The archive contains duplicate filenames.")
        if "manifest.json" not in names:
            result.errors.append("manifest.json is required at the ZIP root.")
            return result
        if any(member.flag_bits & 0x1 for member in members):
            result.errors.append("Encrypted ZIP entries are not supported.")

        total_bytes = sum(
            member.file_size for member in members if member.filename != "manifest.json"
        )
        result.summary["total_bytes"] = total_bytes
        if total_bytes > settings.MEDIA_IMPORT_MAX_TOTAL_BYTES:
            result.errors.append("The extracted media files exceed the total size limit.")
        if len(members) - 1 > settings.MEDIA_IMPORT_MAX_FILES:
            result.errors.append("The archive contains too many media files.")
        oversized = [
            member.filename
            for member in members
            if member.filename != "manifest.json"
            and member.file_size > settings.MEDIA_IMPORT_MAX_FILE_BYTES
        ]
        if oversized:
            result.errors.append(f"Media file exceeds the per-file limit: {oversized[0]}.")

        try:
            manifest_info = archive.getinfo("manifest.json")
            if manifest_info.file_size > 1024 * 1024:
                result.errors.append("manifest.json is larger than 1 MiB.")
                return result
            manifest = json.loads(archive.read("manifest.json").decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            result.errors.append("manifest.json must contain valid UTF-8 JSON.")
            return result

        result.manifest = manifest
        if not isinstance(manifest, dict):
            result.errors.append("The manifest root must be an object.")
            return result
        if manifest.get("schema_version") != 1:
            result.errors.append("schema_version must be 1.")
        assets = manifest.get("assets")
        if not isinstance(assets, list) or not assets:
            result.errors.append("assets: a non-empty list is required.")
            return result
        result.summary["assets"] = len(assets)

        external_ids = []
        filenames = []
        archive_names = set(names)
        for index, item in enumerate(assets, start=1):
            path = f"assets[{index}]"
            if not isinstance(item, dict):
                result.errors.append(f"{path}: must be an object.")
                continue
            external_id = _required_text(item, "external_id", path, result)
            filename = _required_text(item, "filename", path, result)
            _required_text(item, "title", path, result)
            kind = _required_text(item, "kind", path, result)
            language_code = _optional_text(item, "language_code", path, result)
            _optional_text(item, "alt_text_sq", path, result)
            _required_text(item, "creator", path, result)
            _optional_text(item, "source_url", path, result)
            _required_text(item, "license_name", path, result)
            _optional_text(item, "license_url", path, result)
            _optional_text(item, "attribution_text", path, result)
            acquired_on = _required_text(item, "acquired_on", path, result)
            external_ids.append(external_id)
            filenames.append(filename)

            if external_id and MediaAsset.objects.filter(external_id=external_id).exists():
                result.errors.append(f"{path}.external_id: already exists.")
            if filename and (not _safe_archive_name(filename) or filename == "manifest.json"):
                result.errors.append(f"{path}.filename: unsafe archive path.")
            elif filename and filename not in archive_names:
                result.errors.append(f"{path}.filename: file is missing from the archive.")
            extension = PurePosixPath(filename).suffix.lower()
            if kind == MediaAsset.Kind.IMAGE:
                result.summary["images"] += 1
                if extension not in IMAGE_EXTENSIONS:
                    result.errors.append(f"{path}.filename: unsupported image format.")
                if language_code:
                    result.errors.append(f"{path}.language_code: images cannot have a language.")
                if not str(item.get("alt_text_sq", "")).strip():
                    result.errors.append(f"{path}.alt_text_sq: required for images.")
            elif kind == MediaAsset.Kind.AUDIO:
                result.summary["audio"] += 1
                if extension not in AUDIO_EXTENSIONS:
                    result.errors.append(f"{path}.filename: unsupported audio format.")
                if language_code not in MediaAsset.Language.values:
                    result.errors.append(f"{path}.language_code: use de, sq, or an empty string.")
            elif kind:
                result.errors.append(f"{path}.kind: use image or audio.")
            try:
                date.fromisoformat(acquired_on)
            except ValueError:
                result.errors.append(f"{path}.acquired_on: use YYYY-MM-DD.")

        if len(external_ids) != len(set(external_ids)):
            result.errors.append("assets: duplicate external_id values are not allowed.")
        if len(filenames) != len(set(filenames)):
            result.errors.append("assets: each filename may be referenced only once.")
        referenced = set(filenames)
        unreferenced = sorted(set(names) - referenced - {"manifest.json"})
        if unreferenced:
            result.warnings.append(
                "Unreferenced files will be ignored: " + ", ".join(unreferenced[:5])
            )
        result.warnings.append("Imported media remains unapproved until staff review.")
    return result


@transaction.atomic
def import_media_archive(archive_path):
    validation = validate_media_archive(archive_path)
    if not validation.is_valid:
        raise MediaImportError(validation.errors)

    created = []
    with zipfile.ZipFile(archive_path) as archive:
        try:
            for item in validation.manifest["assets"]:
                content = ContentFile(
                    archive.read(item["filename"]),
                    name=PurePosixPath(item["filename"]).name,
                )
                asset = MediaAsset(
                    external_id=item["external_id"],
                    title=item["title"],
                    kind=item["kind"],
                    language_code=item.get("language_code", ""),
                    file=content,
                    alt_text_sq=item.get("alt_text_sq", ""),
                    creator=item["creator"],
                    source_url=item.get("source_url", ""),
                    license_name=item["license_name"],
                    license_url=item.get("license_url", ""),
                    attribution_text=item.get("attribution_text", ""),
                    acquired_on=date.fromisoformat(item["acquired_on"]),
                )
                asset.full_clean()
                asset.save()
                created.append(asset)
        except Exception:
            for asset in created:
                asset.file.delete(save=False)
            raise
    return {"assets": len(created)}
