#!/usr/bin/env bash
# Publish a release of the Minna no Nihongo Anki deck.
#
# Usage:
#   scripts/publish.sh v1.0.0
#   scripts/publish.sh v1.0.1 --rebuild
#   scripts/publish.sh v1.0.1 --notes "Fix lesson 3 audio"
#   scripts/publish.sh v1.0.1 --notes-file path/to/notes.md
#   scripts/publish.sh v1.0.1 --dry-run

set -euo pipefail

# ---------- arg parsing ----------
VERSION="${1:-}"
shift || true

REBUILD=0
DRY_RUN=0
NOTES=""
NOTES_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rebuild)     REBUILD=1; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    --notes)       NOTES="$2"; shift 2 ;;
    --notes-file)  NOTES_FILE="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$VERSION" ]]; then
  echo "usage: $0 vMAJOR.MINOR.PATCH [--rebuild] [--notes TEXT | --notes-file FILE] [--dry-run]" >&2
  exit 2
fi

if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
  echo "version must look like v1.2.3 or v1.2.3-rc1, got: $VERSION" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APKG="dist/MinnaNoNihongo_Vocab.apkg"

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY:  $*"
  else
    echo "RUN:  $*"
    eval "$@"
  fi
}

# ---------- preflight ----------
echo "==> Preflight checks"

# clean working tree
if [[ -n "$(git status --porcelain)" ]]; then
  echo "working tree is dirty. commit or stash first." >&2
  git status --short >&2
  exit 1
fi

# tag must not already exist
if git rev-parse "$VERSION" >/dev/null 2>&1; then
  echo "tag $VERSION already exists locally." >&2
  exit 1
fi
if git ls-remote --tags origin "refs/tags/$VERSION" 2>/dev/null | grep -q "$VERSION"; then
  echo "tag $VERSION already exists on origin." >&2
  exit 1
fi

# gh authed
if ! gh auth status >/dev/null 2>&1; then
  echo "gh CLI not authenticated. run: gh auth login" >&2
  exit 1
fi

# release must not already exist
if gh release view "$VERSION" >/dev/null 2>&1; then
  echo "release $VERSION already exists on GitHub." >&2
  exit 1
fi

# pyproject version sanity (warn only)
PYPROJ_VERSION="$(grep -E '^version' pyproject.toml | head -1 | sed -E 's/.*"([^"]+)".*/v\1/')"
if [[ "$PYPROJ_VERSION" != "$VERSION" ]]; then
  echo "warning: pyproject.toml version is $PYPROJ_VERSION, releasing as $VERSION" >&2
fi

echo "    git tree clean"
echo "    tag $VERSION available"
echo "    gh authenticated"

# ---------- build ----------
if [[ $REBUILD -eq 1 ]] || [[ ! -f "$APKG" ]]; then
  echo "==> Building deck"
  run "uv run mnn all"
fi

if [[ ! -f "$APKG" ]]; then
  echo "expected $APKG to exist after build" >&2
  exit 1
fi

APKG_SIZE="$(du -h "$APKG" | cut -f1)"
echo "    deck: $APKG ($APKG_SIZE)"

# ---------- release notes ----------
NOTES_ARG=()
if [[ -n "$NOTES_FILE" ]]; then
  [[ -f "$NOTES_FILE" ]] || { echo "notes file not found: $NOTES_FILE" >&2; exit 1; }
  NOTES_ARG=(--notes-file "$NOTES_FILE")
elif [[ -n "$NOTES" ]]; then
  NOTES_ARG=(--notes "$NOTES")
else
  NOTES_ARG=(--generate-notes)
fi

# ---------- tag + push ----------
echo "==> Tagging $VERSION"
run "git tag -a $VERSION -m \"Release $VERSION\""
run "git push origin $VERSION"

# ---------- gh release ----------
echo "==> Creating GitHub release"
TITLE="$VERSION"
if [[ -n "$NOTES" ]] && [[ ${#NOTES} -lt 60 ]]; then
  TITLE="$VERSION — $NOTES"
fi

if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY:  gh release create $VERSION --title \"$TITLE\" ${NOTES_ARG[*]} $APKG"
else
  gh release create "$VERSION" \
    --title "$TITLE" \
    "${NOTES_ARG[@]}" \
    "$APKG"
fi

echo
echo "==> Done."
echo "    https://github.com/k1ng440/minna-no-nihongo-anki/releases/tag/$VERSION"
