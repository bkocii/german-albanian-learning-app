# Media ZIP import format

Create one ZIP with `manifest.json` at its root and media beneath a folder such as `files/`:

```text
media-import.zip
├── manifest.json
└── files/
    ├── greeting-wave.webp
    └── guten-morgen.mp3
```

Copy `course_content/media/manifest-example.json` to the ZIP root as `manifest.json`, then edit the
asset records. Schema version 1 supports `image` and `audio`.

Required for every asset:

- `external_id`: stable slug used by course JSON references
- `filename`: exact case-sensitive path inside the ZIP
- `title`
- `kind`: `image` or `audio`
- `language_code`: empty for images; `de`, `sq`, or empty for audio
- `creator`
- `license_name`
- `acquired_on`: `YYYY-MM-DD`

Images also require Albanian `alt_text_sq`. Source URL, license URL, and attribution text may be
empty for original work but should be completed when an external licensed asset is used.

Supported image files: JPEG, PNG, and WebP. Supported audio files: MP3, M4A, MP4 audio, Ogg, WAV,
and WebM audio.

Default safety limits are 25 MiB per ZIP, 15 MiB per media file, 50 MiB extracted total, and 100
media files. Preview tokens expire after 15 minutes. Unsafe paths, encrypted entries, duplicate
names or IDs, missing files, existing external IDs, and unsupported formats are rejected before
database writes.

Imported assets are always unapproved. A staff member must listen to audio, inspect images,
confirm licensing and attribution, and then add approval metadata in Admin. Course JSON may refer
to imported external IDs, but a listening exercise cannot be published until its German audio is
approved.
