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
- Benchmark evidence: pending (maintainer's schema 3 report from the
  controlled Apple Silicon host, on the candidate commit)
- Pre-release Linux CI: pending (the tagged commit's run)
- Pre-release platform qualification: pending (manual dispatch with
  `package_artifacts` on the exact candidate commit)

## Expected benchmark outcome

The release report is compared with
[`benchmark-0.5.0.json`](../bench/release-evidence/benchmark-0.5.0.json),
the accepted 0.5.0 report (`complete` scope):

```sh
sh bench/release.sh benchmark-0.6.0.json \
  bench/release-evidence/benchmark-0.5.0.json
```

Nine of the thirteen result counts must equal the baseline's: the five
analysis rows and the four `lo/gos` rows. The four `i(/hmi` rows change,
because ἵημι returns 2,949 records instead of 2,918 on the historical
index. It gains 62 unaugmented forms and 4 with a movable ν. It loses 17
compound-only forms, which analysis accepts only after a preverb, and
dialect hybrids. The rows become 58,980, 117,960, 235,920 and 29,490
records instead of 58,360, 116,720, 233,440 and 29,180.

Analysis rows should stay within noise. Generation rows are expected to be
slower, as measured above: about twice as long for the maximal lemma, half
as long again for the small one, and about 10–15 ms more for the cold rows.

## Remaining authorization

Before publication, a maintainer must:

1. run `bench/release.sh` on the candidate commit on the controlled host,
   have the report reviewed against the baseline and committed with its
   sidecar as `bench/release-evidence/benchmark-0.6.0.json`;
2. dispatch the platform workflow with `package_artifacts` for the candidate
   commit and inspect the three native archives;
3. confirm the final tagged Linux CI and platform runs and record their links
   above;
4. explicitly authorize creation of `v0.6.0`, then of `wasm-v0.3.0` on the
   same commit or a descendant with an unchanged runtime, and of
   `data-v0.3.0`.
