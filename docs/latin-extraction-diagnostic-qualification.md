<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Qualifications des diagnostics d’extraction latins

Ces résultats agrégés proviennent des qualifications CI de la PR nº 18. Les dossiers individuels restent privés. Ils ne constituent pas une approbation du remplacement du corpus.

## Revue source des préverbes sur `f3f8c15` — qualification mesurée

Le commit [`f3f8c15`](https://github.com/defense-humanites/libmorpheus/commit/f3f8c15df1725f9d76fe77181385a934f00e6a40) rapproche les ajouts par préverbes de leurs articles source, sans hériter de la conjugaison du verbe de base. Les dossiers privés sont liés aux empreintes qualifiées ; leur projection grammaticale est reproduite.

**Les trois workflows réussissent** : [Linux](https://github.com/defense-humanites/libmorpheus/actions/runs/37802685333), [plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37802685476), [recherche](https://github.com/defense-humanites/libmorpheus/actions/runs/37802676749). Les 91 tests unitaires ciblés et les 10 tests d’intégration native passent. Les résultats globaux précédents sont reproduits à empreintes identiques.

**Les 123 lectures par préverbes concernent un seul autre lemme**, non 123 lemmes. Ce lemme n’a aucune définition dans le candidat final original et **aucun article joint** par les routes exactes de l’index actuel (clé projetée ou headword émis, numéros d’homographes conservés). Aucune lecture ne reçoit donc une attente de présent sous un article unique littéralement identique. Répartition : 33 lectures sans temps spécifié, 47 présentes, 26 imparfaites et 17 futures.

Cette absence de jointure **ne prouve pas l’absence du lemme dans le TEI complet** : les articles en erreur de projection sont exclus de cet index, et aucune identité alternative n’est substituée. Une recherche source élargie et bornée reste nécessaire avant arbitrage. Les 123 lectures ne sont pas approuvées ; la copie de présent reste expérimentale.

Dossier privé SHA-256 : `8d79a647c74830d83f026058866aa149915f529ff0b9da706c1bb260b6cf4e1a`. Les entrées sont vérifiées inchangées. Articles, formes et décompositions restent privés. Aucun essai n’est promu ; PR en brouillon, production inchangée. [Méthode et limites](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-source-present-preverb-review.md).

## Présent à chiffre source sur `1174ee2` — qualification mesurée

Le commit [`1174ee2`](https://github.com/defense-humanites/libmorpheus/commit/1174ee2685c5ced75144f3d55531bdc04a8ce677) sélectionne l’unique essai réussi dont le champ source contient un chiffre de conjugaison nu, sans indication terminale contradictoire. L’orthographie source est complète et le lemme littéral identique. Les autres champs de l’en-tête restent conservés comme preuves ; aucune partie passée n’est reconstruite. La copie de présent déjà construite est revalidée par les empreintes qualifiées de sa source, de ses index et de son dossier natif.

**Les trois workflows ont réussi** : [Linux](https://github.com/defense-humanites/libmorpheus/actions/runs/37792624984), [plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37792624900), [recherche](https://github.com/defense-humanites/libmorpheus/actions/runs/37792618112), dont le [job latin](https://github.com/defense-humanites/libmorpheus/actions/runs/37792618112/job/113363707928). Les 83 tests unitaires ciblés et les 10 tests d’intégration native passent.

### Famille de présent issue du chiffre source

Une famille, sous un seul lemme source, comporte 13 cellules indépendamment attendues : six indicatifs, six subjonctifs et un infinitif présents. La couverture passe de **0 à 13 cellules**. Les trois lectures antérieures sont conservées ; aucune n’est supprimée. Les 15 lectures ajoutées sont toutes directes sous ce lemme : **13 attendues et deux supplémentaires**, au présent passif, deuxième personne du singulier (une impérative et une indicative). La comparaison étendue des décompositions confirme ces mêmes nombres et aucun ajout par préverbe dans cette famille. Ces deux lectures supplémentaires ne sont pas comptées comme cellules attendues.

### Comparaison globale candidat final → copie de présent

Les **1 033 579 formes** de LISTALL sont comparées, options natives 0, sur les multisets à onze champs, y compris les changements à compte égal, avec garde de troncature. Tous les couples de statuts API valent 0/0.

| Mesure | Résultat |
| --- | ---: |
| Formes reconnues dans les deux copies | 847 750 |
| Formes absentes avant, reconnues après | **93** |
| Formes reconnues avant, absentes après | **0** |
| Formes absentes dans les deux copies | 185 736 |
| Lectures avant → après | 2 100 530 → 2 100 776 |
| Lectures conservées / supprimées / ajoutées | **2 100 530 / 0 / 246** |
| Formes dont le multiset grammatical change | 188 |
| Changements à compte égal | 0 |

Les 246 ajouts sont verbaux : **123 directs sous le lemme source et 123 par préverbe natif sous d’autres lemmes**. Chaque route a la même répartition numérique : 33 lectures sans temps spécifié, 47 présentes, 26 imparfaites et 17 futures. Aucun ajout au parfait, plus-que-parfait ou futur antérieur ; aucun changement nominal ou adjectival. Une entrée limitée au radical de présent peut donc produire aussi des lectures d’imparfait et de futur.

Les décompositions étendues sont relues sur les **188 formes dont les onze champs changent** et reproduisent les 246 ajouts, sans suppression. Cette relecture distingue les routes et les relations de lemmes ; **elle n’est pas un audit global à seize champs**. Le contrôle global copie → même copie conserve les 2 100 776 lectures, sans aucun changement sur les 1 033 579 formes.

### Limites et reçus

**Les 123 ajouts sous d’autres lemmes par préverbe restent à arbitrer avec leurs articles source.** Le résultat numérique ne constitue pas leur approbation lexicale. La justification des 99 lectures récupérées seulement par l’essai complet précédent reste également ouverte. Les nombres de cette famille, de cette comparaison globale et des deux isolations précédentes ne doivent pas être additionnés comme des récupérations distinctes.

Les index du candidat final d’origine sont vérifiés inchangés. Aucun essai n’est promu au candidat ou à la production ; la PR reste en brouillon. Seuls les outils, tests synthétiques, agrégats et empreintes sont publiés.

| Reçu SHA-256 | Empreinte |
| --- | --- |
| Source de la copie de présent | `fa0fb3904e5c43bf6c95ed1cffa7b6072408ddc985025ffbc51669b1732677c4` |
| LISTALL comparé | `1df0800fb1443b2cfd64d787c257319aa72b69f453c3c37ec60c359c70cebd93` |
| Dossier privé de la famille | `908e52e24b67fa56e6b46435c763a03d053393808e45759f4b965f3f0fdeec91` |
| Différence globale privée | `b84e4cc77a9c8581285b3a47271277f917b1a52411a5355c39295997d419bbc3` |
| Relecture privée des routes | `461da7b4d5a082c072c553d501f4541c1f297f78b92c0b2a79fca28a3c34c627` |
| Différence vide du contrôle identique | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

[Critères et limites de cette qualification](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-isolated-source-present-qualification.md). Les mesures complètes des itérations précédentes sont conservées dans le [compte rendu archivé](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-extraction-diagnostic-qualification.md).

## Essais natifs des champs isolés qualifiés sur `e131f03`

Le commit [`e131f03`](https://github.com/defense-humanites/libmorpheus/commit/e131f038aaf01c9f5557b5598d1012521a636f26) est qualifié par les trois workflows verts : [Linux](https://github.com/defense-humanites/libmorpheus/actions/runs/37781371593), [plateformes](https://github.com/defense-humanites/libmorpheus/actions/runs/37781371607), [recherche](https://github.com/defense-humanites/libmorpheus/actions/runs/37781363582). Le [job latin](https://github.com/defense-humanites/libmorpheus/actions/runs/37781363582/job/113324992698) confirme **76 tests unitaires ciblés et dix tests natifs**, dont le nouveau contrôle synthétique de la productivité d’une dérivation.

Les cinq essais de champs source sont reproduits exactement. **Les deux essais émettant sous le lemme attendu concernent un seul lemme**, parmi les huit dossiers ; leurs cibles uniques sont **143 formes et 221 anciennes lectures**. L’occurrence classée « autre structure » et le chiffre de conjugaison nu produisent les mêmes sources, les mêmes index et les mêmes mesures natives. Leurs résultats ne doivent donc pas être additionnés comme deux récupérations distinctes.

| Copie diagnostique, pour chacun des deux essais | Formes cibles reconnues / 143 | Lectures anciennes exactes retrouvées / 221 | Encore manquantes | Autres lectures sur ces cibles |
| --- | ---: | ---: | ---: | ---: |
| Directive complète | 143 | 221 | 0 | 0 |
| Radical de présent isolé | 93 | 122 | 99 | 0 |

Dans les deux copies, le présent de l’en-tête passe de **zéro à une lecture directe attendue**, conserve ses **trois lectures antérieures** et n’en retire aucune. La comparaison enrichie confirme un ajout direct, sans nouvel ajout par préverbe. L’expansion complète contient une directive dérivée `:de:` de classe `are_vb` et un présent explicite `:vs:` de classe `conj1` ; la seconde copie contient uniquement le présent explicite. Aucun radical du témoin n’est copié.

La comparaison directe complet → présent sur les 143 cibles conserve **122 occurrences**, en retire **99**, n’en ajoute aucune et perd la reconnaissance de **50 formes**. Les multisets changent sur 54 formes. **Ces 99 suppressions sont toutes des lectures exactes du témoin ciblé** : deux au temps API non spécifié (0), 33 au futur (3), 46 au parfait (5), 12 au plus-que-parfait (6) et six au futur antérieur (7). Le chiffre 99 ne correspond donc pas uniquement à des parfaits. Les récupérations exactes des deux copies diffèrent effectivement ; l’essai complet reproduit aussi des lectures rendues possibles par sa dérivation productive.

Ces mesures ciblées ne qualifient pas le paradigme entier, la suppression des autres champs source, les parties passées ni l’absence de régression globale des copies. Le présent bénéficie d’un chiffre de conjugaison source explicite et fournit une piste pour un essai de récupération borné ; ses treize cellules source et une comparaison globale de ce nouvel essai restent à contrôler. Les 99 lectures supplémentaires du témoin retrouvées par la dérivation complète demandent leur propre justification source avant toute promotion.

Empreintes communes aux deux essais :

| Sortie privée | Directive complète | Présent isolé |
| --- | --- | --- |
| Source | `19ac70069dd6199fba2de17d01a00df08aa9297deb46b02bccf50fd3c3a6351d` | `fa0fb3904e5c43bf6c95ed1cffa7b6072408ddc985025ffbc51669b1732677c4` |
| Index verbal | `3a6bef5237ba8a6d5ad2876e09f8c4a99829906ed38f97819c7ded7f09b87553` | `00fb4438695a8de07da3c2b28f3ac91dd510cca1dccfa3eb8b31e0420e10bd8a` |
| Index secondaire | `e4aa833fd24c1271f2742a7af74560957818de1dee48a375d61292bf71ea5226` | `1401f2885c3a2d44df8bbaaf4774dbecb9c42952e5ff6d924c7821c3d6315b50` |

Les sondes privées conservent la position du champ source et ont des empreintes distinctes : `921c65aa5fe79a85d30ff596a5dc1d0bfabdee018376719462830cc02696863f` et `5299af6c2e2fbb7f87f56e061d62d54f939cb1da22f94ce45a2196f620134f58`. Le dossier des huit blocages garde `64804fe621a6376419636eb2558a4ebce2ad8e408b06b2efa0df415314dcee9c` ; les empreintes des diagnostics des sept chiffres terminaux restent reproduites. Les témoins nominaux et les quatre index finaux sont vérifiés inchangés. Aucun essai n’est promu au candidat ou à la production ; la PR reste en brouillon. [Critères et limites](https://github.com/defense-humanites/libmorpheus/blob/research/lexical-arbitration-2026-09-29/docs/latin-isolated-field-native-probe.md).


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


