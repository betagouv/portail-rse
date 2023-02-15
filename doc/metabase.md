# Metabase

Le projet Impact utilise trois aplications Scalingo associées chacune à une base de données PostgreSQL :
 - une application Django, déployée via Scalingo à partir de ce repo
 - une application Metabase, déployée via Scalingo à partir de https://github.com/Scalingo/metabase-scalingo
 - une application vide Metabase-data servant uniquement pour sa base de données PostgreSQL associée (Scalingo ne permet pas d'avoir plusieurs bdd associées à une seule application)

Metabase n'a pas d'accès à la base de données de l'application Django (cf l'ADR [2023-02-08 Metabase](ADR/2023-02-08%20Metabase)).
C'est l'application Django elle-même qui alimente la base de données séparée Metabase-data dans un schéma postgreSQL `impact` dédié.


## Pré-requis

Dans la base de données de Metabase-data :
  - création manuelle de l'utilisateur `metabase` depuis l'interface de scalingo avec des droits de lecture (read only)
  - création manuelle de l'utilisateur `impact` depuis l'interface de scalingo avec des droits d'écriture
  - création manuelle du schéma `impact` depuis une console pgsql :

```
$ scalingo --app {METABASE_APP} pgsql-console
\c {METABASE_DATABASE} impact
CREATE SCHEMA impact AUTHORIZATION impact;
```
  - définition des droits d'accès en lecture de l'utilisateur `metabase` sur les tables du schéma `impact` :

```
GRANT USAGE ON SCHEMA impact TO metabase;
GRANT SELECT ON ALL TABLES IN SCHEMA impact TO metabase;
ALTER DEFAULT PRIVILEGES IN SCHEMA impact GRANT SELECT ON TABLES TO metabase;
```

Dans l'application Django :
  - présence de la variable d'environnement `METABASE_DATABASE_URL` contenant les informations de connexion à la base de données de Metabase-data avec l'option `currentSchema=impact`
  - création automatique des tables dans la base de données de Metabase via la commande de migration de django :

```
scalingo --app {DJANGO_APP} run python3 impact/manage.py migrate metabase --database metabase
```

Dans l'application Metabase :
  - ajout de la source de données `Impact` depuis l'interface de Metabase configurée avec l'utilisateur `metabase` et seulement le schéma `impact`


## Alimentation des données

L'alimentation des données peut être réalisée manuellement depuis l'application Django avec la commande sync_metabase :

```
scalingo --app {DJANGO_APP} run python3 impact/manage.py sync_metabase
```

Elle est programmée pour se lancer automatiquement via un cron toutes les nuits à minuit.

## Suppression manuelle des données

En cas de besoin :

```
$ scalingo --app {METABASE_APP} pgsql-console
\c {METABASE_DATABASE} impact
DROP SCHEMA impact CASCADE;
```

Cela supprime le schéma, il faut donc le recréer ensuite et attribuer à nouveau les droits d'accès à l'utilisateur `metabase`.
