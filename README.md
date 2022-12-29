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


### suppression des données

```
scalingo --app ${PROJET} pgsql-console
drop owned by ${PROJET}_3273;
```
créer à nouveau le super utilisateur avec

```
scalingo --app ${PROJET} run python3 impact/manage.py createsuperuser
```
