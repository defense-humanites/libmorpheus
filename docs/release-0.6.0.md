<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# libmorpheus 0.6.0

This native release brings experimental generation close to the inverse of
analysis, the contract 0.5.0 defined for it
([public-api.md](public-api.md#greek-lemma-generation)). Generation now
returns compound verbs, the variants and spellings analysis reads, and
dialects that hold for every part of a form. The C ABI stays 2: one
generation flag is added and the default limit changes. Analysis results are
unchanged except one reading. It is the release WebAssembly binding 0.3.0 is
compiled from and declares ([release-wasm-0.3.0.md](release-wasm-0.3.0.md)).

## Why a new version

Issue #78 measured how far generation was from analysis, and issue #100
measured what remained after it. Generation must return every form that
analysis attributes to a lemma, and every form it returns must analyze back
to that lemma. The changes since 0.5.0:

- **Compound verbs** (#92, #93, #95). `morpheus_generate()` accepts the
  compound lemmas analysis reports:
  - the names `stemsrc/vbs.cmp.ml` lists (`a)podi/dwmi`);
  - the hyphenated names analysis gives a preverb and a verb that the list
    does not join (`a)mfi/-lu/w`);
  - outer preverbs before a listed compound (`a)nti/-paradi/dwmi`).

  It composes them at run time from the simple verb's records and the stems
  that occur only in compounds. A compound of one preverb also returns the
  preverb variants analysis accepts, with their flags: apocope (κάββαλε), ἐς,
  ξυν-, the augment before the preverb (ἠφίει), the Ionic unaspirated
  preverb (ἀπίκετο). `MORPHEUS_GENERATION_EXCLUDE_PREVERB_VARIANTS` leaves
  them out. Generated surfaces no longer write the engine's hiatus mark after
  πρό (προέηκε, not `pro+e/hke`).
- **Dialects by intersection** (#97). A form has the dialects that its
  preverb, augment, stem and ending all allow. A form whose parts share none
  is left out (τιμήσωντι), unless its record forces the ending. A
  first-declension ending in -η after ρ, ε or ι is Ionic and epic, no
  longer Attic (χώρην). Analysis shares that check: see below.
- **Unaugmented indicatives** (#98). Analysis reads an imperfect, aorist or
  pluperfect without its augment for every verb, and generation returns these
  forms, flagged `unaugmented`, as Homeric and Ionic (ἄγον, ἀπόλυον).
- **Verbal adjectives** (#99). A verb no longer returns the adjective in -τός
  that its derivation lists. Analysis reads φερτός as a lemma of its own,
  and none of these 17,642 forms analyzed back to the verb.
- **Record keys and movable ν** (#102). Keys joined by a comma are read as
  the analysis index reads them, in any key: χαλκός is suffix-accented,
  υἱός and υἱόν are generated, and a preverb joined by a comma counts.
  Irregular forms take their movable ν as the analysis index gives it
  (ἀνδράσιν).
- **Accented clitics** (#103). Proclitics come accented as the analysis
  index accents them (ὅ, οἵ, εἴς). Enclitics come with the accent their
  record writes, or the acute a following enclitic gives them (ἐστί, τινός),
  and ἐστί(ν) also as ἔστι(ν).
- **Default limit.** `MORPHEUS_GENERATION_DEFAULT_LIMIT`, applied to `NULL`
  options or a zero `result_limit`, becomes the maximum, 65,536 records,
  instead of 4,096: 3,180 listed compounds exceed 4,096 records.

Two defects of the shared engine are fixed. The stem expansion leaked the
buffer of a record's unknown keys when none of its endings applied, and
freed it twice when a stem produced too many forms. The ending check cleared
a stem's flag after the first ending in -η, so that χώρης and χώρῃ kept an
Attic label that χώρη had lost.

The version is a minor one, as for 0.5.0: generation returns different
records for most lemmas, and a new capability and flag are public.

## Results and compatibility

**Analysis.** The 33,410 words of the Alpheios lemma list analyze
identically with the `v0.5.0` library and this release's (45,900 analyses,
same digest). The ending fix changes one reading among the 858,532 words an
independent audit compared (14 November): the plural noun χρῆς, under χρή,
is Ionic and epic instead of Aeolic and Doric, as generation labels it.
#105 removes a slowdown of analysis that #95 had introduced: it now takes
0.1 % more instructions than with 0.5.0 (callgrind, the benchmark fixture).

**Generation**, with `@libmorpheus/data` 0.3.0's index
([release-data-0.3.0.md](release-data-0.3.0.md)), against 0.5.0 with
0.2.0's:

| | 0.5.0 | 0.6.0 |
| --- | ---: | ---: |
| AGDT 2.1: readings analysis gives that generation returns | 82.8 % | 95.2 % |
| AGDT 2.1: verb tokens with every reading generated | 66.6 % | 94.2 % |
| Readings as a simple verb | 91.4 % | 96.2 % |
| Readings as a listed compound | 0.9 % | 93.9 % |
| Readings as a hyphenated compound | 0.0 % | 68.9 % |
| Listed compound names that generate | 317 of 19,289 | 19,130 of 19,289 |

The treebank measure counts each (form, lemma) pair that analysis gives a
noun, adjective, pronoun or verb token, weighted by its tokens. It compares
forms without capitals, with grave accents as acute and without the second
accent of an enclitic. Once the text is normalized as analysis normalizes it
before lookup (second accents and diaeresis), 96.3 % of the readings are
generated. Most of the rest are readings analysis gives without regard to
accent or through compounds it builds; issue #100 records the breakdown.

In the other direction, 99.49 % of the 412,988 surfaces of the 246 most
frequent verbs analyze back to their verb, and 99.93 % of the 664,367 of
300 random listed compounds. The index's 106,080 lemmas generate 23.1
million forms (22.1 million with 0.5.0 and 0.2.0's index). Its 340
unusable records are skipped in 275 lemmas, and 114 lemmas return no form.
The listed compounds generate 56.4 million forms; προσκρεμάννυμι, the
largest, returns 28,200 records.

**ABI.** The C ABI stays **2** and the SONAME **1**. Nothing is removed or
changed in layout. `MORPHEUS_GENERATION_EXCLUDE_PREVERB_VARIANTS` is a new
bit of `morpheus_generation_flags`; earlier libraries reject it as an
unknown flag. The default limit is the library's: a caller that passes
`NULL` options now receives up to 65,536 records, and the macro's value in
the header follows it.

**Indexes.** An index prepared by `@libmorpheus/data` 0.3.0 works with
earlier runtimes, which never reach its reserved keys (`-dhme/w`). With an
earlier index, 0.6.0 generates compounds without their compound-only stems.

**Bindings.** The native archives contain no stemlib data. The Node.js and
Python bindings keep declaring native 0.5.0 until their next releases, which
declare 0.6.0, pin data 0.3.0 and its index, and pass the new flag
(`excludePreverbVariants`, `exclude_preverb_variants`), which 0.5.0
rejects.

## Measured effect

On the 2-vCPU Linux sandbox, against a `v0.5.0` library built with the same
compiler and options (Release), on the historical generation index, with
the two versions alternated twice:

- Analysis takes 208–212 µs per benchmark word, against 202–208 µs:
  unchanged within noise.
- Small warm generation (`lo/gos`) takes 17 µs instead of 11 µs.
- Maximal warm generation (`i(/hmi`) takes 9.9–11.4 ms instead of
  4.5–4.7 ms.
- A first generation in a new context takes about 10–15 ms more, since
  it builds the compound table (29–45 ms instead of 22–31 ms).

The cost is that of the passes the contract requires. The unaugmented
indicatives generate every verb record a second time, and the movable ν,
clitic and dialect passes are added to that. Every new pass can be weighed
against its share of the treebank readings above.

## Release record

- Project version: **0.6.0**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.5.0`
- Benchmark evidence: **accepted**
- Pre-release Linux CI: [passed on `7dcc93a`](https://github.com/defense-humanites/libmorpheus/actions/runs/44138463704)
- Pre-release platform qualification: [passed on `7dcc93a`](https://github.com/defense-humanites/libmorpheus/actions/runs/44138484613)
  (manual dispatch with `package_artifacts`, first attempt)
- Tagged platform run and release publication: [passed on `7dcc93a`](https://github.com/defense-humanites/libmorpheus/actions/runs/44163354021)
  (second attempt)
- Release: [`v0.6.0`](https://github.com/defense-humanites/libmorpheus/releases/tag/v0.6.0),
  created on 2026-11-17 on `7dcc93a18121ff79c3b694afb3b9fc9e4ebf1886`

## Benchmark evidence

The schema 3 report from source revision
`b00ee435eb1ec96b425df74a8aa40a9dc6c4271d` (the merge of the release
preparation) uses the pinned Alpheios stemlib revision
`4632415fe93c85e9fdca47a0c5a13f31385f0023` on the controlled Apple Silicon
host, with the toolchain of the baseline (Apple Clang 21 build 2100.4.1.1,
Node.js 26.13.1, libuv thread pool of four) and the tree's Node.js binding,
0.3.0. It is retained as
[`benchmark-0.6.0.json`](../bench/release-evidence/benchmark-0.6.0.json);
its SHA-256 is
`998060d582bb22340ce5b497f186ddc0dea2f34c6ba0c41bc26ef0f29a7aa05e`. The
release validator passes with the recorded source revision and compiler,
and the comparison with
[`benchmark-0.5.0.json`](../bench/release-evidence/benchmark-0.5.0.json)
has `complete` scope.

Nine of the thirteen result counts equal the baseline's: the five analysis
rows and the four `lo/gos` rows. The four `i(/hmi` rows change as predicted,
because ἵημι returns 2,949 records instead of 2,918 on the historical index:
58,980, 117,960, 235,920 and 29,490 records instead of 58,360, 116,720,
233,440 and 29,180. It gains 62 unaugmented forms and 4 with a movable ν, and
loses 17 compound-only forms, which analysis accepts only after a preverb,
and dialect hybrids.

| Row | 0.5.0 (µs) | 0.6.0 (µs) | Change |
| --- | --- | --- | --- |
| `node`, 1 context | 213 | 214 | +0.3 % |
| `node`, 2 contexts | 131 | 132 | +0.3 % |
| `node`, 4 contexts | 86 | 83 | −3.8 % |
| `cruncher-persistent` | 211 | 201 | −4.4 % |
| `cruncher-cold` | 2,700 | 2,741 | +1.5 % |
| maximal generation, warm, 1 / 2 / 4 contexts | 3,659 / 1,755 / 1,113 | 6,010 / 3,125 / 1,677 | +64.3 / +78.1 / +50.7 % |
| small generation, warm, 1 / 2 / 4 contexts | 35 / 21 / 14 | 42 / 23 / 14 | +19.5 / +12.7 / −2.7 % |
| maximal / small generation, cold | 19,036 / 14,708 | 27,089 / 19,908 | +42.3 / +35.3 % |

Analysis is within noise, as #105 made it; `cruncher-persistent` stays
within the 202–227 µs that the retained reports since 0.4.6 measured.

Generation is slower, as expected, though less than on the sandbox. Through
the Node.js binding, which also decodes each record, these changes appear:
- maximal warm generation takes 51 to 78 % longer, 2.4 ms more at one
  context, against twice as long natively;
- small warm generation moves by −2.7 to +19.5 %, a few microseconds;
- cold generation takes 5 to 8 ms more, for the compound table the first
  request builds.

This is the cost of the passes described above, and it is accepted for this
release.

Between the two reports, the binding's code differs only by the option
that passes the new flag, so the comparison isolates the runtime.

Peak RSS stays within 2 % for analysis. For generation, it rises by 10.7 to
14.0 % with two and four contexts, up to 13 MiB at four, as each context
builds its compound table. With one context it moves by −2.8 to +4.9 %.

RSS growth of the two-context maximal row reaches 13.2 MiB against 2.9 MiB,
which follows the order of allocations within one process. The one-context
row grows less than in 0.5.0 (14.2 against 17.7 MiB).

This report replaces `benchmark-0.5.0.json` as the baseline of the next
native release.

## Publication record

The tag was created by the maintainer on 2026-11-17 on `7dcc93a`, the merge
of the accepted benchmark evidence. That commit descends from the measured
revision `b00ee43` and differs from it only by that evidence and these
documents.

The Linux CI of the merge commit on `main` passed at its first attempt,
including the push-only sanitizer, ThreadSanitizer, byte-conversion,
legacy-make and release jobs. The manual `package_artifacts` dispatch also
passed at its first attempt and produced the three archives.

On the tag, Linux CI and WebAssembly passed at their first attempt. The
platform run's first `apple-silicon` job waited fifteen minutes without a
macOS runner and was cancelled before any step ran, as during the 0.5.0
publication; the other qualification jobs had passed. The second attempt
qualified Apple Silicon and published the release. The tag never moved.

The release carries the three native archives and their digests, plus the
accepted benchmark report and its sidecar:

| Asset | SHA-256 |
|---|---|
| `libmorpheus-0.6.0-Linux-x86_64-glibc.tar.gz` | `c3858a14b00e727be72d1a6163778c9c1f9b7b19e7c9424bcab3a3d6d23479d5` |
| `libmorpheus-0.6.0-Linux-aarch64-glibc.tar.gz` | `a4d0bdbea11dbd4c0bd252baba35f9aa43b795c7bbbdd6d4e0d8195428c2e4f6` |
| `libmorpheus-0.6.0-macOS-arm64.tar.gz` | `a310afa8882fe08c04770e4712c947c3383d29adb5b886fada46cd71c4bf12d0` |
| `benchmark-0.6.0.json` | `998060d582bb22340ce5b497f186ddc0dea2f34c6ba0c41bc26ef0f29a7aa05e` |

After publication, the Linux x86-64 archive was downloaded and checked
against its sidecar. The tree's Node.js binding, declaring 0.6.0, acquired
the same archive with `libmorpheus-native`. Through the Python binding of
the tree, whose 26 tests pass against it, it was exercised over the index of
`@libmorpheus/data` 0.3.0:
- δίδωμι generates 3,317 records (2,212 distinct surfaces), with one record
  skipped;
- καταβάλλω generates 5,825 records, 3,040 with
  `exclude_preverb_variants`;
- τις returns ἄττα and τινός accented.

WebAssembly binding 0.3.0 and data package 0.3.0 were tagged on the same
commit afterwards; see [`release-wasm-0.3.0.md`](release-wasm-0.3.0.md) and
[`release-data-0.3.0.md`](release-data-0.3.0.md).
