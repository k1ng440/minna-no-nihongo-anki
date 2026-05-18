# Releasing

Workflow for publishing the Minna no Nihongo vocab deck to GitHub Releases.

## Versioning

Semver. Bump rules tied to Anki review-history impact:

| Bump  | When                                            | Review history |
|-------|-------------------------------------------------|----------------|
| Patch `v1.0.X` | Typo, single card fix, CSS tweak, audio swap | Preserved |
| Minor `v1.X.0` | New lessons, new card types, added fields    | Preserved |
| Major `vX.0.0` | Model ID change, GUID logic change, deck rename | **Lost** |

## Stable IDs — do not break

Anki matches notes across re-imports via:

- **Note GUID** — derived in `src/mnn/deck/models.py` / builder. Never change derivation logic.
- **Model ID** — three constants in `src/mnn/deck/models.py` (Vocab, Quiz, Info). Never change.
- **Deck ID** — derived from deck name. Renaming the deck = new deck = orphaned history.

Safe edits (history preserved):

- Field reorder, field rename
- Template HTML / CSS edits
- Adding new fields (old cards get empty value)
- Adding new notes (appear as new cards)
- Media swap (same filename)

Unsafe edits (force major bump + migration note):

- Removing or re-numbering models
- Changing GUID derivation
- Renaming deck

## Patch workflow

1. Fix the bug in code or data.
2. Rebuild deck:
   ```bash
   mnn all
   ```
   Output: `dist/MinnaNoNihongo_Vocab.apkg`.
3. Smoke test — import the new `.apkg` into a throwaway Anki profile, confirm:
   - Cards count matches expectation
   - Fixed card renders correctly
   - Existing reviewed cards retain scheduling (re-import over old deck)
4. Commit + tag:
   ```bash
   git add -A
   git commit -m "fix: <one-line summary>"
   git tag v1.0.1
   git push && git push --tags
   ```
5. Create release with the `.apkg` attached:
   ```bash
   gh release create v1.0.1 \
     --title "v1.0.1 - <fix summary>" \
     --notes-file RELEASE_NOTES.md \
     ./dist/MinnaNoNihongo_Vocab.apkg
   ```
   Or inline notes:
   ```bash
   gh release create v1.0.1 \
     --title "v1.0.1 - Fix lesson 3 audio" \
     --notes "- Fixed mismatched audio in lesson 3 card 47" \
     ./dist/MinnaNoNihongo_Vocab.apkg
   ```

## End-user upgrade instructions

Paste into release notes:

```
1. Download MinnaNoNihongo_Vocab.apkg from this release
2. In Anki: File -> Import -> select the .apkg
3. Anki updates existing cards in place. Your review history is preserved.
4. New cards added in this release will appear as new.
```

## Major version / breaking release

When forced to bump major:

1. Document the break in `CHANGELOG.md` and release notes.
2. Tell users explicitly: *"This release resets review history. Suspend the old deck or start fresh."*
3. Consider renaming the deck (e.g. `Minna no Nihongo v2`) so the old deck stays parked rather than colliding.

## Cache / data assets

Generated dirs are gitignored. Re-upload as release assets only when their generation logic changes.

Bundle:

```bash
tar --use-compress-program=zstd -cf cache-v1.0.0.tar.zst cache/
tar --use-compress-program=zstd -cf data-v1.0.0.tar.zst data/
```

Attach to release:

```bash
gh release upload v1.0.1 cache-v1.0.0.tar.zst data-v1.0.0.tar.zst
```

If cache logic is unchanged, link the previous release's cache in the new release notes instead of re-uploading.

GitHub asset limits: 2 GB per file, unlimited count, public bandwidth free.

## Pre-release checklist

- [ ] Version bumped in `pyproject.toml`
- [ ] `mnn doctor` passes
- [ ] `mnn all` completes without errors
- [ ] `.apkg` imports clean into a fresh Anki profile
- [ ] Re-import over previous version preserves scheduling on at least one reviewed card
- [ ] Release notes drafted
- [ ] Tag pushed
- [ ] Asset attached to release

## Rollback

Releases are immutable references. To "rollback":

1. Mark the bad release as pre-release or delete the assets:
   ```bash
   gh release edit v1.0.1 --prerelease
   # or
   gh release delete v1.0.1 --cleanup-tag
   ```
2. Cut a new patch (`v1.0.2`) that reverts the bad change. Do not retag.
