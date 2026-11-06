#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later

set -eu

# Optional overrides:
# MORPHEUS_BENCHMARK_LABEL, MORPHEUS_BENCHMARK_STEMLIB,
# MORPHEUS_BENCHMARK_ITERATIONS, MORPHEUS_BENCHMARK_WARMUP,
# MORPHEUS_BENCHMARK_CONTEXTS, and MORPHEUS_BENCHMARK_COLD_SAMPLES.

usage()
{
  echo "usage: sh bench/release.sh OUTPUT.json [BASELINE.json]" >&2
  exit 2
}

[ "$#" -ge 1 ] && [ "$#" -le 2 ] || usage

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir=$(CDPATH= cd -- "${script_dir}/.." && pwd)
cd "${project_dir}"

output=$1
baseline=${2-}
case "${output}" in
  /*) ;;
  *) output="${project_dir}/${output}" ;;
esac
if [ -n "${baseline}" ]; then
  case "${baseline}" in
    /*) ;;
    *) baseline="${project_dir}/${baseline}" ;;
  esac
fi

[ ! -e "${output}" ] || {
  echo "benchmark output already exists: ${output}" >&2
  exit 1
}
[ -d "$(dirname -- "${output}")" ] || {
  echo "benchmark output directory does not exist: $(dirname -- "${output}")" >&2
  exit 1
}
[ -z "${baseline}" ] || [ -f "${baseline}" ] || {
  echo "benchmark baseline does not exist: ${baseline}" >&2
  exit 1
}

if ! git diff --quiet --ignore-submodules=all -- ||
   ! git diff --cached --quiet --ignore-submodules=all --; then
  echo "tracked project files differ from HEAD" >&2
  exit 1
fi
submodule_status=$(git submodule status -- vendor/alpheios-morpheus)
case "${submodule_status}" in
  " "*) ;;
  *)
    echo "Alpheios submodule is uninitialized or differs from the recorded commit" >&2
    exit 1
    ;;
esac
if ! git -C vendor/alpheios-morpheus diff --quiet -- ||
   ! git -C vendor/alpheios-morpheus diff --cached --quiet --; then
  echo "tracked Alpheios submodule files differ from its recorded commit" >&2
  exit 1
fi

for command in cmake ctest git node; do
  command -v "${command}" >/dev/null 2>&1 || {
    echo "required command is missing: ${command}" >&2
    exit 1
  }
done

build_dir="${project_dir}/build/release"
stemlib=${MORPHEUS_BENCHMARK_STEMLIB:-vendor/alpheios-morpheus/dist/stemlib}
label=${MORPHEUS_BENCHMARK_LABEL:-release-candidate}
iterations=${MORPHEUS_BENCHMARK_ITERATIONS:-20}
warmup=${MORPHEUS_BENCHMARK_WARMUP:-2}
contexts=${MORPHEUS_BENCHMARK_CONTEXTS:-1,2,4}
cold_samples=${MORPHEUS_BENCHMARK_COLD_SAMPLES:-10}

case "${stemlib}" in
  /*) ;;
  *) stemlib="${project_dir}/${stemlib}" ;;
esac

case "$(uname -s)" in
  Darwin) library="${build_dir}/libmorpheus.dylib" ;;
  Linux) library="${build_dir}/libmorpheus.so" ;;
  *)
    echo "release benchmark supports controlled Linux and macOS hosts" >&2
    exit 1
    ;;
esac
cruncher="${build_dir}/cruncher"
addon="${build_dir}/node/libmorpheus_node.node"

revision=$(git rev-parse HEAD)
stemlib_revision=$(git -C vendor/alpheios-morpheus rev-parse HEAD)

cmake --preset release -DBUILD_TESTING=ON -DMORPHEUS_BUILD_NODE_BINDING=ON
cmake --build --preset release
ctest --preset release

[ -f "${addon}" ] || {
  echo "Node-API addon was not built: ${addon}" >&2
  exit 1
}

generation_index="${build_dir}/test-gener-corpus/first.mgi"
[ -f "${generation_index}" ] || {
  echo "qualified generation index was not produced by CTest" >&2
  exit 1
}
generation_stemlib=$(mktemp -d "${TMPDIR:-/tmp}/morpheus-benchmark.XXXXXX")
ln -s "${stemlib}/Greek" "${generation_stemlib}/Greek"
cp "${generation_index}" "${generation_stemlib}/gener.index"
stemlib=${generation_stemlib}

compiler_command=$(sed -n \
  's/^CMAKE_C_COMPILER:[^=]*=//p' "${build_dir}/CMakeCache.txt")
[ -n "${compiler_command}" ] || {
  echo "configured C compiler was not found in CMakeCache.txt" >&2
  exit 1
}
compiler=$("${compiler_command}" --version | sed -n '1p')

temporary="${output}.tmp.$$"
cleanup()
{
  rm -f "${temporary}"
  rm -rf "${generation_stemlib}"
}
trap cleanup 0 HUP INT TERM

if [ -n "${baseline}" ]; then
  set -- --baseline "${baseline}"
else
  set --
fi
MORPHEUS_LIBRARY="${library}" \
MORPHEUS_NODE_ADDON="${addon}" \
MORPHEUS_STEMLIB="${stemlib}" \
MORPHEUS_CRUNCHER="${cruncher}" \
  node bench/compare.mjs --json "$@" \
    --label "${label}" --revision "${revision}" \
    --stemlib-revision "${stemlib_revision}" --compiler "${compiler}" \
    --iterations "${iterations}" --warmup "${warmup}" \
    --contexts "${contexts}" --cold-samples "${cold_samples}" \
    --generation-small "lo/gos" --generation-maximal "i(/hmi" \
    > "${temporary}"

node bench/validate.mjs "${temporary}" \
  --label "${label}" --revision "${revision}" \
  --stemlib-revision "${stemlib_revision}" --compiler "${compiler}"

mv "${temporary}" "${output}"
rm -rf "${generation_stemlib}"
trap - 0 HUP INT TERM
echo "release benchmark written to ${output}"
