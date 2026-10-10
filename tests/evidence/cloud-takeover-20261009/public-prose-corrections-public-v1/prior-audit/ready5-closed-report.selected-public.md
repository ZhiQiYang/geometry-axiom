# READY5 selected public projection audit

Summary: {"packetCount": 5, "actualTextFileCount": 914, "markdownCount": 5, "actualProjectedFileCount": 58, "boundedPathOnlyMismatchFiles": 7, "confirmedLineFindings": 7, "uniqueOriginalLineDefects": 1, "packetsWithConfirmedDefect": 4, "unresolvedCount": 0, "markdownAllExactOriginal": true, "allOriginalSourcesResolved": true, "result": "confirmed_non_path_only_public_projection", "closedReadOnlyAudit": true, "releaseApproved": false}

All five actual Markdown READMEs match the exact authored originals. The following selected findings show actual public code text changing content outside bounded ASCII private path tokens. They do not disclose original private paths. Original/public raw hashes bind each finding.

## ready5-1

full-102ff-failed-public-v2/source/102ff28ecb005a85b42a8ae9cd7f22fdcf8cf01c/tests/binaries.py:19

Original SHA256 `a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba`; public SHA256 `beb6b6549b92e323ad29a1ccff72c41f4b4a9b698a3380af7a077ca03836fadd`.

Actual public:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory> off Windows),
```
Bounded path-only expected:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory>`` off Windows),
```

## ready5-2

nav-bb7-59-failed-public-v3/executed-source-bytes/a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba/binaries.py:19

Original SHA256 `a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba`; public SHA256 `beb6b6549b92e323ad29a1ccff72c41f4b4a9b698a3380af7a077ca03836fadd`.

Actual public:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory> off Windows),
```
Bounded path-only expected:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory>`` off Windows),
```

## ready5-3

nav-bb7-59-failed-public-v3/source/59c736066a97ca044c3a47c0ecdcb5245a59efab/tests/binaries.py:19

Original SHA256 `a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba`; public SHA256 `beb6b6549b92e323ad29a1ccff72c41f4b4a9b698a3380af7a077ca03836fadd`.

Actual public:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory> off Windows),
```
Bounded path-only expected:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory>`` off Windows),
```

## ready5-4

nav-bb7-59-failed-public-v3/source/bb7e6302d4d909766521840ca564fbe1aaf57a27/tests/binaries.py:19

Original SHA256 `a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba`; public SHA256 `beb6b6549b92e323ad29a1ccff72c41f4b4a9b698a3380af7a077ca03836fadd`.

Actual public:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory> off Windows),
```
Bounded path-only expected:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory>`` off Windows),
```

## ready5-5

9eb-caption-six-public-v2/executed-source-bytes/a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba/binaries.py:19

Original SHA256 `a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba`; public SHA256 `beb6b6549b92e323ad29a1ccff72c41f4b4a9b698a3380af7a077ca03836fadd`.

Actual public:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory> off Windows),
```
Bounded path-only expected:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory>`` off Windows),
```

## ready5-6

9eb-caption-six-public-v2/source/9eb670110379ec0d726914f3e5b2d8e7237f2b9c/tests/binaries.py:19

Original SHA256 `a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba`; public SHA256 `beb6b6549b92e323ad29a1ccff72c41f4b4a9b698a3380af7a077ca03836fadd`.

Actual public:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory> off Windows),
```
Bounded path-only expected:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory>`` off Windows),
```

## ready5-7

9eb-recovered-full-failed-public-v4/source/9eb670110379ec0d726914f3e5b2d8e7237f2b9c/tests/binaries.py:19

Original SHA256 `a211fd0d066b8a5138855c4773373f9f526717f26264de909c0f61f997ac9aba`; public SHA256 `beb6b6549b92e323ad29a1ccff72c41f4b4a9b698a3380af7a077ca03836fadd`.

Actual public:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory> off Windows),
```
Bounded path-only expected:
```
Everything is written under ``%TEMP%\\geometry-tests\\`` (``<isolated-test-directory>`` off Windows),
```
