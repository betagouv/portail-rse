Choix 1 :
BDESE_50_300 et BDESE_300 deviennent des modèles abstraits.
Pour chacune, 2 nouveaux modèles qui héritent du modèle abstrait : PersonalBDESE et EntrepriseBDESE
PersonalBDESE a un attribut user en plus, qui ne peut pas être null
2 tables différentes, 2 objets différents, 2 requêtes
Il faut savoir où on veut chercher et une méthode pour faire l'aiguillage (qui existe un peu déjà avec _get_or_create_bdese)

Choix 2 :
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
    personal = PersonalManager()
    official = OfficialManager()

BDESE.personal.all()  # retourne toutes les BDESE personnelles d'utilisateurs non habilités
BDESE.official.all()  # retourne toutes les BDESE officielles d'entreprises
```

Choix 3 :
Choix 2 + on ajoute un ou deux modèles proxy PersonalBDESE et EntrepriseBDESE
1 seule table, 1 seule requête, 2 objets différents
