#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Create the missing GitHub releases of published Node.js and Python binding
# tags, from the maintainer's machine:
#
#   sh tools/backfill-binding-releases.sh [TAG...]
#
# Without arguments, every node-v* and python-v* tag that has notes in
# docs/release-notes/ and no GitHub release yet. Each release carries the files
# the registry serves (the four npm tarballs, or the wheel and the source
# distribution), checked against the registry's digests by
# tools/registry-release-assets.py, with SHA256SUMS; its title is the tag and
# its body the notes. It never becomes the repository's latest release.
#
# A workflow token cannot create a release on a tag whose workflow files
# differ from main's (GitHub requires the `workflows` permission), which is why
# this runs locally with `gh`, authenticated with the `workflow` scope
# (`gh auth refresh -s workflow`). Requires Python 3.9+ and a clean checkout of
# main; run it from the repository root.

set -eu

repository="${MORPHEUS_REPOSITORY:-defense-humanites/libmorpheus}"
test -f tools/registry-release-assets.py || {
  echo "run from the repository root" >&2
  exit 1
}
command -v gh > /dev/null || {
  echo "gh is required" >&2
  exit 1
}

if [ "$#" -eq 0 ]; then
  set -- $(ls docs/release-notes | grep -E '^(node|python)-v[0-9]+\.[0-9]+\.[0-9]+\.md$' | sed 's/\.md$//')
fi

staging="$(mktemp -d)"
trap 'rm -rf "$staging"' EXIT
created=0
for tag in "$@"; do
  case "$tag" in
    node-v*) registry=npm; version="${tag#node-v}" ;;
    python-v*) registry=pypi; version="${tag#python-v}" ;;
    *) echo "$tag: not a Node.js or Python binding tag" >&2; exit 1 ;;
  esac
  notes="docs/release-notes/$tag.md"
  test -f "$notes" || { echo "$tag: no $notes" >&2; exit 1; }
  git rev-parse --verify --quiet "refs/tags/$tag" > /dev/null || {
    echo "$tag: tag not fetched (git fetch --tags)" >&2
    exit 1
  }
  if gh release view "$tag" --repo "$repository" > /dev/null 2>&1; then
    echo "$tag: release exists, skipped"
    continue
  fi
  python3 -I tools/registry-release-assets.py "$registry" "$version" \
    "$staging/$tag" > /dev/null
  gh release create "$tag" --repo "$repository" --verify-tag \
    --title "$tag" --notes-file "$notes" --latest=false \
    "$staging/$tag"/*
  created=$((created + 1))
done
echo "$created release(s) created"
