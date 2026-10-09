<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Résultats historiques de qualification latine — PR 18

Les sections ci-dessous sont conservées intégralement depuis la description de la PR au commit `b4cd55d`. Chaque section décrit sa révision, son protocole, ses empreintes et ses limites ; les mesures d’étapes différentes ne doivent pas être additionnées. Les diagnostics récents de présent isolé, de préverbes et de portabilité sont consignés séparément. Aucun résultat archivé ne constitue une promotion du corpus.

## Revue des parties source et lectures supplémentaires qualifiée sur `5e25943`

Les trois workflows de [`5e25943`](https://github.com/defense-humanites/libmorpheus/commit/5e25943407939186f1de50014fef28544d47432e) sont verts : [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37753905888), [plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37753905882) et [recherche lexicale](https://github.com/defense-humanites/libmorpheus/actions/runs/37753900212). Le [job latin](https://github.com/defense-humanites/libmorpheus/actions/runs/37753900212/job/113233591226) valide **58 tests unitaires ciblés et neuf tests natifs**, également passants localement sur macOS. Les assemblages et mesures qualifiés précédemment restent reproduits : 91 cellules de présent couvertes, 418 signatures anciennes exactement retrouvées, 510 toujours manquantes, 542 lectures conservées entre les deux copies, 99 retirées et aucune ajoutée.

### Syntaxe originale des parties déclarées

Le champ `itype` original, sans simplification, est conservé avec l’en-tête validé et ses parties littérales dans un dossier privé. Le classement publié est syntaxique : il ne reconstruit aucun suffixe ou radical passé et n’affirme pas qu’un token constitue une partie principale complète.

| Chiffre source / morphologie de l’en-tête | Structure du champ avant le chiffre terminal | Dossiers |
| --- | --- | ---: |
| 1 / active | Deux tokens isolés, terminaisons `i` puis `um`, avec marques de quantité | 1 |
| 3 / active | Deux tokens isolés, terminaisons `i` puis `um`, avec marques de quantité | 2 |
| 3 / passive | Un token isolé terminé en `us` | 1 |
| 4 / active | Trois parties : token en `i`, partie coordonnée/alternative terminée en `i`, token en `um` | 1 |
| 1 / active | Trois tokens isolés : terminaisons `i`, `um`, puis autre terminaison | 1 |
| 3 / active | Trois tokens isolés : autre terminaison, `i`, puis `um` | 1 |
| **Total** | | **7** |

Les sept champs ne relèvent donc pas tous d’une simple paire de parties. Même les trois paires de tokens isolés doivent encore être rapprochées de leur base et du contexte source avant toute restitution de parfait ou de quatrième partie. Une terminaison en `i`, `um` ou `us` ne suffit pas à autoriser la concaténation d’un fragment.

### Les 19 autres occurrences ajoutées sur les cellules de présent

Le partage des 110 ajouts est désormais mesuré explicitement : **91 signatures conformes aux cellules attendues et 19 autres**. Toutes ces 19 occurrences concernent **le même lemme source que la cellule attendue**. « Autres » désigne les occurrences non affectées aux 91 lectures directes attendues ; cela ne prouve pas que chaque occurrence possède une grammaire différente, notamment lorsqu’une signature apparaît par plusieurs routes.

| Grammaire API des autres occurrences sur les 91 cellules | Occurrences |
| --- | ---: |
| Présent de l’indicatif passif, deuxième personne du singulier | 5 |
| Présent de l’impératif passif, deuxième personne, singulier/pluriel | 6 |
| Futur de l’indicatif, première/deuxième personne, actif/passif | 8 |
| **Total** | **19** |

**16 occurrences** ont une signature présente uniquement par voie directe dans le résultat après l’essai. **Trois** ont une signature apparaissant à la fois par voie directe et avec préverbe natif : la comparaison à onze champs ne distingue pas ces routes et ne permet pas d’attribuer précisément l’occurrence ajoutée à l’une d’elles. Ces profils précisent les analyses supplémentaires ; ils ne prouvent pas leur attestation individuelle dans l’article.

### Les 124 autres lectures des formes complètement perdues

Sur les 591 formes ciblées, les **124 lectures hors du multiset ancien attendu** sont toutes des lectures verbales directes, rattachées à **l’un des sept lemmes source**. Aucun profil de ce groupe ne présente de préverbe natif, de provenance mixte ou de lemme extérieur aux sept. Cela ne signifie pas qu’une autre lecture d’une forme appartient nécessairement au lemme de sa lecture ancienne perdue.

| Grammaire API des lectures supplémentaires | Occurrences |
| --- | ---: |
| Mode `GERUNDIVE` / adjectif verbal, sans temps API | 33 |
| Participe présent | 14 |
| Infinitif présent | 4 |
| Indicatif présent | 13 |
| Subjonctif présent | 13 |
| Indicatif imparfait | 13 |
| Subjonctif imparfait | 13 |
| Indicatif futur | 13 |
| Impératif présent | 4 |
| Impératif futur | 4 |
| **Total** | **124** |

Il n’y a aucun parfait, plus-que-parfait ou futur antérieur dans ces 124 lectures. « Présent seul » reste une restriction de classe de radical : celui-ci produit aussi imparfait, futur et formes non finies. Les comptes des 91 cellules et des 591 formes portent sur des inventaires différents et ne doivent pas être additionnés.

### Empreintes et suite

Le dossier privé de parties source a SHA-256 `30026f5fdb8ef5993cb00b9d85ec2c672e930d6a52fcf7fd1edc5fe3903bd168`. Les probes enrichis des lectures supplémentaires ont SHA-256 `62d69a4e0e5cfbe6cda7deb15cd8327c7d920ab018a0d273288472b0772f72af`. Le premier dossier contrefactuel reste `2d48ac575e8b0e6a8d708e5e9edea909096153569f8de42e6bcb569fef6f4093` ; les sources et index privés des deux copies reproduisent les empreintes déjà qualifiées. Les quatre index du candidat final restent inchangés.

La prochaine étape doit établir, avec le contexte source, quelles parties sont des formes complètes et lesquelles sont des fragments, puis qualifier séparément leurs transformations éventuelles. Les trois signatures à provenance mixte demandent une comparaison distinguant les routes si leur attribution devient nécessaire. Les 510 anciennes signatures toujours manquantes et les autres pertes globales restent ouvertes. Aucun radical nouveau n’est ajouté au candidat final. Seuls outils, tests synthétiques, agrégats et empreintes sont publiés ; la PR reste en brouillon et la production inchangée.

## Familles source et comparaison directe qualifiées sur `21f3542`

Les trois workflows de [`21f3542`](https://github.com/defense-humanites/libmorpheus/commit/21f35429a33472a9b4daa9ff837ef6b295b9c0d0) sont verts : [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37750493630), [plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37750493678) et [recherche lexicale](https://github.com/defense-humanites/libmorpheus/actions/runs/37750488007). Le [job latin](https://github.com/defense-humanites/libmorpheus/actions/runs/37750488007/job/113222213913) valide **55 tests unitaires ciblés et neuf tests natifs**, ainsi que le rejeu global et les contrôles des sept dossiers. Les tests locaux macOS passent également, dont 104 cellules synthétiques couvrant les profils actifs et déponents pris en charge.

### Identité des trois directives précédemment non classées

Le profil du runner distingue **deux directives `:de:` de classe `are_vb` et une de classe `ire_vb`**, en plus des sept directives `:vs:` de présent. Ce sont des dérivations productives, pas trois radicaux explicites de parfait. Les sept présents se répartissent en deux `conj1`, trois `conj3`, un `conj3_io` et un `conj4`. Le rapport public ne contient que les préfixes et noms grammaticaux fixes, aucun radical ni champ lexical libre. Le code natif conserve les directives de dérivation dans l’index ; leur absence de classement comme radical explicite de parfait ne permettait donc pas de conclure à l’absence de génération extrapolée.

### Comparaison directe des deux copies privées

La comparaison porte sur les **mêmes 591 formes** et sur les signatures à onze champs avec multiplicité. Les multisets de la copie limitée aux radicaux de présent sont inclus dans ceux de la copie avec dérivations. L’identité des récupérations exactes est désormais vérifiée directement, indépendamment de l’égalité de leurs totaux.

| Copie avec dérivations → copie limitée au présent | Résultat |
| --- | ---: |
| Lectures conservées | 542 |
| Lectures retirées | 99 |
| Lectures ajoutées | 0 |
| Formes dont le multiset change | 54 |
| Formes cessant d’être reconnues | 50 |
| Formes nouvellement reconnues | 0 |
| Anciennes signatures cibles retrouvées puis perdues | 0 |
| Anciennes signatures cibles nouvellement retrouvées | 0 |

Les **418 récupérations exactes** sont identiques dans les deux copies ; **510 signatures anciennes restent manquantes**. La copie limitée au présent reconnaît 370 des 591 formes et fournit 124 autres lectures. Les 50 reconnaissances supprimées provenaient uniquement de lectures hors du multiset cible ; leur suppression ne résout pas les 510 anciennes signatures manquantes.

| Temps API des 99 lectures supprimées entre copies | Occurrences |
| --- | ---: |
| Sans temps | 2 |
| Futur | 33 |
| Parfait | 46 |
| Plus-que-parfait | 12 |
| Futur antérieur | 6 |

Ces retraits ne sont donc pas tous des parfaits. La comparaison établit leur absence de contribution aux récupérations exactes mesurées ; elle ne tranche pas individuellement leur acceptabilité linguistique.

### Contrôle indépendant des familles de présent

Les attentes sont construites depuis les en-têtes complets et leurs chiffres explicites, sans utiliser les radicaux candidats ni les réponses natives : six cellules d’indicatif, six de subjonctif et un infinitif par dossier. Chaque cellule exige le lemme littéral direct, les traits attendus et la morphologie active/passive source, sans troncature.

| Contrôle des sept familles / 91 cellules | Résultat |
| --- | ---: |
| Cellules avec la lecture attendue avant l’essai | 0 |
| Cellules avec la lecture attendue après l’essai | 91 |
| Lectures attendues après l’essai | 91 |
| Autres lectures préexistantes conservées sur ces cellules | 87 |
| Lectures préexistantes supprimées | 0 |
| Lectures ajoutées, dont les 91 attendues | 110 |

Les **19 autres occurrences ajoutées** sur ces cellules restent à examiner. Les comptes sont mesurés par cellule forme/lemme/grammaire ; ils ne doivent pas être additionnés aux mesures des 591 formes perdues. Ce contrôle qualifie une couverture ciblée de présent dans la copie privée, pas l’abandon des parties principales de la TEI, le paradigme entier ou un remplacement du corpus.

Les sources et index privés reproduisent les empreintes de `db4d002` : source limitée au présent `814d770d2b53fb8b2e4c700c8e6dcb72882893bd2f6d9848cdc0411da28b9d38`, index verbal `b2fe13a794ed08422dedcc794619004e627ce059e6b3bc4f0793c0c12ec378da`, index secondaire `2f89739a3030ce5e97763f33c138cb8fd8ebdda57ad6e3533e5938111e76e75a`. Le dossier privé enrichi par les comparaisons directes et familles a SHA-256 `3029f980dc9b735bac4d0948711a1085fb21f8c3ac3b8ad55a4d3db3855c64d7`. Le premier dossier contrefactuel reste `2d48ac575e8b0e6a8d708e5e9edea909096153569f8de42e6bcb569fef6f4093`. Les empreintes des dossiers d’entrée et des assemblages antérieurs sont reproduites ; les quatre index du candidat final restent inchangés.

La prochaine étape doit examiner les parties principales source et les lectures supplémentaires avant toute règle de récupération générale. Les 510 signatures manquantes de ce groupe, les autres dossiers de définitions manquantes et le reste des pertes globales restent ouverts. Seuls outils, tests synthétiques, agrégats et empreintes sont publiés. La PR reste en brouillon ; le candidat final et la production restent inchangés.

## Isolation diagnostique du présent qualifiée sur `db4d002`

Les trois workflows de [`db4d002`](https://github.com/defense-humanites/libmorpheus/commit/db4d002eaeb8dfa271592a59f7edc3a5aef71235) sont verts : [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37653069586), [plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37653069582) et [recherche lexicale](https://github.com/defense-humanites/libmorpheus/actions/runs/37653062778). Le [job latin](https://github.com/defense-humanites/libmorpheus/actions/runs/37653062778/job/112901114867) valide les 52 tests unitaires ciblés et les huit tests natifs synthétiques.

La seconde copie privée conserve exactement **sept directives littérales `:vs:` de présent**, une par dossier, sans copier de radical du témoin. Son expansion ne contient aucune autre classe pour ces lemmes. Les trois autres entrées verbales et les index nominaux restent contrôlés ; les quatre index du candidat final demeurent inchangés.

| Contrôle ciblé, mêmes 591 formes / 928 signatures attendues | Chiffre isolé avec dérivation | Radicaux de présent isolés |
| --- | ---: | ---: |
| Formes reconnues | 420 | 370 |
| Anciennes signatures exactement retrouvées | 418 | 418 |
| Anciennes signatures toujours manquantes | 510 | 510 |
| Autres lectures ajoutées | 223 | 124 |

Les groupes par temps des lectures retrouvées et manquantes sont également identiques aux mesures précédentes. Les sept en-têtes passent toujours de 0 à 7 lectures attendues couvertes ; les 9 autres lectures préexistantes sont conservées et aucune supprimée. L’essai de présent produit donc les mêmes récupérations exactes mesurées, avec 99 lectures supplémentaires de moins dans cet inventaire. Ces agrégats ne démontrent pas à eux seuls l’inclusion exacte des multisets entre les deux copies ; une comparaison directe reste nécessaire.

Le classement reconnaît désormais les classes parfaites `avperf`, `evperf` et `ivperf`, confirmées par les tables du dépôt. **Trois directives restent toutefois classées « autres » dans la première copie** : leur identité grammaticale doit encore être examinée, et ne doit pas être inférée du seul nom des nouvelles classes prises en compte.

| Sortie de la copie privée limitée au présent | SHA-256 |
| --- | --- |
| Source | `814d770d2b53fb8b2e4c700c8e6dcb72882893bd2f6d9848cdc0411da28b9d38` |
| Index verbal | `b2fe13a794ed08422dedcc794619004e627ce059e6b3bc4f0793c0c12ec378da` |
| Index secondaire | `2f89739a3030ce5e97763f33c138cb8fd8ebdda57ad6e3533e5938111e76e75a` |
| Contrôles natifs privés | `862992e28edb5f3671a44477713436cfd544eb68977bf564975b7d8b32036653` |

« Présent seul » désigne la classe du radical, non une restriction des temps retournés. Cette mesure ne qualifie ni les familles complètes ni l’ajout au candidat final. La prochaine étape examine les directives non classées et compare directement les deux multisets ciblés. La PR reste en brouillon ; le candidat de référence et la production restent inchangés.

## Contre-épreuve des sept chiffres de conjugaison qualifiée sur `38a9cbc`

Le commit [`38a9cbc`](https://github.com/defense-humanites/libmorpheus/commit/38a9cbc08221e31c594d7ec6c5fc1a94618a7f6a) a été rattaché à la branche par le connecteur GitHub après reprise du service, sans interface web. La contre-épreuve privée examine les **sept en-têtes / 928 lectures** sélectionnés dans la revue qualifiée. Les en-têtes sont revalidés contre la TEI épinglée, les transcriptions originales reproduites à l’identique et les empreintes des deux dossiers, du candidat et des assemblages contrôlées.

### Localisation de l’échec d’extraction

Pour les sept cas, le champ `itype` original survit textuellement inchangé dans les sorties de **`combitype`, `splitlat`, `conj1` et `latvb`**. Le préfixe d’en-tête reste également inchangé et une seule balise `itype` demeure à chaque étape. Le rejeu original n’émet aucune définition. Réduire **seulement ce champ** à son chiffre terminal, dans une copie explicitement contrefactuelle, déclenche l’émission sous le même lemme littéral :

| Chiffre source | En-têtes | Rejeux simplifiés émettant sous le lemme attendu |
| --- | ---: | ---: |
| 1 | 2 | 2 |
| 3 | 4 | 4 |
| 4 | 1 | 1 |
| **Total** | **7** | **7** |

Cette mesure montre que les sept champs ne sont pas perdus avant leur arrivée dans le filtre verbal. Leur forme complète n’y déclenche pas l’émission, contrairement au chiffre isolé. Elle ne prouve pas que supprimer leurs parties principales conserve la grammaire source.

### Contrôles natifs ciblés

Les **sept formes d’entrée source** passent de **0 à 7 lectures attendues couvertes**, chacune avec le lemme exact et une analyse directe de première personne du singulier, présent de l’indicatif, voix active/passive attendue. Il ne s’agit pas d’une absence préalable de toute analyse de ces formes : les **9 autres lectures préexistantes sont conservées**, aucune n’est supprimée, et **7 lectures sont ajoutées**.

Les **928 anciennes lectures** des sept lemmes concernent **591 formes distinctes**, toutes sans analyse dans le candidat final qualifié. Leur multiset cible est reproduit exactement par une relecture native du témoin, puis comparé à l’assemblage contrefactuel :

| Mesure ciblée | Résultat |
| --- | ---: |
| Formes reconnues dans la contre-épreuve | 420 / 591 |
| Formes toujours sans analyse | 171 / 591 |
| Signatures cibles à onze champs rétablies, multiplicité comprise | 418 / 928 |
| Signatures cibles toujours absentes | 510 / 928 |
| Autres lectures contrefactuelles sur ces mêmes formes | 223 |

Reconnaître une forme ne signifie pas rétablir son ancienne signature : les **420 formes** ne sont pas un compte de récupérations grammaticales exactes. Les **223 autres lectures** ne sont pas automatiquement source approuvées. Sur ces formes auparavant vides, la contre-épreuve retourne au total **641 lectures**.

| Temps API des signatures cibles | Rétablies exactement | Toujours absentes |
| --- | ---: | ---: |
| Sans temps | 194 | 104 |
| Présent | 122 | 93 |
| Imparfait | 65 | 52 |
| Futur | 37 | 132 |
| Parfait | 0 | 93 |
| Plus-que-parfait | 0 | 24 |
| Futur antérieur | 0 | 12 |
| **Total** | **418** | **510** |

### Limites et prochain contrôle

L’expansion privée comporte **7 directives de classes de présent et 3 directives classées « autres »** par le classificateur actuel. Ce dernier reconnaît `perfstem` mais ne distingue pas encore les alias réguliers `avperf` et `ivperf`, présents dans les règles historiques de [`are_vb`](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/stemlib/Latin/derivs/source/are_vb.deriv) et [`ire_vb`](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/stemlib/Latin/derivs/source/ire_vb.deriv). **On ne peut donc pas déduire de cet agrégat qu’aucun parfait n’a été extrapolé**, ni identifier sûrement les trois autres directives sans compléter ce contrôle. L’absence de récupération d’anciennes lectures parfaites ne prouve pas non plus l’absence de nouvelles lectures parfaites. Cette limite ne change pas les comptes natifs ci-dessus.

Le prochain essai doit **identifier complètement ces classes puis isoler les seules directives de présent**, qualifier les familles natives attendues et examiner les parties principales source avant d’ajouter quoi que ce soit au candidat. La simplification du champ reste une contre-épreuve diagnostique, pas une règle de récupération autorisée. Les mesures portent sur les formes d’entrée et les 591 formes ciblées ; elles n’établissent ni un paradigme complet ni l’absence globale de régressions de l’assemblage contrefactuel.

Les trois entrées verbales conservées et les index nominaux sont contrôlés ; les **quatre index du candidat final restent inchangés** après l’expérience. Les deux passes grammaticales globales précédentes, la revue des **6 789 formes / 11 005 lectures / 133 lemmes**, et celle des **30 lemmes / 2 672 lectures** reproduisent les mesures et empreintes qualifiées. **50 tests ciblés et sept tests natifs synthétiques passent dans le runner.**

Les trois workflows sont verts : [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37646030285), [qualification des plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37646030302) et [recherche lexicale](https://github.com/defense-humanites/libmorpheus/actions/runs/37646019588). Le [job latin](https://github.com/defense-humanites/libmorpheus/actions/runs/37646019588/job/112876857874) a réussi.

| Sortie privée de la contre-épreuve | SHA-256 |
| --- | --- |
| Source verbale contrefactuelle | `f172c3ccf40fff2e264f3667accad45b34c8ae91447c6bd9e36b9aaf28692c0f` |
| Index verbal contrefactuel | `e9805436e30bfd87d0f5fdd485a082c4eb79c03633f8ae1a9343b9ba9f07c20f` |
| Index secondaire contrefactuel | `ccafc613bf74bab0ee194bfcff9a19165ece1e2e312726662d47e3bc0d225b9f` |
| Dossier natif ciblé | `2d48ac575e8b0e6a8d708e5e9edea909096153569f8de42e6bcb569fef6f4093` |

Les formes, lemmes, transcriptions et radicaux individuels restent privés dans le runner ; aucun artefact lexical n’est téléversé. Seuls outils, tests synthétiques, agrégats et empreintes sont publiés. [Protocole](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-terminal-conjugation-probe.md). La PR reste en brouillon et le corpus de production demeure inchangé.

## Revue source des 30 lemmes sans définition finale qualifiée sur `c8efbce`

Le commit [`2250541`](https://github.com/defense-humanites/libmorpheus/commit/22505419953a32531635c31d1f299e173713e3fa), suivi de la déclaration SPDX du protocole sur [`c8efbce`](https://github.com/defense-humanites/libmorpheus/commit/c8efbcedf0a59dcc104ec79d6e54b3a48deae55a), examine les **30 lemmes / 2 672 lectures** sans définition finale. Le diagnostic privé, le candidat et l’assemblage final reproduisent leurs empreintes qualifiées. Les jointures complètes — en-têtes, routes, partitions et XML/digests des articles — sont reconstruites contre la TEI épinglée et vérifiées à l’identique.

| Résultat mécanique de la revue | Lemmes | Lectures complètement perdues |
| --- | ---: | ---: |
| Article unique, partition verbale, aucune définition émise par le rejeu historique isolé | 15 | 1 842 |
| Article unique, partition nominale, aucune définition émise par le rejeu historique isolé | 3 | 281 |
| Aucune jointure littérale avec les clés projetées ou les orthographies émises | 12 | 549 |
| **Total** | **30** | **2 672** |

Les **18 articles rejoints** ont tous une première orthographie de portée `full`, et leur orthographie d’en-tête, après suppression des seules marques `_^-`, correspond exactement au lemme littéral perdu, suffixe d’homographe conservé. Aucune ambiguïté ni substitution d’identité n’est détectée dans ce groupe. Aucun de ces 18 lemmes ne possède de définition dans le candidat brut ni dans l’assemblage final. Le rejeu indépendant de chaque en-tête par `combitype → splitlat → conj1 → latvb` n’émet aucune directive de radical liée à un lemme. Les blocs vides et le texte ECHO ne comptent pas comme définitions.

Cette mesure situe les **15 cas déjà classés verbaux** dans l’extraction historique : changer seulement leur partition ne suffit pas à obtenir un radical dans ce rejeu. Elle ne valide pas le paradigme du témoin et n’autorise aucune réinsertion. Les **3 cas nominaux** n’ont aucun signal verbal direct au premier sens selon le contrôle existant ; leur statut lexical demande un arbitrage. L’absence de jointure des **12 autres cas** ne prouve pas l’absence d’un article linguistiquement correspondant : aucune normalisation supplémentaire ni équivalence de lemme n’est supposée.

### Profils syntaxiques des 15 en-têtes verbaux non émis

| Profil des champs `itype` projetés | Lemmes | Lectures |
| --- | ---: | ---: |
| Un champ de parties principales terminé par un chiffre de conjugaison | 7 | 928 |
| Plusieurs champs `itype` | 2 | 253 |
| Aucun champ `itype` | 2 | 311 |
| Un autre champ `itype` | 3 | 349 |
| Un champ ayant la forme d’un infinitif | 1 | 1 |
| **Total** | **15** | **1 842** |

Ces profils décrivent la syntaxe projetée, pas une approbation linguistique. Le prochain groupe borné à examiner est celui des **sept champs à chiffre de conjugaison**, avec leurs articles et sorties intermédiaires privés, pour déterminer une règle source et la qualifier nativement avant tout ajout.

Les **deux passes grammaticales globales** et le diagnostic natif des **6 789 formes / 11 005 lectures / 133 lemmes** reproduisent les mesures et empreintes précédentes. **41 tests ciblés et six tests natifs synthétiques passent dans le runner.** Les trois workflows du dernier commit sont verts : [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37634470838), [qualification des plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37634470791) et [recherche lexicale](https://github.com/defense-humanites/libmorpheus/actions/runs/37634462185). Le [job latin](https://github.com/defense-humanites/libmorpheus/actions/runs/37634462185/job/112836888973) a réussi. La première tentative des deux workflows généraux échouait uniquement sur l’absence de l’identifiant SPDX dans le nouveau protocole ; cet oubli est corrigé dans le dernier commit.

Empreinte SHA-256 du dossier privé des 30 revues : `0cf86ce597e83ff92f0301b06fb34b700a714eaddccd66eb9a195cf0c58decbc`. Les deux rejeux `2250541` et `c8efbce` reproduisent la même revue et son empreinte. Les formes, lemmes, articles individuels, radicaux et transcriptions restent privés dans le runner ; aucun dossier n’est téléversé en artefact. Seuls outils, tests synthétiques, agrégats et empreintes sont publiés. [Protocole](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-missing-definition-review.md). La PR reste en brouillon et le corpus de production demeure inchangé.

## Diagnostic natif et source des pertes complètes qualifié sur `8eeb5f6`

Le commit [`8eeb5f6`](https://github.com/defense-humanites/libmorpheus/commit/8eeb5f63a7558bb405b62ddecd1506792b50bf3e) relit les **6 789 formes complètement perdues** avec l’API native, sur les mêmes racines témoin et finale. Il reproduit exactement leurs **11 005 lectures**, toutes verbales, et leurs **133 lemmes distincts**, avec les mêmes multisets à onze champs et leurs multiplicités. Chaque forme reste sans lecture dans le candidat final. Les champs textuels utilisés par le diagnostic sont vérifiés pour chaque analyse, avec les signatures publiques à trois arguments des accesseurs FFI ; une troncature ou une erreur native interrompt le contrôle.

Les **deux passes grammaticales globales** sont également répétées et reproduisent les comptes, la matrice et l’empreinte privée de `d861a41` : `08f0aca20f35eecf95f24a50690ad91a35a139663f558570d9ea86ea07f8bd52`. Les sources, les candidats des deux traitements de quantité, les quatre index, la citation passive et les 65 cellules des cinq familles reproduisent la qualification antérieure. Le contrôle de la même racine finale reste sans différence.

### Définitions verbales dans les assemblages complets

Le contrôle porte sur les fichiers développés complets, incluant le fichier remplacé **et les trois fichiers verbaux conservés**. Il compare les lignes sous le même lemme exact, avec leurs flags et multiplicité. Ces états décrivent des définitions littérales ; une différence de notation ou d’espacement n’est pas à elle seule une régression sémantique.

| État des définitions sous le lemme exact | Lemmes distincts | Lectures complètement perdues |
| --- | ---: | ---: |
| Définitions témoin présentes, aucune définition finale | 30 | 2 672 |
| Multisets de définitions modifiés | 59 | 5 547 |
| Aucune définition explicite dans les deux assemblages | 44 | 2 786 |
| **Total** | **133** | **11 005** |

Les **2 672** lectures des 30 lemmes sans définition finale sont toutes directes. Les **2 786** lectures des 44 lemmes sans définition explicite dans les deux assemblages proviennent toutes du mécanisme natif de préverbes : leur absence comme bloc ne prouve donc pas un défaut de lemme à corriger. Les 59 lemmes modifiés portent 5 456 lectures directes et 91 lectures à préverbe.

La présence dans les entrées brutes confirme **5 545** lectures sous des lemmes présents seulement dans le fichier remplacé, **2** avec présence dans le fichier remplacé et dans les fichiers conservés, et **5 458** sous des lemmes absents des quatre entrées finales. Cette dernière observation inclut les compositions natives ; elle n’autorise pas une réinsertion automatique de paradigmes.

### Correspondances des radicaux natifs avec les jetons développés

| Correspondance sous le même lemme exact | Lectures |
| --- | ---: |
| Jeton exact dans le témoin et dans le candidat | 66 |
| Jeton exact dans le témoin, aucune correspondance exacte dans le candidat | 2 113 |
| Piste après retrait de `_`, `^`, `-` dans les deux assemblages | 176 |
| Piste après retrait de ces marques dans le témoin, aucune dans le candidat | 5 003 |
| Radical natif sans correspondance dans les définitions témoin examinées | 3 647 |

Ce sont des **comptes de lectures**, pas de radicaux distincts. La piste de notation est séparée de l’identité exacte. Les 2 113 cas sans correspondance exacte finale peuvent encore avoir une autre notation ; un jeton conservé ne garantit pas la conservation des flags et de la lecture perdue. Les 3 647 cas sans correspondance témoin restent non résolus plutôt que déclarés absents du moteur. Aucun de ces groupes n’approuve un paradigme.

### Rapprochement avec les articles TEI validés

Les routes gardent la clé projetée et la vedette émise, leurs suffixes d’homographie et leur identité d’article. **82 lemmes** rejoignent chacun un article unique ; **51** n’ont pas de rapprochement validé par ces routes. Aucun rapprochement multiple n’est trouvé dans ce jeu, mais le diagnostic conserve explicitement les ambiguïtés lorsqu’elles existent.

| Article unique et partition de recherche, ou absence de rapprochement | Lemmes distincts | Lectures |
| --- | ---: | ---: |
| Article classé verbal | 77 | 7 496 |
| Article classé nominal | 5 | 528 |
| Aucun rapprochement validé | 51 | 2 981 |

Le sélecteur de recherche n’est pas le `vtags` historique et sa partition ne démontre pas une cause linguistique. Parmi les **2 672** lectures dont le lemme n’a plus de définition finale, **1 842** rejoignent un article classé verbal, **281** un article classé nominal et **549** aucun article par ces routes. Ce sous-ensemble constitue une priorité concrète pour l’examen source ; ces nombres ne sont pas des comptes de formes ou de lemmes distincts.

### Validation et empreintes

**33 tests unitaires ciblés et six tests d’intégration native passent dans le runner**, dont une perte complète causée par un changement de radical synthétique, vérifiée contre les définitions réellement développées. Le test de troncature inspecte aussi la deuxième lecture. Les trois workflows du dernier commit sont verts : [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37610801659), [qualification des plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37610801624) et [recherche lexicale](https://github.com/defense-humanites/libmorpheus/actions/runs/37610793507). Le [job latin et son diagnostic source](https://github.com/defense-humanites/libmorpheus/actions/runs/37610793507/job/112757276071) ont réussi.

| Sortie ou entrée privée | SHA-256 |
| --- | --- |
| Dossier natif et source des pertes complètes | `a4be9ccc97383f48f4ba94bc4e23092e17b729a685eb01c5242d2bfac9c4ba1a` |
| Assemblage verbal développé témoin | `f64a9c551a1c56013c645628408e79a02bb6b9672bc98585f8c0edd7038836c3` |
| Assemblage verbal développé final | `83e4157c96bc029fa6950c589c5a26f4f1c55eef07a2654d7cc771ceeafa0940` |

Le dossier privé garde les formes, les lectures natives, les radicaux, les définitions et les articles XML avec leurs empreintes. Il n’est ni commité ni téléversé comme artifact Actions. Seuls outils, tests synthétiques, agrégats et empreintes sont publiés. [Protocole du diagnostic](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-complete-loss-diagnostic.md).

Les 30 lemmes sans définition finale et les 59 lemmes modifiés restent à arbitrer sur preuve source. Les cas issus de préverbes et les rapprochements non résolus demandent leurs propres critères. Aucun radical ni paradigme n’est ajouté par cette étape ; le corpus de production demeure inchangé et la PR reste en brouillon.

## Comparaison grammaticale globale qualifiée sur `d861a41`

Le commit [`d861a41`](https://github.com/defense-humanites/libmorpheus/commit/d861a41a473561d6badab187d8ed093c36f07b4e) ajoute deux passes complètes : la racine finale contre elle-même, puis le témoin reconstruit contrôlé contre cette racine. Chaque passe couvre **1 033 579 formes**, avec options natives zéro et tous les couples de statuts API `0,0`. Les multisets sont comparés pour chaque forme dans les onze champs : workword, lemme, POS, personne, nombre, genre, cas, temps, mode, voix et degré. L’ordre des résultats est ignoré et leur multiplicité est conservée.

Le contrôle de la même racine conserve **2 100 530 lectures**, avec zéro changement de compte ou de multiset, zéro ajout et zéro suppression. Les sources, les candidats des deux traitements de quantité, les quatre index et les totaux de reconnaissance et de lectures reproduisent exactement les [empreintes de référence](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/tools/latin-final-present-reference.json) qualifiées sur `e42866d`. Les onze passes de comptes précédentes restent qualifiées sur ce commit ; la présente exécution ajoute **deux passes grammaticales globales**, sans les répéter.

### Matrice finale mesurée

| Reconnaissance témoin contrôlé → candidat final | Formes |
| --- | ---: |
| Les deux racines | 831 201 |
| Témoin seul | 6 789 |
| Candidat seul | 16 549 |
| Aucune | 179 040 |

Le témoin reconnaît **837 990** formes et le candidat **847 750**, soit un gain net de **9 760**. La comparaison avec la matrice historique témoin→alternance vocalique montre que les **206** formes rétablies par les cinq dernières graphies sont toutes des gains nouveaux : **aucune des 6 789 pertes historiques n’est réparée**.

### Lectures conservées, retirées et ajoutées sur tout LISTALL

| Multisets à onze champs, multiplicité comprise | Lectures |
| --- | ---: |
| Conservées | 2 006 554 |
| Retirées | 41 774 |
| Ajoutées | 93 976 |
| Total témoin | 2 048 328 |
| Total candidat | 2 100 530 |

**60 937** formes changent de compte ; **66 927** changent de multiset grammatical. Les **5 990** formes supplémentaires ont des lectures différentes malgré un compte identique. Les équations de conservation sont vérifiées : conservées + retirées = total témoin ; conservées + ajoutées = total candidat. Le gain net de 52 202 lectures ne démontre donc pas la conservation des analyses du témoin.

| POS API | Lectures retirées | Lectures ajoutées |
| --- | ---: | ---: |
| Nom | 24 | 7 |
| Verbe | 41 719 | 93 969 |
| Adjectif | 31 | 0 |

Ces lignes sont des occurrences de signatures natives. Elles ne sont ni des comptes de formes ni des diagnostics de cause.

### Diagnostic des pertes complètes

Les **6 789** formes reconnues uniquement par le témoin portaient **11 005 lectures**, toutes verbales, concernant **133 lemmes distincts**. Elles comprennent **8 128** lectures directes et **2 877** lectures issues du mécanisme natif de préverbes ; aucune signature perdue de ce groupe n’a une provenance mixte.

| Temps API des lectures complètement perdues | Lectures |
| --- | ---: |
| Sans temps | 1 948 |
| Présent | 2 146 |
| Imparfait | 1 363 |
| Futur | 2 591 |
| Parfait | 2 112 |
| Plus-que-parfait | 564 |
| Futur antérieur | 281 |

| Présence exacte du lemme dans le seul fichier verbal remplacé | Directes | Préverbes | Total |
| --- | ---: | ---: | ---: |
| Présent dans ce fichier | 5 456 | 91 | 5 547 |
| Absent de ce fichier | 2 672 | 2 786 | 5 458 |

Cette présence vérifie les octets du lemme, sans normalisation. Elle exclut les trois autres entrées verbales conservées dans l’assemblage : un lemme absent de ce fichier n’est pas nécessairement absent du runtime ; un lemme présent ne prouve pas que son radical ou paradigme requis existe. Ces groupes orientent l’examen source suivant et ne démontrent pas les causes linguistiques des pertes. Hors des pertes complètes, **30 769** lectures du témoin sont également retirées sur des formes encore reconnues.

Les **24 tests unitaires ciblés et cinq tests d’intégration native** passent dans le runner, dont une substitution de lemme à compte identique. Les trois workflows du dernier commit sont verts : [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37601021030), [qualification des plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37601020966) et [recherche lexicale](https://github.com/defense-humanites/libmorpheus/actions/runs/37601013584). Le [job latin global](https://github.com/defense-humanites/libmorpheus/actions/runs/37601013584/job/112725110543) a réussi.

Empreinte SHA-256 du fichier privé des différences globales : `08f0aca20f35eecf95f24a50690ad91a35a139663f558570d9ea86ea07f8bd52`. Le contrôle identique produit un fichier vide, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Les formes, lemmes et signatures détaillées restent privés dans le runner ; seuls outils, tests synthétiques, agrégats et empreintes sont publiés.

[Protocole global](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-global-reading-qualification.md). Cette qualification établit la mesure, pas l’acceptabilité d’un remplacement du corpus. La PR reste en brouillon ; le corpus de production demeure inchangé.

## Qualification complète du présent cité et des cinq graphies sur `e42866d`

Le commit [`e42866d`](https://github.com/defense-humanites/libmorpheus/commit/e42866dcfe92b311b3492a25d457fe51ec7de77c) qualifie les six dossiers nécessitant des critères distincts : un présent cité dans un article à deux supins et cinq graphies complètes de leurs propres en-têtes. Les cinq règles bornent l’omission nasale, le préfixe avec restauration vocalique, une alternance consonantique devant une liquide, l’élision à une frontière explicitement délimitée et le préverbe court/complet. Elles exigent la grammaire explicite, un présent canonique unique apparié à la source et la même sous-classe de conjugaison. Aucun parfait ni supin n’est ajouté.

Le contrôle source confirme **un puis cinq ajouts** par traitement de quantité. Les cinq dernières familles ont chacune une règle distincte ; leurs témoins sont identiques entre traitements hormis l’empreinte du candidat. L’inventaire reconstruit de seize dossiers est désormais traité ainsi :

| Résultat dans les essais de présent | Dossiers |
| --- | ---: |
| Qualifiés par renvoi indépendant unique | 9 |
| Qualifiés par citation passive et grammaire à supins coordonnés | 1 |
| Qualifiés par graphie complète et transformation bornée | 5 |
| Abréviation contextuelle exclue de l’insertion littérale | 1 |

Le seul dossier restant est exactement l’abréviation déjà exclue, avec contrôle de son empreinte d’article ; son inventaire privé a SHA-256 `48a62d1fc5a145f496887dd156c748e4cb6eec868efc334ba3df0e906efd2101`. Cette qualification du nouvel inventaire ne prouve pas son identité avec l’ancien fichier privé indisponible.

Le présent passif cité a **une lecture attendue avant et après** l’ajout : une lecture directe du lemme source, troisième personne du singulier, présent de l’indicatif passif. La première version du contrôle sur `04a88f4` échouait parce qu’elle exigeait une absence préalable, alors que l’assemblage verbal conservé contient déjà le radical correspondant. Le contrôle corrigé mesure cette couverture et vérifie la lecture après insertion. La lecture précédente est conservée ; les index et tous les comptes LISTALL de cette étape restent identiques.

Les cinq graphies passent le contrôle indépendant de **65 cellules** : six indicatifs, six subjonctifs et un infinitif au présent actif par variante. La couverture attendue passe de **13 à 65** cellules, avec 65 lectures conformes après ajout. Sur ces mêmes entrées, les multisets à onze champs conservent **37** anciennes lectures, ajoutent **64** lectures verbales directes et n’en suppriment aucune.

Les **onze passes complètes** couvrent chacune **1 033 579 formes** et tous les couples de statuts API sont `0,0`. Les cinq contrôles identiques ont zéro différence. Les **sept rapports antérieurs**, leurs empreintes privées et les **quatre index antérieurs** reproduisent exactement `6d0a199`. Les deux traitements de quantité donnent les mêmes index et les témoins nominaux demeurent fixes.

| Étape consécutive nouvelle | Formes rétablies | Formes perdues | Comptes augmentés | Lectures ajoutées |
| --- | ---: | ---: | ---: | ---: |
| Présent cité avec supins coordonnés | 0 | 0 | 0 | 0 |
| Cinq graphies complètes bornées | 206 | 0 | 309 | 462 |

Les **462** ajouts de la dernière étape sont tous des lectures verbales directes des lemmes source. Les **163** anciennes lectures des formes dont le compte change sont conservées dans les onze champs comparés, sans suppression. Le candidat final reconnaît **847 750 formes** et retourne **2 100 530 lectures**.

Ces mesures sont une série Linux contrôlée. Sur `e42866d`, le croisement complet témoin→candidat final et les changements grammaticaux à compte égal restaient à mesurer. La qualification globale sur `d861a41`, consignée ci-dessus, effectue désormais ce croisement sur chaque forme et montre que les 206 gains ne réparent aucune des 6 789 pertes historiques. La présente section conserve les mesures consécutives de `e42866d`.

### Empreintes de la qualification sur `e42866d`

| Sortie privée ou index | SHA-256 |
| --- | --- |
| Radicaux, toutes quantités | `c130bad78f1b7d34542057393d2c79669aa4378325b4540b53ba6a25986678a4` |
| Radicaux, traitement des lettres | `6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9` |
| Index verbal commun | `d13367a683e0645adcbe83ab1b34ddc9a4444c8d22d2c9d83fcaf5e875f39ac4` |
| Index secondaire commun | `486c8641cb83a5d1b8dd2184aae9204b7f7a77ce3293daadbe4a7c1b3b36e954` |
| Contrôle de la même racine finale | `488b65bf28b415a36706735034d3c823a0e85e3551af1af2773eb305e04ec1de` |
| Comparaison consécutive des cinq graphies | `d2a61da5de2d934685dd2aaaf132baea5657f20eea4ccec7c815f4cbac36dde1` |
| Contrôle privé des 65 cellules | `f326621ee446b8bba66345bc7348ab3a4f36c9727aa95d72d103d08c3a0d4452` |
| Contrôle privé de la citation passive | `d01bfdb8651e74e7f966aed811ab5d81426b94916b61cad46216e8d0af9567fc` |

**35 tests ciblés passent localement et quatre tests natifs synthétiques passent dans le runner.** Les trois workflows du commit sont verts : [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37426892295), [qualification des plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37426892334) et [recherche lexicale](https://github.com/defense-humanites/libmorpheus/actions/runs/37426884736). Le [job latin complet](https://github.com/defense-humanites/libmorpheus/actions/runs/37426884736/job/112148459316) a réussi.

Protocoles : [présent cité](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-coordinated-present-qualification.md) et [cinq graphies](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-bounded-present-qualification.md). Ces fichiers décrivent les critères et attentes au commit ; les mesures finales du run sont consignées ici. Seuls outils, tests synthétiques, agrégats et empreintes sont publiés. La PR reste en brouillon et le corpus de production demeure inchangé.

## Inventaire source et neuf présents supplémentaires

La source locale correspond exactement à la TEI épinglée : SHA-256 `ccbd2f79db1006edc607fe51227babab6872fbdaa4e925f4c1999a3b978041ee`, blob Git `a67c25871afc486ea91c44ebdb5cb2e25b718247`. La projection, les en-têtes récupérés et l’inventaire strict reproduisent les empreintes de la CI.

Le sélecteur strict trouve **15 variantes dans 15 articles**. Un mode diagnostique borné à la syntaxe de deux supins reliés par `and` trouve **16 variantes dans 16 articles**, avec exactement un dossier supplémentaire. Ce périmètre est expliqué ; l’identité avec l’ancien fichier privé de seize dossiers reste à vérifier. Les deux traitements de quantité produisent les mêmes dossiers :
- inventaire strict : `66b6c1c1d3b22619a8077c788cabeda889230d4f288e27d5fdcb80eeb1b72f3d` ;
- inventaire élargi : `f2d4517cbef3a014758ebbc6b50394126bbe96a5da2aa86c508efd2c988697a0`.

L’examen individuel du nouvel inventaire donne :

| Décision initiale de l’examen source | Variantes |
| --- | ---: |
| Présent complet dans son article, confirmé par une entrée distincte renvoyant explicitement à cet article | 9 |
| Graphie complète explicite nécessitant un autre critère de récupération | 5 |
| Composant abrégé contextuellement, exclu d’une insertion littérale sous le lemme composé | 1 |
| Grammaire à supins coordonnés et citation au présent passif, nécessitant un essai distinct | 1 |

Empreinte du registre privé : `3c007771de47fe140cdcfb3de75f17ce0cba7477f4e43aa741fcdab9e3bf2882`.

Le nouvel outil ajoute **neuf enregistrements de présent sous neuf lemmes existants**. Les anciens enregistrements restent inchangés. Les références intégrées à un développement, les ambiguïtés, les grammaires ou voix incompatibles et les abréviations ne satisfont pas son critère.

Les neuf en-têtes isolés reproduisent leurs radicaux attendus dans les filtres historiques. Le contrôle natif indépendant couvre **117 couples forme/lemme/grammaire** : couverture attendue de **0 à 117**, avec 117 lectures conformes après l’essai. Sur ces mêmes entrées, les multisets à onze champs conservent **189** anciennes lectures, ajoutent **149** lectures verbales directes et ne suppriment aucune lecture. Les deux traitements de quantité donnent les mêmes index et les témoins nominaux restent fixes.

Ces mesures constituent une **série locale macOS distincte** : les sorties brutes des filtres historiques diffèrent du runner Linux, malgré l’identité des en-têtes et dossiers source. Le contrôle ciblé compare ses propres racines avant/après. Les sept passes passent aussi sur ces 117 formes locales, sans erreur API, avec trois contrôles identiques sans différence.

Au stade des neuf ajouts, **six dossiers stricts** restaient : cinq graphies à qualifier et l’abréviation exclue. Le dossier à supins coordonnés était hors de ce sélecteur ; les deux nouveaux essais qualifiés ci-dessus laissent désormais uniquement l’abréviation exclue. Empreinte privée des six dossiers : `bca781f7c5292333e4df155022f4816f55f0771b8669fe52ddb35a2e42d058d6`.

Critères et limites : [inventaire restant](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-remaining-present-review.md) et [qualification des renvois indépendants](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-backlinked-present-qualification.md).

## Qualification Linux complète sur `6d0a199`

Les anciennes mesures comportaient cinq arbitrages nominaux privés indisponibles dans l’environnement repris. La série automatisée utilise les données nominales du témoin reconstruit contrôlé et ne prétend pas reproduire ces anciens totaux.

Les sept passes couvrent **1 033 579 formes distinctes**, avec ABI 2 et options zéro. Toutes ont zéro erreur API ; les trois contrôles identiques ont zéro différence. Les cinq anciens rapports, leurs empreintes privées et les trois anciens index reproduisent exactement `f9338dc`, qui reproduisait `37f979e`. Le [rejeu complet](https://github.com/defense-humanites/libmorpheus/actions/runs/37372785571/job/111973821302) a réussi. Les deux traitements de quantité produisent les mêmes index ; les témoins nominaux restent inchangés.

| Étape consécutive | Formes rétablies | Formes perdues | Comptes augmentés | Lectures ajoutées |
| --- | ---: | ---: | ---: | ---: |
| Onze présents à frontière de préfixe | 0 | 0 | 528 | 794 |
| Quatre présents à alternance vocalique interne | 92 | 0 | 206 | 312 |
| Neuf présents confirmés par renvoi indépendant | 0 | 0 | 490 | 747 |

Les **1 163**, puis **182**, puis **922** anciennes lectures des formes dont le compte change sont conservées dans les onze champs comparés, sans suppression. Ces nombres concernent des étapes consécutives et ne forment pas un total de lectures distinctes. La première étape ajoute 780 lectures verbales directes et 14 lectures issues de préverbes à examiner ; les **312** puis **747** ajouts des deux étapes suivantes sont tous directement rattachés aux lemmes source.

Le candidat après l’alternance vocalique reconnaît **847 544** formes et retourne **2 099 321** lectures. Les neuf nouveaux radicaux portent ce total à **2 100 068** lectures sur exactement les mêmes formes : cette étape enrichit les analyses de formes déjà reconnues et ne rétablit aucune forme absente. La reconnaissance face au témoin reconstruit contrôlé reste donc la suivante — déduction de la comparaison témoin→alternance vocalique et de l’absence de tout changement de reconnaissance lors de l’étape suivante :

| Reconnaissance | Formes |
| --- | ---: |
| Les deux racines | 831 201 |
| Témoin seul | 6 789 |
| Candidat seul | 16 343 |
| Aucune | 179 246 |

Le gain net de 9 554 formes ne résout pas les 6 789 pertes. La comparaison globale témoin→alternance vocalique porte sur les comptes et ne contrôle pas les multisets grammaticaux ; aucun contrôle grammatical global témoin→renvois indépendants n’a été exécuté. [Compte rendu complet](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-present-replay-qualification.md).

### Empreintes du nouveau rejeu

L’entrée LISTALL a SHA-256 `1df0800fb1443b2cfd64d787c257319aa72b69f453c3c37ec60c359c70cebd93`. Les empreintes Linux de cette étape sont distinctes de la série locale macOS :

| Sortie privée ou index | SHA-256 |
| --- | --- |
| Radicaux, toutes quantités | `5a11ca636d4ac9eaac48a69608c4cd474ac943a59b3c2ecb629e44092254dded` |
| Radicaux, traitement des lettres | `309942cb9bf28580562c1dce26b43b9210089199119f190a87aa6ffa926b12ef` |
| Index verbal commun | `97fcde5d7da6bc9423f5434f56ff30fb4fc38c1285795bd02a5585ae48d5ecd3` |
| Index secondaire commun | `5ae0b185886a7b181478ba19631f3d2c80eec5e34905c7103a2354226e2971ae` |
| Contrôle de la même racine | `fc99203e0decaba03cf7752dc68e20adbfb451099311f4a80aa4d4d7c3ceb2b2` |
| Comparaison consécutive | `9e75aaf4dba4f5e7dedb214ec03beea92479bcf8d2090657bb9c3f485bb8ef52` |

La CI confirme les empreintes des inventaires strict (15), élargi (16) et restant après récupération (6), identiques entre traitements de quantité et aux dossiers locaux. Seuls ces agrégats et empreintes sont publiés.

## Validation historique sur `6d0a199`

Le commit [`6d0a199`](https://github.com/defense-humanites/libmorpheus/commit/6d0a199d0a799e22e4c5418ee65a3ec816927c3a) publie les outils, tests, workflow et comptes rendus de cette reprise. **115 tests synthétiques et deux tests d’intégration native passent localement.** Les suites du nouvel outil et du rejeu ont été revérifiées après le dernier ajustement.

Les trois CI du commit `6d0a199` sont vertes : [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37372789901), [qualification des plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37372789927) et [recherche lexicale](https://github.com/defense-humanites/libmorpheus/actions/runs/37372785571). Les jobs annulés avant exécution ont réussi après relance ciblée, en conservant les jobs déjà réussis. Le contrôle grec, l’identité des projections autonome/checkout, les inventaires à quinze et seize dossiers, les neuf ajouts et les sept comparaisons complètes ont tous passé.

