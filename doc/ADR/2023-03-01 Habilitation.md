# Différenciation des BDESE selon les habilitations des utilisateurs

## Problématique

Aujourd'hui tout le monde peut créer un compte utilisateur facilement et le rattacher à une entreprise. Cet utilisateur a alors accès à la BDESE de l'entreprise.

Dans un premier temps on va garder la facilité de rattachement à une entreprise mais ajouter la notion de compte utilisateur habilité (validé par l'entreprise comme pouvant avoir accès et modifier les informations de l'entreprise) et utilisateur non habilité.

Un compte utilisateur non habilité peut :
 - accéder aux données publiques de l'entreprise uniquement ;
 - tester sans valider une déclaration (lorsque le module de déclaration/transmission/publication existe pour une réglementation) ;
 - accéder à ses brouillons mais pas à ceux des autres comptes utilisateurs de l’entreprise.

Un compte utilisateur habilité peut :
 - accéder aux données publiques et privées de l'entreprise ;
 - accéder et valider la déclaration ; s'il y a plusieurs utilisateurs habilités, ils partagent et modifient la même déclaration ;
 - modifier les données de l'entreprise.

Pour la réglementation BDESE cela se traduit par :

- un compte utilisateur non habilité peut remplir une BDESE personnelle ("brouillon") pour cette entreprise ;
- un compte utilisateur non habilité ne partage pas sa BDESE personnelle avec d’autres utilisateurs de l’entreprise. Chaque utilisateur non habilité de l’entreprise à accès uniquement à sa propre BDESE personnelle.
- les BDESE personnelles ne sont pas pré-remplies avec les données privées de l’entreprise, uniquement les données publiques ;
- un compte utiisateur habilité peut remplir une BDESE officielle, partagée avec tous les utilisateurs habilités de l’entreprise ;
- les BDESE officielles sont pré-remplies avec les données privées de l’entreprise ;

Techniquement il faut donc deux distinguer deux types de BDESE : personnelle et officielle.


## Solutions envisagées

### 1. BDESE_50_300 et BDESE_300 deviennent des modèles abstraits

Pour chacun, création de 2 nouveaux modèles qui héritent du modèle abstrait : PersonalBDESE et OfficialBDESE.
PersonalBDESE a un attribut user en plus, qui ne peut pas être null.
Pour chacun, 2 tables différentes, 2 objets différents, 2 requêtes différentes.

- Permet de vraiment séparer dans l'admin et le code les 2 types d'objets
- Il faut savoir où on veut chercher et une méthode pour faire l'aiguillage (qui existe un peu déjà avec `_get_or_create_bdese`).
- On peut conserver en base la BDESE personnelle quand on devient habilité (pas de perte de données), on peut revenir en arrière.
- Il faut une migration des tables existantes.

### 2. Une seule table, un seul objet et deux managers différenciés

On garde nos modèles BDESE_50_300 et BDESE_300 actuels, on ajoute simplement l'attribut user qui peut être null (dans le cas d'une BDESE officielle).
Pour chacun, 1 seule table, 1 seul objet, 1 seule requête avec un argument user qui peut être None.

- On peut ajouter des custom managers qui surchargent `get_queryset` pour filtrer directement les types qu'on veut :
```
class PersonalManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user__isnull=False)

class OfficialManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user__isnull=True)

class BDESE():
    personals = PersonalManager()
    officials = OfficialManager()

BDESE.personals.all()  # retourne toutes les BDESE personnelles d'utilisateurs non habilités
BDESE.officials.all()  # retourne toutes les BDESE officielles d'entreprises
```
- On peut conserver en base la personnelle quand on devient habilité (pas de perte de données), on peut revenir en arrière.
- Impossible de séparer vraiment dans l'admin les deux types d'objets (on peut simplement ajouter un filtre)

### 3. Une seule table, deux objets proxy et deux managers différenciés

Choix 2 auquel on ajoute des modèles proxy PersonalBDESE et OfficialBDESE. Les proxy s'appuient sur les managers pour filtrer les objets à prendre en compte.
Pour chacun des modèles BDESE_50_300 et BDESE_300 existants : 1 seule table, 2 objets proxy différents.

- Un peu plus de code que le choix 2
- Permet d'avoir des interfaces plus intuitives
- Permet de vraiment séparer dans l'admin les 2 types d'objets


## Choix

Choix 3 : « une seule table, deux objets proxy et deux managers différenciés » pour la séparation métier, notamment dans l'admin.

Le choix 1 qui avait été privilégiée au départ a été abandonné à cause de la migration nécessaire (renommage et suppression des modèles existants qui deviennent abstraits). Cette migration causait des problèmes dans les tests.

Quelques fonctions ont été ajoutées en plus pour avoir une interface cohérente avec le métier. Comme les managers et proxys, elles abstraient la réalité de la base de donnée.
