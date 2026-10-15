# Expanded research archive

The original ZIP is 105,119,701 bytes, above GitHub's 100 MiB single-file limit. These four parts preserve its original bytes. No study or archive content was altered.

After cloning the repository, run from its root:

```bash
python scripts/restore_bundles.py
```

The script verifies each part and the complete archive before restoring `outputs/bundles/task-preserving-research-20261015-expanded.zip`. The original SHA-256 is `db6ac2985b1cc595b26df3fc1cc8f0ae27a386299988bbfd5a413daa8e686876`. Use `--out /path/to/archive.zip` to choose another destination. Smaller archives remain intact beside this directory.
