// SPDX-License-Identifier: AGPL-3.0-or-later

export const MORPHEUS_NATIVE_VERSION = "0.4.5";
export const MORPHEUS_NATIVE_ABI_VERSION = 2;
export const MORPHEUS_NATIVE_SCHEMA_VERSION = 2;
export const MORPHEUS_NATIVE_REPOSITORY =
  "https://github.com/defense-humanites/libmorpheus";

const targets = [
  {
    platform: "linux", arch: "x64", name: "linux-x86_64-glibc",
    asset: `libmorpheus-${MORPHEUS_NATIVE_VERSION}-Linux-x86_64-glibc.tar.gz`,
    archiveRoot: `libmorpheus-${MORPHEUS_NATIVE_VERSION}-Linux-x86_64-glibc/`,
    libraryPath: "lib/libmorpheus.so",
  },
  {
    platform: "linux", arch: "arm64", name: "linux-aarch64-glibc",
    asset: `libmorpheus-${MORPHEUS_NATIVE_VERSION}-Linux-aarch64-glibc.tar.gz`,
    archiveRoot: `libmorpheus-${MORPHEUS_NATIVE_VERSION}-Linux-aarch64-glibc/`,
    libraryPath: "lib/libmorpheus.so",
  },
  {
    platform: "darwin", arch: "arm64", name: "macos-arm64",
    asset: `libmorpheus-${MORPHEUS_NATIVE_VERSION}-macOS-arm64.tar.gz`,
    archiveRoot: `libmorpheus-${MORPHEUS_NATIVE_VERSION}-macOS-arm64/`,
    libraryPath: "lib/libmorpheus.dylib",
  },
];

export function selectMorpheusNativeTarget(platform, arch, glibcVersion) {
  if (platform === "linux" && glibcVersion === undefined) {
    throw new TypeError("the libmorpheus native runtime requires glibc on Linux");
  }
  const target = targets.find((candidate) =>
    candidate.platform === platform && candidate.arch === arch
  );
  if (target === undefined) {
    throw new TypeError(`unsupported native platform: ${platform}/${arch}`);
  }
  return target;
}
