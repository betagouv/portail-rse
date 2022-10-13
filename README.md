# Plateforme Impact

https://beta.gouv.fr/startups/plateforme.impact.html


## développement local

Créer le fichier de variable d'environnement `.env` à partir du fichier d'exemple `.env.example`

```
make install
make run
```

Il est nécessaire d'installer le paquet système `libpq-dev` pour avoir `pg_config`.


## migration en recette


```
scalingo --app ${PROJET} run python3 impact/manage.py migrate
```

Pour un migration en local, voir le `Makefile`.

### suppression des données

```
$ scalingo --app ${PROJET} db-tunnel SCALINGO_POSTGRESQL_URL

# dans un autre terminal:
$ scalingo --app ${PROJET} pgsql-console
puis:
drop owned by ${PROJET}_3273;
```