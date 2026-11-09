# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from libmorpheus import (
    GenerationOptions,
    Language,
    Library,
    MorpheusError,
    Number,
    Option,
    PartOfSpeech,
    Status,
    TruncatedField,
    has_morph_flag,
)


class BindingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        repository = Path(__file__).resolve().parents[3]
        Path(tempfile.gettempdir()).mkdir(parents=True, exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(
            prefix="libmorpheus-python-test-"
        )
        cls.library_path = Path(cls.temporary.name) / "libmorpheus-fixture.so"
        subprocess.run(
            [
                os.environ.get("CC", "cc"),
                "-std=c17",
                "-shared",
                "-fPIC",
                "-Wall",
                "-Wextra",
                "-Werror",
                f"-I{repository / 'include'}",
                str(Path(__file__).with_name("fixture.c")),
                "-o",
                str(cls.library_path),
            ],
            check=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_preserves_multiple_analyses_nulls_masks_and_dual(self) -> None:
        with Library(self.library_path) as library:
            with library.context("fixture-stemlib", Language.GREEK) as context:
                raw = context.analyze_raw("bi/ou", Option.STRICT_CASE)
                analyses = context.analyze("bi/ou", Option.STRICT_CASE)

        self.assertEqual(len(raw), 2)
        self.assertEqual(len(analyses), 2)
        self.assertIsNone(analyses[0].person)
        self.assertEqual(analyses[0].dialects, ("epic",))
        self.assertEqual(analyses[1].dialects, ("attic", "ionic"))
        self.assertEqual(analyses[1].grammatical_number, "dual")
        self.assertEqual(analyses[1].genders, ("feminine", "masculine"))
        self.assertEqual(
            analyses[1].grammatical_cases,
            ("accusative", "nominative"),
        )
        self.assertEqual(analyses[1].truncated_fields, ("lemma",))
        self.assertTrue(has_morph_flag(raw, 36))
        self.assertTrue(has_morph_flag(analyses, "rare"))
        self.assertFalse(has_morph_flag(analyses, "enclitic"))
        self.assertEqual(raw[1].truncated_fields, int(TruncatedField.LEMMA))

    def test_preserves_multiple_generations_masks_and_duals(self) -> None:
        with Library(self.library_path) as library:
            with library.context("fixture-stemlib", Language.GREEK) as context:
                raw = context.generate_raw("lo/gos")
                generations = context.generate("lo/gos")
                duals = context.generate(
                    "lo/gos", GenerationOptions(number=Number.DUAL)
                )
                singulars = context.generate(
                    "lo/gos", GenerationOptions(exclude_duals=True)
                )

        self.assertEqual(len(raw), 3)
        self.assertEqual(len(generations), 3)
        self.assertEqual(len(duals), 2)
        self.assertEqual(len(singulars), 1)
        self.assertEqual(generations[0].grammatical_number, "singular")
        self.assertEqual(generations[1].grammatical_number, "dual")
        self.assertEqual(generations[1].dialects, ("attic", "ionic"))
        self.assertEqual(generations[1].genders, ("feminine", "masculine"))
        self.assertEqual(
            generations[1].grammatical_cases,
            ("accusative", "nominative"),
        )
        self.assertEqual(generations[1].surface, generations[2].surface)
        self.assertNotEqual(
            generations[1].grammatical_cases,
            generations[2].grammatical_cases,
        )
        self.assertTrue(has_morph_flag(raw, "rare"))
        self.assertTrue(has_morph_flag(generations, "rare"))
        self.assertEqual(generations[2].truncated_fields, ("surface",))
        self.assertEqual(
            raw[2].truncated_fields,
            int(TruncatedField.WORKWORD),
        )

    def test_generation_filters_limits_and_empty_results(self) -> None:
        with Library(self.library_path) as library:
            with library.context("fixture-stemlib", Language.GREEK) as context:
                self.assertEqual(context.generate("missing"), ())
                self.assertEqual(
                    context.generate(
                        "lo/gos",
                        GenerationOptions(part_of_speech=PartOfSpeech.VERB),
                    ),
                    (),
                )
                with self.assertRaises(MorpheusError) as caught:
                    context.generate(
                        "lo/gos", GenerationOptions(result_limit=1)
                    )
        self.assertEqual(caught.exception.status, Status.RESULT_LIMIT_EXCEEDED)

    def test_reports_native_status_and_enforces_lifetimes(self) -> None:
        library = Library(self.library_path)
        context = library.context("fixture-stemlib", Language.LATIN)
        with self.assertRaisesRegex(RuntimeError, "Close all Morpheus contexts"):
            library.close()
        with self.assertRaises(MorpheusError) as caught:
            context.analyze("error")
        self.assertEqual(caught.exception.status, Status.INPUT_TOO_LONG)
        context.close()
        context.close()
        with self.assertRaisesRegex(RuntimeError, "context is closed"):
            context.analyze("bi/ou", Option.STRICT_CASE)
        library.close()
        library.close()
        with self.assertRaisesRegex(RuntimeError, "library is closed"):
            library.context("fixture-stemlib", Language.GREEK)

    def test_names_the_stemlib_and_language_a_context_fails_to_open(self) -> None:
        with Library(self.library_path) as library:
            with self.assertRaises(MorpheusError) as caught:
                library.context("missing-stemlib", Language.LATIN)
        self.assertEqual(caught.exception.status, Status.STEMLIB_ERROR)
        self.assertEqual(
            str(caught.exception),
            "opening missing-stemlib for Latin failed: "
            "stemlib is unavailable or incomplete",
        )

    def test_validates_python_inputs_before_native_calls(self) -> None:
        with Library(self.library_path) as library:
            with self.assertRaisesRegex(ValueError, "NUL byte"):
                library.context("fixture\0stemlib", Language.GREEK)
            with library.context("fixture-stemlib", Language.GREEK) as context:
                with self.assertRaisesRegex(ValueError, "NUL byte"):
                    context.analyze("bi\0ou")
                with self.assertRaisesRegex(ValueError, "exceed uint64"):
                    context.analyze("bi/ou", Option(1 << 64))
                with self.assertRaisesRegex(ValueError, "NUL byte"):
                    context.generate("lo\0gos")
                for value in (-1, True, 65_537):
                    with self.subTest(result_limit=value):
                        with self.assertRaisesRegex(ValueError, "result_limit"):
                            context.generate(
                                "lo/gos", GenerationOptions(result_limit=value)
                            )


if __name__ == "__main__":
    unittest.main()
