basé sur https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050/LEGISCTA000036411564?init=true&page=1&query=Article+R2312-9+-+Code+du+travail&searchField=ALL&tab_selection=all&anchor=LEGIARTI000045680845#LEGIARTI000045680845


1°  A   a)  i   (I) signifie-t-il qu'il faut remplir pour chaque indicateur où ce (I) apparait (comme par exemple le premier, mais de nombreux autres) une donnée pour chaque structure de qualification ? Comment définit-on cette classification ? Si cette classification peut être librement définie dans l'entreprise, au niveau de la BDESE, comment espère-t-on récupérer les infos par catégorie via API ?

prendre " cadres ; employés, ETAM ; et ouvriers"

> I.-Une structure de qualification détaillée, en trois ou quatre postes minimum, est requise. 
> Il est souhaitable de faire référence à la classification de la convention collective, de l’accord d’entreprise et aux pratiques habituellement retenues dans l’entreprise
> A titre d’exemple la répartition suivante peut être retenue : cadres ; employés, techniciens et agents de maîtrise (ETAM) ; et ouvriers.

sexe : homme/femme/autre ? prendre H/F

âge : on force les catégories ? -25, 25-35, 35-45, 45-55, 55+ | on garde ça

ancienneté : faible, moyenne, forte ? | -10, 10-20, 20-30 ans

qualification détaillée : sous catégorie hommes et femmes ? | prendre Niveau de diplôme  https://www.service-public.fr/particuliers/vosdroits/F199

> Une structure de qualification détaillée en cinq ou six postes minimum est requise. Il est souhaitable de faire référence à la classification de la convention collective, de l’accord d’entreprise et aux pratiques habituellement retenues dans l’entreprise.
> A titre d’exemple, la répartition suivante des postes peut être retenue : cadres ; techniciens ; agents de maîtrise ; employés qualifiés ; employés non qualifiés ; ouvriers qualifiés ; ouvriers non qualifiés. Doivent en outre être distinguées les catégories femmes et hommes.

1°  A   b)  par catégorie professionnelle = (I) ?

1°  A   b)   ii  Comment on distingue les différents systèmes légaux et conventionnels de toute nature ? | mettre champ libre

1°  A   d)  Evolution du nombre de stagiaires : a quoi ça correspond ? Pour l'instant on ne met rien (il y a déjà le nombre de stagiaires)   | évolution sur l'année
Si évolution par rapport à l'année précédente, on ne met pas un nouveau champ, on le calculera par rapport à l'année précédente ?

Puis à nouveau dans e) i- on a
> Nombre de stagiaires (II) ;

> Nombre d'heures de stage (II) :
> -rémunérées ;
> -non rémunérées.

Comme il y a (II), faut-il décomposer par catégorie pro détaillée ? Ou est-ce une erreur ?

> Décomposition par type de stages à titre d'exemple : adaptation, formation professionnelle, entretien ou perfectionnement des connaissances ;

On met un champ libre ?

1°  A   f)  Conditions de travail : Que met-on ? Champ libre ? | à enlever

1°  A   f)  i   Est-ce normal de demander le "Nombre d'accidents avec arrêts de travail divisé par nombre d'heures travaillées" puis le "Nombre d'accidents de travail avec arrêt × 106 divisé par nombre d'heures travaillées" ? | bizarre, question au ministere du travail

Quelle unité pour le taux de fréquence des accidents du travail et taux de gravité des accidents du travail (I) ? Est-ce que ce n'est pas plutôt à remplacer par les indicateurs suivants ? (Nombre d'accidents / Nombre d'heure travaillées, Nombre de journées perdues / Nombre d'heures travaillées) ? Et dans ce cas, faut-il ces indicateurs par catégorie pro ?

"Nombre d'incapacités permanentes (partielles et totales) notifiées à l'entreprise au cours de l'année considérée (distinguer français et étrangers)" : français et etrangers ? | faire "partiel fr", "partiel etranger", "total fr", "total etranger"

1°  A   f)  iii La dénomination des maladies pro est-elle réglementée/connue à l'avance ? | champ libre en attendant d'avoir une liste par secteur  https://www.ameli.fr/medecin/exercice-liberal/presciption-prise-charge/prise-charge-situation-type-soin/situation-patient-mp/maladies-professionnelles

1°  A   f)  v   Au titre du présent code = code du travail ? | code du travail + code rural

1°  A   f)  vii Faut-il distinguer par seuils associés aux facteurs de risques pro ?

1°  A   f)  viii Pourquoi le premier indicateur parle de "personnes" et les autres de "salariés" ? Le premier comprend les presta, stagiaires... ? | le premier peut compter les visiteurs

1   A   f)  xi Part du temps consacré à l'analyse et à l'intervention = une seule part ou deux ? | mettre deux champs

1°  B   a)  comment se mesure l'évolution ? c'est un nombre ? une description ? | un nombre

1°  B   b)  c'est un montant ? | oui

1°  B   c)  comment se mesure l'évolution ? description ? | champ libre

pour 2° voir sur resana, le décret joe_2019... indexegapro. les méthodes de calcul sont dans l'annexe 1.

2°  I   A   a)  réparation par catégorie professionnelle: avec la définition des CSP de l'INSEE?
                https://www.insee.fr/fr/metadonnees/definition/c1758

dans la page, il est indiqué:
> Concernant la notion de catégorie professionnelle, il peut s'agir de fournir des données distinguant :
> a) Les ouvriers, les employés, techniciens, agents de maîtrise et les cadres ;
> b) Ou les catégories d'emplois définies par la classification ;
> c) Ou toute catégorie pertinente au sein de l'entreprise.

2°  I   A   c) le nombre de congé : quel est l'unité à prendre en compte (le nombre de congés, le nombre de jours)

2°  I   A   e) répartition des effectifs  par niveau ou coefficient hiérarchique : quel sont les niveaux? coefficient hiérarchique?

2°  I   B   d) rémunération moyenne ou médiane mensuelle -> comment choisir

2°  I   D   "poste de travail": fournir une liste ?

"expositions à des risques professionnels" -> liste de risques professionnnels ? des niveaux (par ex. faible, moyen, haut) ?

"pénibilité": oui/non ? des niveaux ?  | mettre des niveaux (attendre résultat api DSN)  https://www.service-public.fr/particuliers/vosdroits/F15504

"accidents de travail, accidents de trajet et maladies professionnelles" : 3 champs différents ou aggrégés ?

"répartition des accidents par éléments matériels (28)" : champs aggrégés ou différents ? mêmes catégories que 1°A-f)ii ?

"dénomination des maladies professionnelles" : permettre à l'utilisateur de remplir librement les maladies ?

"maladies": champ libre pour lister des maladies non professionnelles ?

4°  A a)  indicateurs au choix -> on met tout et on laisse remplir ? | oui

4°  A a)  iv Charge salariale globale : pas d'indicateur de précisé | pas un probleme

4°  A b) rien de précisé | remplir "montant global des rémunération des rémunérations versées aux personnes les mieux rémunérées, le nombre de ces personnes étant de dix ou de cinq selon que l'effectif du personnel est ou non d'au moins deux cent cinquante salariés". peut-etre seulement les société anonymes. à voir

Doublon ?
- 1° A f : Nombre de journées d'absence pour accidents du travail et de trajet ou maladies professionnelles (I) ; | par catégorie
- 2° I D : nombre de journée d'absence pour accidents de travail, accidents de trajet ou maladies professionnelles ; | par sexe
