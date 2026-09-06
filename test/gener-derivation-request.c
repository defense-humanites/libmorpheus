/* SPDX-License-Identifier: AGPL-3.0-or-later */
#include <stdio.h>
#include "../src/gener/derivation.h"

int main(int argc, char **argv)
{
    FILE *output;
    int invalid, unmatched, valid, failed;
    if (argc != 2 || !(output = fopen(argv[1], "w"))) return 1;
    invalid = morpheus_gener_expand_derivation(output, "log", "reg_conj", "", "vs,-t");
    unmatched = morpheus_gener_expand_derivation(output, "log", "reg_conj", "", "va,-missing");
    valid = morpheus_gener_expand_derivation(output, "log", "reg_conj", "", "va,-t");
    failed = invalid != -1 || unmatched != 0 || valid != 1;
    if (failed) fprintf(stderr, "derivation results: invalid=%d unmatched=%d valid=%d\n", invalid, unmatched, valid);
    if (fclose(output)) failed = 1;
    remove(argv[1]);
    return failed;
}
