# Stockage des caractéristiques d'une entreprise par année

## Problématique

Certaines caractéristiques de l'entreprise permettent de déterminer à quelle réglementation l'entreprise est soumise (typiquement aujourd'hui : l'effectif et l'existence d'un accord concernant la BDESE au sein de l'entreprise).

Jusqu'à maintenant ces caractéristiques sont simplement enregistrées sur l'objet Entreprise. Elles sont systématiquement demandées à l'utilisateur (et pré-remplies quand les informations peuvent être connues et récupérées par API) lorsque l'utilisateur veut consulter les réglementations de son entreprise et que ces caractéristiques ne sont pas encore enregistrées.

Pourtant les valeurs de ces caractéristiques ne sont pas fixes et vont évidemment évoluer dans le temps. Le nombre et la nature de ces caractéristiques vont également évoluer au fur et à mesure de l'ajout de nouvelles réglementations basées sur des critères différents.

Il faut donc être capable de faire évoluer ces caractéristiques et s'assurer qu'elles sont à jour avant d'afficher les réglementations de l'entreprise.


## Solutions envisagées

### 1. Redemander aux utilisateurs et écraser les valeurs régulièrement

On peut par exemple stocker la date à laquelle les caractéristiques ont été renseignées et redemander à l'utilisateur tous les ans de les remplir à nouveau. On ne stocke alors pas l'historique de ces caractéristiques.

- Méthode la plus simple
- On perd de l'information. Se complique lorsque certaines réglementations se basent sur plusieurs années (par exemple le "Plan de vigilance" ou "l'Audit énergétique" qui s'appliquent lorsque des critères sont remplis pour deux exercices consécutifs).

### 2. Stocker à part ces caractéristiques et leur évolution

Déplacer ces champs dans un nouveau modèle lié à l'entreprise et ajouter un champ pour l'année de l'exercice considéré. Demander à l'utilisateur tous les ans de les remplir à nouveau.

- Méthode plus complexe. Nécessite la création d'un nouveau modèle et une migration.
- On conserve l'historique. Permet de savoir à quel moment une entreprise devient soumise (ou inversement n'est plus soumise mais l'a été) à une réglementation. Permet d'identifier facilement si une entreprise est soumise à une réglementation basée sur des critères qui s'appliquent pendant plusieurs exercices consécutifs.


## Choix

Choix 2 : "Stocker à part ces caractéristiques et leur évolution" pour la plus grande flexibilité permise, notamment dans le contexte où on ne connait pas encore toutes les réglementations présentes et à venir et donc leurs critères.

Nous avons créé un nouveau modèle `CaracteristiquesAnnuelles` pour stocker l'ensemble des valeurs annuelles permettant de savoir à quelles réglemntations est soumise une entreprise.

Nous avons ajouté une contrainte d'unicité en base sur le couple (Entreprise - Année) pour éviter de créer par erreur des doublons. Les méthodes `caracteristiques_annuelles(annee)` et `caracteristiques_actuelles()` sur le modèle `Entreprise` permettent de récupérer les caractéristiques souhaitées de l'entreprise.
