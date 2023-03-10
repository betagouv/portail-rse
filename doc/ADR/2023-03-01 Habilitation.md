# Différenciation des BDESE selon les habilitations des utilisateurs

## Besoin

Il faut différencier les BDESE entre un utilisateur habilité (validé par l'entreprise comme pouvant avoir accéder et modifier les informations de l'entreprise) et un utilisateur non habilité.

Un compte utilisateur non habilité peut :
 - accéder aux données publiques uniquement ;
 - tester sans valider la déclaration (lorsque le module de déclaration/transmission/publication existe) ;
 - accéder à ses brouillons mais pas à ceux des autres comptes utilisateurs de l’entreprise ;

Un compte utilisateur non habilité ne dispose d'aucun droit sur le compte entreprise utilisatrice.

Un compte utilisateur habilité peut :
 - accéder aux données publiques et privées ;
 - accéder et valider la déclaration ; s'il y a plusieurs utilisateurs habilités, ils partagent et modifient la même déclaration.
 - modifier les données de l'entreprise utilisatrice.

## Solutions envisagées


### 1. BDESE_50_300 et BDESE_300 deviennent des modèles abstraits

Pour chacune, 2 nouveaux modèles qui héritent du modèle abstrait : PersonalBDESE et EntrepriseBDESE
PersonalBDESE a un attribut user en plus, qui ne peut pas être null
2 tables différentes, 2 objets différents, 2 requêtes
Il faut savoir où on veut chercher et une méthode pour faire l'aiguillage (qui existe un peu déjà avec _get_or_create_bdese)
On peut conserver en base la personnelle quand on devient habilité (pas de perte de données), on peut revenir en arrière.
Il faut une migration.
Cette migration cause des problèmes dans les tests.

### 2. une seule table, deux managers différenciés

On garde nos modèles actuels, on ajoute l'attribut user qui peut être null
1 seule table, 1 seule requête avec un argument user qui peut être None
On peut ajouter des custom managers qui surchargent `get_queryset` pour filtrer directement les types qu'on veut
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
Quand on devient habilité la version personnelle est transformé en officielle et on ne peut pas revenir dans l'autre sens.

### 3. une seule table, deux managers différenciés et deux proxys

Choix 2 et des modèles proxy PersonalBDESE et EntrepriseBDESE pour accéder de manière plus naturelles aux objets. Les proxy s'appuient sur les managers pour filtrer les objets à prendre en compte.

Un peu plus de code pour obtenir une interface plus intuitive.

1 seule table, 1 seule requête, 2 objets différents


## Choix

choix 3 « une seule table, deux managers différenciés et proxys »

Quelques fonctions ont été ajoutées en plus pour avoir une interface cohérente avec le métier. Comme les managers et proxys, elles abstraient la réalité de la base de donnée.
