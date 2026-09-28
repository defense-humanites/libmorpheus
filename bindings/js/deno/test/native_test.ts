// SPDX-License-Identifier: AGPL-3.0-or-later

import { join } from "node:path";
import { sha256 } from "../internal/data_internal.ts";
import {
  acquireMorpheusNativeWithDependencies,
  type NativeAcquisitionDependencies,
} from "../internal/native_internal.ts";
import {
  MORPHEUS_NATIVE_ABI_VERSION,
  MORPHEUS_NATIVE_VERSION,
  parseMorpheusNativeArgs,
} from "../native.ts";
import { selectMorpheusNativeTarget } from "../internal/native_manifest.ts";
import { MORPHEUS_DENO_VERSION } from "../internal/version.ts";

const encoder = new TextEncoder();
const decoder = new TextDecoder();

function assert(
  condition: unknown,
  message = "assertion failed",
): asserts condition {
  if (!condition) throw new Error(message);
}

async function assertRejects(
  callback: () => Promise<unknown>,
  pattern: RegExp,
): Promise<void> {
  try {
    await callback();
  } catch (error) {
    assert(error instanceof Error);
    assert(pattern.test(error.message), `unexpected error: ${error.message}`);
    return;
  }
  throw new Error("expected promise to reject");
}

function putOctal(
  target: Uint8Array,
  offset: number,
  length: number,
  value: number,
): void {
  const text = value.toString(8).padStart(length - 1, "0");
  target.set(encoder.encode(`${text}\0`), offset);
}

function tarEntry(
  path: string,
  content = new Uint8Array(),
  type = "0",
  linkPath = "",
): Uint8Array {
  const header = new Uint8Array(512);
  header.set(encoder.encode(path), 0);
  putOctal(header, 100, 8, type === "5" ? 0o755 : 0o644);
  putOctal(header, 108, 8, 0);
  putOctal(header, 116, 8, 0);
  putOctal(header, 124, 12, content.length);
  putOctal(header, 136, 12, 0);
  header.fill(0x20, 148, 156);
  header[156] = type.charCodeAt(0);
  header.set(encoder.encode(linkPath), 157);
  header.set(encoder.encode("ustar\0"), 257);
  header.set(encoder.encode("00"), 263);
  let checksum = 0;
  for (const byte of header) checksum += byte;
  header.set(
    encoder.encode(`${checksum.toString(8).padStart(6, "0")}\0 `),
    148,
  );
  const result = new Uint8Array(512 + Math.ceil(content.length / 512) * 512);
  result.set(header);
  result.set(content, 512);
  return result;
}

function tarArchive(entries: Uint8Array[]): Uint8Array {
  const result = new Uint8Array(
    entries.reduce((total, entry) => total + entry.length, 1024),
  );
  let offset = 0;
  for (const entry of entries) {
    result.set(entry, offset);
    offset += entry.length;
  }
  return result;
}

async function gzip(bytes: Uint8Array): Promise<Uint8Array> {
  return new Uint8Array(
    await new Response(
      new Blob([Uint8Array.from(bytes).buffer]).stream().pipeThrough(
        new CompressionStream("gzip"),
      ),
    ).arrayBuffer(),
  );
}

async function fixture(
  extraEntries: Uint8Array[] = [],
  libraryEntries?: Uint8Array[],
): Promise<{ compressed: Uint8Array; asset: string }> {
  const target = selectMorpheusNativeTarget("linux", "x86_64");
  const root = target.archiveRoot;
  const compressed = await gzip(tarArchive([
    tarEntry(root, new Uint8Array(), "5"),
    tarEntry(`${root}lib/`, new Uint8Array(), "5"),
    ...(libraryEntries ?? [
      tarEntry(`${root}${target.libraryPath}`, encoder.encode("ELF fixture")),
    ]),
    ...extraEntries,
  ]));
  return { compressed, asset: target.asset };
}

function dependencies(
  compressed: Uint8Array,
  asset: string,
  checksum?: string,
): Promise<NativeAcquisitionDependencies> {
  return sha256(compressed).then((digest) => ({
    os: "linux",
    arch: "x86_64",
    fetch: ((url: string | URL | Request) => {
      const href = String(url);
      if (href.endsWith(".sha256")) {
        return Promise.resolve(
          new Response(`${checksum ?? digest}  ${asset}\n`),
        );
      }
      return Promise.resolve(
        new Response(Uint8Array.from(compressed).buffer),
      );
    }) as typeof fetch,
  }));
}

Deno.test("native CLI and target selection reject ambiguous input", () => {
  const parsed = parseMorpheusNativeArgs(["--output=runtime"]);
  assert(parsed.output === "runtime" && !parsed.help);
  try {
    selectMorpheusNativeTarget("windows", "x86_64");
  } catch (error) {
    assert(error instanceof TypeError && /unsupported/.test(error.message));
    return;
  }
  throw new Error("unsupported target was accepted");
});

Deno.test("native acquisition verifies, extracts, and records the release", async () => {
  const parent = await Deno.makeTempDir();
  const output = join(parent, "native");
  try {
    const archive = await fixture();
    const receipt = await acquireMorpheusNativeWithDependencies(
      { output },
      await dependencies(archive.compressed, archive.asset),
    );
    assert(receipt.schema === 2);
    assert(receipt.packageVersion === MORPHEUS_DENO_VERSION);
    assert(receipt.nativeVersion === MORPHEUS_NATIVE_VERSION);
    assert(receipt.abiVersion === MORPHEUS_NATIVE_ABI_VERSION);
    assert(
      receipt.sourceUrl.includes(
        `/releases/download/v${MORPHEUS_NATIVE_VERSION}/`,
      ),
    );
    assert(receipt.target === "linux-x86_64-glibc");
    assert(
      decoder.decode(await Deno.readFile(join(output, receipt.libraryPath))) ===
        "ELF fixture",
    );
    const stored = JSON.parse(
      await Deno.readTextFile(join(output, "MORPHEUS-NATIVE.json")),
    );
    assert(stored.archiveSha256 === receipt.archiveSha256);
  } finally {
    await Deno.remove(parent, { recursive: true });
  }
});

Deno.test(
  "native extraction materializes versioned library links",
  async () => {
    const parent = join(Deno.cwd(), "build", "deno-scoped-native");
    const output = join(parent, "native");
    await Deno.remove(parent, { recursive: true }).catch((error) => {
      if (!(error instanceof Deno.errors.NotFound)) throw error;
    });
    await Deno.mkdir(parent, { recursive: true });
    try {
      const target = selectMorpheusNativeTarget("linux", "x86_64");
      const root = target.archiveRoot;
      const archive = await fixture([], [
        tarEntry(
          `${root}lib/libmorpheus.so.1`,
          new Uint8Array(),
          "2",
          `libmorpheus.so.${MORPHEUS_NATIVE_VERSION}`,
        ),
        tarEntry(
          `${root}lib/libmorpheus.so.${MORPHEUS_NATIVE_VERSION}`,
          encoder.encode("versioned ELF fixture"),
        ),
        tarEntry(
          `${root}${target.libraryPath}`,
          new Uint8Array(),
          "2",
          "libmorpheus.so.1",
        ),
      ]);
      const receipt = await acquireMorpheusNativeWithDependencies(
        { output },
        await dependencies(archive.compressed, archive.asset),
      );
      for (const path of [
        receipt.libraryPath,
        "lib/libmorpheus.so.1",
        `lib/libmorpheus.so.${MORPHEUS_NATIVE_VERSION}`,
      ]) {
        const installed = join(output, path);
        assert(
          !(await Deno.lstat(installed)).isSymlink,
          `${path} is a symlink`,
        );
        assert(
          decoder.decode(await Deno.readFile(installed)) ===
            "versioned ELF fixture",
          `${path} has unexpected content`,
        );
      }
    } finally {
      await Deno.remove(parent, { recursive: true });
    }
  },
);

Deno.test("native extraction rejects symbolic link cycles", async () => {
  const parent = await Deno.makeTempDir();
  try {
    const target = selectMorpheusNativeTarget("linux", "x86_64");
    const root = target.archiveRoot;
    const archive = await fixture([], [
      tarEntry(
        `${root}${target.libraryPath}`,
        new Uint8Array(),
        "2",
        "libmorpheus.so.1",
      ),
      tarEntry(
        `${root}lib/libmorpheus.so.1`,
        new Uint8Array(),
        "2",
        "libmorpheus.so",
      ),
    ]);
    const digest = await sha256(archive.compressed);
    await assertRejects(
      () =>
        acquireMorpheusNativeWithDependencies(
          { output: join(parent, "native") },
          awaitableDependencies(
            archive.compressed,
            archive.asset,
            digest,
          ),
        ),
      /symbolic link cycle/,
    );
  } finally {
    await Deno.remove(parent, { recursive: true });
  }
});

Deno.test("native acquisition removes partial output after checksum failure", async () => {
  const parent = await Deno.makeTempDir();
  const output = join(parent, "native");
  try {
    const archive = await fixture();
    await assertRejects(
      () =>
        acquireMorpheusNativeWithDependencies(
          { output },
          awaitableDependencies(
            archive.compressed,
            archive.asset,
            "0".repeat(64),
          ),
        ),
      /checksum mismatch/,
    );
    await assertRejects(() => Deno.lstat(output), /No such file|not found/i);
    const leftovers = [];
    for await (const entry of Deno.readDir(parent)) leftovers.push(entry.name);
    assert(leftovers.length === 0);
  } finally {
    await Deno.remove(parent, { recursive: true });
  }
});

Deno.test("native acquisition rejects release redirects to untrusted hosts", async () => {
  const parent = await Deno.makeTempDir();
  try {
    const archive = await fixture();
    const digest = await sha256(archive.compressed);
    const fetcher = ((url: string | URL | Request) => {
      if (String(url).endsWith(".sha256")) {
        return Promise.resolve(
          new Response(`${digest}  ${archive.asset}\n`),
        );
      }
      return Promise.resolve(
        new Response(null, {
          status: 302,
          headers: { location: "https://example.invalid/native.tar.gz" },
        }),
      );
    }) as typeof fetch;
    await assertRejects(
      () =>
        acquireMorpheusNativeWithDependencies(
          { output: join(parent, "native") },
          { os: "linux", arch: "x86_64", fetch: fetcher },
        ),
      /unsafe redirect/,
    );
  } finally {
    await Deno.remove(parent, { recursive: true });
  }
});

function awaitableDependencies(
  compressed: Uint8Array,
  asset: string,
  checksum: string,
): NativeAcquisitionDependencies {
  return {
    os: "linux",
    arch: "x86_64",
    fetch: ((url: string | URL | Request) => {
      const body = String(url).endsWith(".sha256")
        ? `${checksum}  ${asset}\n`
        : Uint8Array.from(compressed).buffer;
      return Promise.resolve(new Response(body));
    }) as typeof fetch,
  };
}

Deno.test("native extraction rejects traversal, escaping links, and duplicates", async () => {
  const target = selectMorpheusNativeTarget("linux", "x86_64");
  const cases = [
    tarEntry(`${target.archiveRoot}../escape`, encoder.encode("bad")),
    tarEntry(
      `${target.archiveRoot}lib/escape`,
      new Uint8Array(),
      "2",
      "../../escape",
    ),
    tarEntry(
      `${target.archiveRoot}${target.libraryPath}`,
      encoder.encode("duplicate"),
    ),
  ];
  for (const malicious of cases) {
    const parent = await Deno.makeTempDir();
    try {
      const archive = await fixture([malicious]);
      const digest = await sha256(archive.compressed);
      await assertRejects(
        () =>
          acquireMorpheusNativeWithDependencies(
            { output: join(parent, "native") },
            awaitableDependencies(
              archive.compressed,
              archive.asset,
              digest,
            ),
          ),
        /unsafe|escapes|duplicate/,
      );
    } finally {
      await Deno.remove(parent, { recursive: true });
    }
  }
});

Deno.test("native acquisition refuses an existing output directory", async () => {
  const output = await Deno.makeTempDir();
  try {
    const archive = await fixture();
    await assertRejects(
      () =>
        acquireMorpheusNativeWithDependencies(
          { output },
          awaitableDependencies(
            archive.compressed,
            archive.asset,
            "0".repeat(64),
          ),
        ),
      /already exists/,
    );
  } finally {
    await Deno.remove(output, { recursive: true });
  }
});
