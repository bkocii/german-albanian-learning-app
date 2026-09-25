import re
import tempfile
from collections import Counter
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from django.conf import settings

ALLOWED_AUDIO_TYPES = {
    "audio/mp4": ".m4a",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/webm": ".webm",
    "audio/x-wav": ".wav",
}


class SpeechUploadError(ValueError):
    pass


@contextmanager
def temporary_audio_file(upload):
    content_type = (upload.content_type or "").split(";", maxsplit=1)[0].lower()
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise SpeechUploadError("Unsupported audio format.")
    if upload.size <= 0:
        raise SpeechUploadError("The recording is empty.")
    if upload.size > settings.SPEECH_MAX_UPLOAD_BYTES:
        raise SpeechUploadError("The recording is too large.")

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="speech-",
            suffix=ALLOWED_AUDIO_TYPES[content_type],
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            for chunk in upload.chunks():
                temporary.write(chunk)
        yield temporary_path
    finally:
        if temporary_path:
            temporary_path.unlink(missing_ok=True)


@lru_cache(maxsize=1)
def _whisper_model():
    from faster_whisper import WhisperModel

    return WhisperModel(
        settings.SPEECH_WHISPER_MODEL,
        device=settings.SPEECH_WHISPER_DEVICE,
        compute_type=settings.SPEECH_WHISPER_COMPUTE_TYPE,
    )


def transcribe_german(audio_path):
    segments, _ = _whisper_model().transcribe(
        str(audio_path),
        language="de",
        beam_size=5,
        vad_filter=True,
    )
    return " ".join(segment.text.strip() for segment in segments).strip()


def _words(text):
    return re.findall(r"[^\W_]+(?:['’-][^\W_]+)*", text.casefold())


def compare_recognized_words(expected, recognized):
    expected_words = _words(expected)
    recognized_words = _words(recognized)
    remaining_recognized = Counter(recognized_words)
    matched = []
    missing = []
    for word in expected_words:
        if remaining_recognized[word]:
            matched.append(word)
            remaining_recognized[word] -= 1
        else:
            missing.append(word)

    remaining_expected = Counter(expected_words)
    unexpected = []
    for word in recognized_words:
        if remaining_expected[word]:
            remaining_expected[word] -= 1
        else:
            unexpected.append(word)

    return {
        "expected_words": expected_words,
        "recognized_words": recognized_words,
        "matched_words": matched,
        "missing_words": missing,
        "unexpected_words": unexpected,
        "is_match": expected_words == recognized_words,
    }
