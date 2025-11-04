[![test](https://github.com/betagouv/portail-rse/actions/workflows/test.yml/badge.svg)](https://github.com/betagouv/portail-rse/actions/workflows/test.yml)

# Portail RSE

## Liens utiles

Présentation du service :
https://beta.gouv.fr/startups/portail-rse.html

Site vitrine :
https://portail-rse.beta.gouv.fr

Service de gestion (correspond au code de ce dépôt) :
https://portail-rse.beta.gouv.fr

Il existe un service supplémentaire externe pour l'API d'analyse de documents.

## Développement local

### Installation du projet

- Installer [`pipenv`](https://pypi.org/project/pipenv/)
- Créer le fichier de variable d'environnement `.env` à partir du fichier d'exemple `.env.example`. Si nécessaire, il est possible d'activer l'intégration avec Sentry en local en renseignant la variable d'environnement `SENTRY_DSN`.
- Installer le projet avec :

```
make install
```

ℹ️ Il est nécessaire d'installer le paquet système `libpq-dev` pour avoir `pg_config`.


En cas de problème avec `pipenv`, il est possible de l'installer dans un environnement virtuel :

```shell
python3 -m venv venv
. ./venv/bin/activate
pip install pipenv
# puis exécuter les commandes au début de ce paragraphe
```


### Lancement en local

- Lancer le projet avec :

```
make migrate
make run
```

- Le service est disponible sur http://127.0.0.1:8000

- Pour lancer une commande du projet django en local :

```
pipenv run python3 impact/manage.py my_command
```


### Migration des données

Pour générer les nouvelles migrations éventuelles et les appliquer :

```
make migrations
make migrate
```


### Test et CI

- Exécuter les tests en local avec :

```
make test
```

- Formater le code. Le projet utilise [pre-commit](https://pre-commit.com/) pour vérifier le formattage du code automatiquement à chaque commit.
La cible `make install` l'installe directement.


## Migrations en recette

```
scalingo --app ${PROJET} run python3 impact/manage.py migrate
```

Cette commande est jouée automatiquement lors de tout déploiement.

Pour lister les migrations jouées en recette :

```
scalingo --app ${PROJET} run python3 impact/manage.py showmigrations
```

Pour défaire des migrations déjà appliquées en recette **avant** de déployer une branche où l'historique des migrations est différent/a changé (et ainsi éviter les exceptions de type InconsistentMigrationHistory au déploiement et d'avoir à supprimer toutes les données) :
https://docs.djangoproject.com/fr/4.1/ref/django-admin/#django-admin-migrate

```
scalingo --app ${PROJET} run python3 impact/manage.py migrate NOM_DE_L_APP_DJANGO NOM_DE_LA_DERNIERE_MIGRATION_A_LAQUELLE_ON_SOUHAITE_REVENIR
```


### Suppression des données

Pour supprimer toutes les données en recette :

```
scalingo --app ${PROJET} pgsql-console
drop owned by ${PROJET_USER};
```

Penser à créer à nouveau le super utilisateur une fois l'application redéployée/les migrations rejouées avec :

```
scalingo --app ${PROJET} run python3 impact/manage.py createsuperuser
```


## Consommation et mémoire en recette et production

Il est possible de connaître en temps réel la consommation CPU et mémoire avec la commande :

```
scalingo --app ${PROJET} stats

```
