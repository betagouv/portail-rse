# Plateforme Impact

https://beta.gouv.fr/startups/plateforme.impact.html


## développement local

Installer [`pipenv`](https://pypi.org/project/pipenv/)

Créer le fichier de variable d'environnement `.env` à partir du fichier d'exemple `.env.example`

```
make install
make run
```

Il est nécessaire d'installer le paquet système `libpq-dev` pour avoir `pg_config`.

Pour générer les nouvelles migrations éventuelles et les appliquer :

```
make migrations
make migrate
```

Exécuter les tests avec :

```
make test
```

Pour activer l'intégration avec Sentry, il est nécessaire de renseigner la variable d'environnement SENTRY_DSN

## migration en recette


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


### suppression des données

Pour supprimer toutes les données en recette :

```
scalingo --app ${PROJET} pgsql-console
drop owned by ${PROJET}_3273;
```

Penser à créer à nouveau le super utilisateur une fois l'application redéployée/les migrations rejouées avec :

```
scalingo --app ${PROJET} run python3 impact/manage.py createsuperuser
```
