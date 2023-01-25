# Choix du stockage des champs BDESE par catégorie

## Problèmatique

De nombreux indicateurs obligatoires pour la BDESE sont à renseigner par catégorie professionnelle.

https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000045680845
> I.-Une structure de qualification détaillée, en trois ou quatre postes minimum, est requise.
> Il est souhaitable de faire référence à la classification de la convention collective, de l’accord d’entreprise et aux pratiques habituellement retenues dans l’entreprise
> A titre d’exemple la répartition suivante peut être retenue : cadres ; employés, techniciens et agents de maîtrise (ETAM) ; et ouvriers.

Parmi les contraintes, on souhaite que ce soit personnalisable par entreprise.
On souhaite aussi conserver une base SQL et l'ORM de Django.

## Solutions envisagées

- Utiliser un Model.ArrayField
https://github.com/django/django/blob/cb791a2540c289390b68a3ea9c6a79476890bab2/django/contrib/postgres/fields/array.py#L18
C'est un champ spécifique à Postgresql, non portable facilement sur d'autres bases (notamment sqlite pour le dev en local/tests...).
Il faut stocker à part les catégories car on ne stocke que les valeurs ordonnées.
On peut renommer facilement les catégories vu qu'elles sont à part (pour corriger une typo par exemple).
Par contre les catégories peuvent diverger, par exemple en cas d'ajout ou de suppression de catégorie.
Pour le rendu il existe forms.SplitArrayField qu'on peut utiliser directement.

- Utiliser un Model.JSONField
https://github.com/django/django/blob/0dd29209091280ccf34e07c9468746c396b7778e/django/db/models/fields/json.py#L16
Non spécifique à Postgresql.
On peut stocker les catégories avec les valeurs dans un dictionnaire.
Le renommage d'une catégorie (pour une typo par exemple) nécessite une migration de tous les champs exploitant ces catégories vu que l'information est dupliquée.
Les catégories peuvent évoluer plus facilement, par exemple en cas d'ajout ou de suppression.
Pour le rendu il faut créer un forms.MultiField personnalisé.

## Choix

Model.JSONField pour la portabilité et les modifications plus faciles
