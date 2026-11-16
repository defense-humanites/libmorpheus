/* SPDX-License-Identifier: MPL-2.0 */

#ifndef MORPHEUS_GENERATION_SERVICE_H
#define MORPHEUS_GENERATION_SERVICE_H

#include <stddef.h>

#include <gkstring.h>

#include "../api/gener_index.h"

typedef struct morpheus_generation_service morpheus_generation_service;

typedef enum {
	MORPHEUS_GENERATION_OK = 0,
	MORPHEUS_GENERATION_INVALID = 1,
	MORPHEUS_GENERATION_NOT_FOUND = 2,
	MORPHEUS_GENERATION_NO_MEMORY = 3,
	MORPHEUS_GENERATION_ENGINE_ERROR = 4,
	MORPHEUS_GENERATION_STOPPED = 5
} morpheus_generation_status;

/* The form is borrowed and remains valid only for the duration of the call. */
typedef int (*morpheus_generation_visitor)(const gk_word *form, void *state);

morpheus_generation_status morpheus_generation_service_create(
    const morpheus_gener_index *index, morpheus_generation_service **service);
morpheus_generation_status morpheus_generation_service_create_at_path(
    const morpheus_gener_index *index, const char *stemlib_path,
    morpheus_generation_service **service);
void morpheus_generation_service_destroy(morpheus_generation_service *service);

/*
 * With skipped_records NULL, the first record the engine cannot generate fails
 * the request with MORPHEUS_GENERATION_ENGINE_ERROR. Otherwise such records
 * are skipped, none of their forms reach the visitor, and their number is
 * stored in *skipped_records.
 */
morpheus_generation_status morpheus_generation_service_generate(
    morpheus_generation_service *service, const char *canonical_lemma,
    morpheus_generation_visitor visitor, void *state, size_t *form_count,
    size_t *skipped_records);

/*
 * The dialects of a generated form: those its preverb, augment, stem, ending
 * and request all allow, the ones that name no dialect aside; 0 when none
 * names one. Returns 0 when they name dialects with nothing in common
 * (a)erth/swnti: an Attic-Ionic stem in -h- with a Doric ending). Generation
 * leaves such forms out, unless their record forces the ending; analysis
 * accepts them with the union of the dialects (checkgenwds.c).
 */
int morpheus_generation_form_dialect(const gk_word *form, unsigned *dialect);

/* Leaves out the preverb variants of a compound (apocope, psilosis...). */
#define MORPHEUS_GENERATION_SERVICE_NO_PREVERB_VARIANTS 1u
/* Leaves out the unaugmented indicatives (Homeric and Ionic a)/gon). */
#define MORPHEUS_GENERATION_SERVICE_NO_UNAUGMENTED 2u

/* As above, with MORPHEUS_GENERATION_SERVICE_* flags. */
morpheus_generation_status morpheus_generation_service_generate_flags(
    morpheus_generation_service *service, const char *canonical_lemma,
    unsigned flags, morpheus_generation_visitor visitor, void *state,
    size_t *form_count, size_t *skipped_records);

#endif
