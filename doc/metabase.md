# Metabase

Le système utilise deux aplications et deux BdD PostgreSQL:
 - une application django et une application Metabase. Metabase est déployé via scalingo à partir de https://github.com/Scalingo/metabase-scalingo
 - chaque BdD correspond à une application

L'application django alimente Metabase dans un schéma postgreSQL `impact` dédié dans la base de données de Metabase.

## Pré-requis

  - création manuelle de l'utilisateur `impact` depuis scalingo avec des droits d'écriture dans la base de données de Metabase
  - création manuelle du schéma `impact` depuis une console pgsql :

```
$ scalingo --app {METABASE_APP} pgsql-console
\c {METABASE_DATABASE} impact
CREATE SCHEMA impact AUTHORIZATION impact;
```

## Alimentation des données

L'alimentation des données est réalisée depuis l'application django avec la commande

```
impact/manage.py sync_db
```
