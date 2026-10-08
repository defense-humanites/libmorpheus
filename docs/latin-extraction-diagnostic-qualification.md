<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Qualifications des diagnostics d’extraction latins

Ces résultats agrégés proviennent des qualifications CI de la PR nº 18. Les dossiers individuels restent privés. Ils ne constituent pas une approbation du remplacement du corpus.

## Huit autres blocages d’extraction qualifiés sur `453e6d3`

Le commit [`453e6d3`](https://github.com/defense-humanites/libmorpheus/commit/453e6d3079a1ecd44f2d0a32d509ac4bcc1b3eee) ajoute une revue distincte des huit dossiers verbaux à article unique, sans définition finale et hors des sept chiffres terminaux. Les trois workflows réussissent : [Linux](https://github.com/defense-humanites/libmorpheus/actions/runs/37760589367), [plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37760589357), [recherche](https://github.com/defense-humanites/libmorpheus/actions/runs/37760581357). Le [job latin](https://github.com/defense-humanites/libmorpheus/actions/runs/37760581357/job/113255727396) confirme **69 tests unitaires ciblés et neuf tests natifs**, dont huit nouveaux tests de cette revue.

L’outil reproduit exactement les transcriptions originales après vérification des en-têtes contre la TEI épinglée. Les huit dossiers représentent **914 anciennes lectures entièrement perdues** :

| Structure source | Dossiers | Résultat du rejeu original |
| --- | ---: | --- |
| Plusieurs `itype` | 2 | `combitype` fusionne les occurrences en un champ à parties principales et chiffre terminal ; aucun champ original n’est conservé à l’identique. Ce champ fusionné traverse les trois filtres suivants sans émission. |
| Aucun `itype` | 2 | Aucun champ de conjugaison ni aucune directive ne sont produits. |
| Autre structure de `itype` | 3 | Le champ original est conservé à l’identique dans les quatre sorties, sans émission. Les trois en-têtes ont une morphologie de présent déponent. |
| Graphie infinitive | 1 | Le champ original est conservé à l’identique dans les quatre sorties, sans émission. |

Les huit préfixes d’en-tête sont préservés dans toutes les sorties et les filtres n’écrivent aucun stderr. La conservation d’un champ ne démontre pas que sa grammaire est prise en charge : ces mesures distinguent fusion, absence de champ et champ transmis sans définition.

Pour les deux en-têtes multiples, **cinq essais** gardent chaque occurrence source seule à tour de rôle, tous les autres champs restant intacts. **Deux essais émettent sous le lemme attendu**, chacun une directive `:de:` : l’un conserve un chiffre de conjugaison nu, l’autre un champ classé « autre structure ». Dans les deux cas, `conj1` transforme le champ en graphie infinitive avant l’émission par `latvb`. Les trois autres essais — graphie infinitive, autre structure, parties principales avec chiffre terminal — conservent leur champ sans produire de définition. Aucun essai n’émet seulement un autre lemme.

Ces **deux succès sont des essais de champs, pas un compte de lemmes récupérés**. Ils localisent une piste liée à la combinaison des champs ; ils ne justifient ni la suppression d’une information source ni la promotion d’une dérivation productive. Aucun index correspondant n’est construit et aucune récupération native n’est revendiquée. La prochaine qualification doit rattacher les essais réussis à leurs dossiers, examiner les radicaux émis et leur productivité, puis contrôler les lectures attendues et les différences avant/après sur une copie privée.

Le dossier privé a SHA-256 `64804fe621a6376419636eb2558a4ebce2ad8e408b06b2efa0df415314dcee9c`. Le dossier préalable reste `0cf86ce597e83ff92f0301b06fb34b700a714eaddccd66eb9a195cf0c58decbc` ; les trois empreintes des sondes/revue des sept chiffres terminaux reproduisent `dbba407` et leurs index du candidat final restent inchangés. Aucun candidat ni radical de production n’est modifié ; la PR reste en brouillon. [Critères et limites](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-extraction-blocker-review.md).

## Provenance native et indices d’attestation qualifiés sur `dbba407`

Le commit [`dbba407`](https://github.com/defense-humanites/libmorpheus/commit/dbba4070e3903cfc76e2e4b1b5e80229949ce835) compare, sur chaque cellule source, les onze champs grammaticaux complétés par `preverb`, `raw_preverb`, `stem`, `suffix` et `ending`. Les valeurs textuelles restent privées et sont contrôlées contre la troncature. **Les trois workflows réussissent** : [Linux](https://github.com/defense-humanites/libmorpheus/actions/runs/37757699543), [plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37757699489), [recherche](https://github.com/defense-humanites/libmorpheus/actions/runs/37757691294). Le job latin confirme les **61 tests unitaires ciblés et neuf tests natifs**, dont 104 cellules synthétiques contrôlées avec la décomposition enrichie.

Sur les sept familles et 91 cellules, la comparaison enrichie conserve **87 lectures**, en retire **zéro** et ajoute **110 lectures directes**, dont **91 attendues et 19 autres** ; elle n’ajoute aucune lecture avec préverbe. Les trois signatures auparavant « mixtes » correspondent donc à des **ajouts directs**, la lecture avec préverbe déjà présente étant conservée. Les 19 autres occurrences portent le même lemme littéral que la cellule source : cinq indicatifs présents passifs (2e singulier), six impératifs présents passifs (cinq 2e singulier, un 2e pluriel), huit indicatifs futurs (quatre 1re singulier actifs, un 1re singulier passif, trois 2e singulier passifs). « Autres » signifie non affectées aux 91 lectures directes attendues ; cela ne signifie pas nécessairement une grammaire différente. Cette comparaison distingue les décompositions exposées par l’API, sans identifier tous les chemins internes du parseur.

La revue des sept en-têtes comprend **16 parties déclarées**, dont **15 tokens isolés et une coordination/alternative**. Deux parties se terminent par `re`, aucune par `ri` ; ces terminaisons n’établissent pas leur grammaire. **Aucune correspondance exacte indépendante** n’est trouvée dans les orthographies complètes de leur article ni dans les tokens des éléments `quote`/`foreign` explicitement étiquetés `la` ou `lat`, après la normalisation documentée. Deux tokens d’un même en-tête partagent textuellement le préfixe du composant présent. Ce dernier indice ne qualifie pas une forme complète ; son absence n’invalide pas une alternance de radical. Les résultats négatifs sont limités aux critères et articles contrôlés : ils ne prouvent pas l’absence d’une attestation ailleurs et n’autorisent aucune reconstruction de partie abrégée.

Les contrôles précédents restent identiques : **418 anciennes lectures exactes récupérées, 510 encore manquantes**, 124 autres lectures dans l’essai présent isolé ; la comparaison essai complet → présent conserve 542 occurrences, en retire 99 et n’en ajoute aucune, sans changer les récupérations exactes. Les sources, index des essais et quatre index du candidat final gardent leurs empreintes précédentes. Aucun radical de production n’est modifié ; la PR reste en brouillon.

Empreintes des dossiers privés : revue source `9e3069d518b375724350a2f5b5f083d7023605a252bd05c1220d69cf44533939` ; sondes présent enrichies `0cf33203944e6d277e1cbc5afa3365c3aad127055e74d5b28a2fddb339c1e278` ; sondes de l’essai complet inchangées `2d48ac575e8b0e6a8d708e5e9edea909096153569f8de42e6bcb569fef6f4093`. Seuls outils, tests synthétiques, agrégats et empreintes sont publiés.


