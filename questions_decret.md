1°  A   a)  i   (I) signifie-t-il qu'il faut remplir pour chaque indicateur où ce (I) apparait (comme par exemple le premier, mais de nombreux autres) une donnée pour chaque structure de qualification ? Comment définit-on cette classification ? Si cette classification peut être librement définie dans l'entreprise, au niveau de la BDESE, comment espère-t-on récupérer les infos par catégorie via API ?

> I.-Une structure de qualification détaillée, en trois ou quatre postes minimum, est requise. 
> Il est souhaitable de faire référence à la classification de la convention collective, de l’accord d’entreprise et aux pratiques habituellement retenues dans l’entreprise
> A titre d’exemple la répartition suivante peut être retenue : cadres ; employés, techniciens et agents de maîtrise (ETAM) ; et ouvriers.

                sexe : homme/femme/autre ?
                âge : on force les catégories ? -25, 25-35, 35-45, 45-55, 55+
                ancienneté : faible, moyenne, forte ?
                qualification détaillée : sous catégorie hommes et femmes ?

> Une structure de qualification détaillée en cinq ou six postes minimum est requise. Il est souhaitable de faire référence à la classification de la convention collective, de l’accord d’entreprise et aux pratiques habituellement retenues dans l’entreprise.
> A titre d’exemple, la répartition suivante des postes peut être retenue : cadres ; techniciens ; agents de maîtrise ; employés qualifiés ; employés non qualifiés ; ouvriers qualifiés ; ouvriers non qualifiés. Doivent en outre être distinguées les catégories femmes et hommes.

1°  A   b)  par catégorie professionnelle = (I) ?
1°  A   b)   ii  Comment on distingue les différents systèmes légaux et conventionnels de toute nature ?

1°  A   d)  Evolution du nombre de stagiaires : a quoi ça correspond ? Pour l'instant on ne met rien (il y a déjà le nombre de stagiaires)
Puis à nouveau dans e) i- on a
Nombre de stagiaires (II) ;
Nombre d'heures de stage (II) :
-rémunérées ;
-non rémunérées.
Décomposition par type de stages à titre d'exemple : adaptation, formation professionnelle, entretien ou perfectionnement des connaissances ;

1°  A   f)  Conditions de travail : Que met-on ? Champ libre ?
1°  A   f)  i   Est-ce normal de demander le "Nombre d'accidents avec arrêts de travail divisé par nombre d'heures travaillées" puis le "Nombre d'accidents de travail avec arrêt × 106 divisé par nombre d'heures travaillées" ?
                "Nombre d'incapacités permanentes (partielles et totales) notifiées à l'entreprise au cours de l'année considérée (distinguer français et étrangers)" : français et etrangers ?
1°  A   f)  iii La dénomination des maladies pro est-elle réglementée/connue à l'avance ?
1°  A   f)  v   Au titre du présent code = code du travail ?
1°  A   f)  vii Faut-il distinguer par seuils associés aux facteurs de risques pro ?
1°  A   f)  viii Pourquoi le premier indicateur parle de "personnes" et les autres de "salariés" ? Le premier comprend les presta, stagiaires... ? 
1   A   f)  xi Part du temps consacré à l'analyse et à l'intervention = une seule part ou deux ?

1°  B   a)  comment se mesure l'évolution ? c'est un nombre ? une description ?
1°  B   b)  c'est un montant ?
1°  B   c)  comment se mesure l'évolution ? description ?

2°  I   A   a)  réparation par catégorie professionnelle: avec la définition des CSP de l'INSEE?
                https://www.insee.fr/fr/metadonnees/definition/c1758

                dans la page, il est indiqué:
> Concernant la notion de catégorie professionnelle, il peut s'agir de fournir des données distinguant :
> a) Les ouvriers, les employés, techniciens, agents de maîtrise et les cadres ;
> b) Ou les catégories d'emplois définies par la classification ;
> c) Ou toute catégorie pertinente au sein de l'entreprise.

2°  I   A   c) le nombre de congé : quel est l'unité à prendre en compte (le nombre de congés, le nombre de jours)
            e) répartition des effectifs  par niveau ou coefficient hiérarchique : quel sont les niveaux? coefficient hiérarchique?
2°  I   B   d) rémunération moyenne ou médiane mensuelle -> comment choisir
2°  I   D   "poste de travail": fournir une liste ?
            "expositions à des risques professionnels" -> liste de risques professionnnels ? des niveaux (par ex. faible, moyen, haut) ?
            "pénibilité": oui/non ? des niveaux ?
            "accidents de travail, accidents de trajet et maladies professionnelles" : 3 champs différents ou aggrégés ?
            "dénomination des maladies professionnelles" : permettre à l'utilisateur de remplir librement les maladies ?
            "maladies": champ libre pour lister des maladies non professionnelles ?


Doublon ?
1° A f : Nombre de journées d'absence pour accidents du travail et de trajet ou maladies professionnelles (I) ;
2° I D : nombre de journée d'absence pour accidents de travail, accidents de trajet ou maladies professionnelles ;