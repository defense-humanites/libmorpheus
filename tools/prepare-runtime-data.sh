#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later

set -eu

usage() {
  echo "usage: $0 OUTPUT_DIRECTORY" >&2
  echo "prepare the pinned Alpheios Greek stemlib and gener.index locally" >&2
}

if [ "$#" -ne 1 ]; then
  usage
  exit 2
fi

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source_directory=$(CDPATH= cd -- "$script_directory/.." && pwd)

case "$1" in
  /*) output_directory=$1 ;;
  *) output_directory=$PWD/$1 ;;
esac

if [ "$output_directory" = "/" ] || [ "$output_directory" = "$source_directory" ]; then
  echo "refusing unsafe output directory: $output_directory" >&2
  exit 2
fi
if [ -e "$output_directory" ]; then
  echo "output directory already exists: $output_directory" >&2
  exit 2
fi

output_parent=$(dirname -- "$output_directory")
if [ ! -d "$output_parent" ]; then
  echo "output parent does not exist: $output_parent" >&2
  exit 2
fi

alpheios_directory=$source_directory/vendor/alpheios-morpheus
alpheios_stemlib=$alpheios_directory/dist/stemlib
if [ ! -d "$alpheios_stemlib/Greek" ]; then
  echo "the pinned Alpheios submodule is not initialized" >&2
  echo "run: git -C '$source_directory' submodule update --init --recursive" >&2
  exit 1
fi

if ! command -v cmake >/dev/null 2>&1; then
  echo "cmake is required" >&2
  exit 1
fi
if ! command -v ninja >/dev/null 2>&1; then
  echo "ninja is required" >&2
  exit 1
fi

build_directory=${MORPHEUS_RUNTIME_DATA_BUILD_DIR:-$source_directory/build/runtime-data}
case "$build_directory" in
  /*) ;;
  *) build_directory=$PWD/$build_directory ;;
esac

if [ ! -f "$build_directory/CMakeCache.txt" ]; then
  cmake -S "$source_directory" -B "$build_directory" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
fi
cmake --build "$build_directory" --target \
  morpheus_gener_source_preparer \
  morpheus_gener_index_builder \
  morpheus_gener_index_reader_test

corpus_directory=$build_directory/runtime-data-corpus
MORPHLIB=$source_directory/stemlib cmake \
  -DMORPHEUS_GENER_CORPUS_ROOT="$alpheios_stemlib/Greek" \
  -DMORPHEUS_GENER_CORPUS_MANIFEST="$source_directory/tools/gener-corpus-manifest.tsv" \
  -DMORPHEUS_GENER_CORPUS_EXCEPTIONS="$source_directory/tools/gener-corpus-exceptions.tsv" \
  -DMORPHEUS_GENER_CORPUS_PATCHES="$source_directory/tools/gener-corpus-patches.tsv" \
  -DMORPHEUS_GENER_DATA_MANIFEST="$source_directory/bindings/js/data/internal/gener-manifest.js" \
  -P "$source_directory/test/gener-corpus-manifest.cmake"
MORPHLIB=$source_directory/stemlib cmake \
  -DMORPHEUS_GENER_SOURCE_PREPARER="$build_directory/morpheus_gener_source_preparer" \
  -DMORPHEUS_GENER_INDEX_BUILDER="$build_directory/morpheus_gener_index_builder" \
  -DMORPHEUS_GENER_INDEX_READER_TEST="$build_directory/morpheus_gener_index_reader_test" \
  -DMORPHEUS_GENER_CORPUS_ROOT="$alpheios_stemlib/Greek" \
  -DMORPHEUS_GENER_CORPUS_MANIFEST="$source_directory/tools/gener-corpus-manifest.tsv" \
  -DMORPHEUS_GENER_CORPUS_EXCEPTIONS="$source_directory/tools/gener-corpus-exceptions.tsv" \
  -DMORPHEUS_GENER_CORPUS_PATCHES="$source_directory/tools/gener-corpus-patches.tsv" \
  -DMORPHEUS_GENER_CORPUS_WORK_DIR="$corpus_directory" \
  -P "$source_directory/test/gener-corpus.cmake"

temporary_directory=$output_parent/.morpheus-runtime-data.$$
if [ -e "$temporary_directory" ]; then
  echo "temporary directory already exists: $temporary_directory" >&2
  exit 1
fi
cleanup() {
  if [ -d "$temporary_directory" ]; then
    cmake -E remove_directory "$temporary_directory"
  fi
}
trap cleanup EXIT HUP INT TERM

cmake -E make_directory "$temporary_directory"
cmake -E copy_directory "$alpheios_stemlib/Greek" "$temporary_directory/Greek"
cmake -E copy "$corpus_directory/first.mgi" "$temporary_directory/gener.index"

cat > "$temporary_directory/MORPHEUS-DATA.txt" <<EOF
Prepared locally by libmorpheus tools/prepare-runtime-data.sh.
Source dataset: alpheios-project/morpheus, pinned by this source checkout.
Languages: Ancient Greek analysis and experimental Greek generation.
Generation index SHA-256: 8ba328ca8429c657aeb53a47a92045ac4bd64cdeab726af01e8afbcfd67d8fc2

This directory contains upstream linguistic data and a derived index. Review
the upstream licensing evidence before redistributing it. See:
https://github.com/defense-humanites/libmorpheus/blob/main/docs/provenance.md
EOF

mv "$temporary_directory" "$output_directory"
trap - EXIT HUP INT TERM

echo "prepared runtime data: $output_directory"
cmake -E sha256sum "$output_directory/gener.index"
