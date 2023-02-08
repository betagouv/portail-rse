# Metabase

Le projet Impact utilise deux aplications associées chacune à une base de données PostgreSQL :
 - une application Django, déployée via Scalingo à partir de ce repo
 - et une application Metabase, déployée via Scalingo à partir de https://github.com/Scalingo/metabase-scalingo

Metabase n'a pas d'accès à la base de données de l'application Django.
C'est l'application Django qui alimente la base de données de Metabase dans un schéma postgreSQL `impact` dédié.


## Pré-requis

Dans la base de données de Metabase :
  - création manuelle de l'utilisateur `metabase` depuis l'interface de scalingo avec des droits de lecture (read only)
  - création manuelle de l'utilisateur `impact` depuis l'interface de scalingo avec des droits d'écriture
  - création manuelle du schéma `impact` depuis une console pgsql :

```
$ scalingo --app {METABASE_APP} pgsql-console
\c {METABASE_DATABASE} impact
CREATE SCHEMA impact AUTHORIZATION impact;
```

Dans l'application Django :
  - présence de la variable d'environnement `METABASE_DATABASE_URL` contenant les informations de connexion à la base de données de Metabase avec l'option `currentSchema=impact`
  - création automatique des tables dans la base de données de Metabase via la commande de migration de django :

```
scalingo --app {DJANGO_APP} run python3 impact/manage.py migrate metabase --database metabase
```

Dans la base de données de Metabase :
  - définition des droits d'accès en lecture de l'utilisateur `metabase` sur les tables du schéma `impact` :

```
GRANT USAGE ON SCHEMA impact TO metabase;
GRANT SELECT ON ALL TABLES IN SCHEMA impact TO metabase;
```

Dans l'application Metabase :
  - ajout de la source de données `Impact` depuis l'interface de Metabase configurée avec l'utilisateur `metabase` et seulement le schéma `impact`


## Alimentation des données

L'alimentation des données est réalisée depuis l'application Django avec la commande sync_metabase :

```
scalingo --app {DJANGO_APP} run python3 impact/manage.py sync_metabase
```


## Suppression manuelle

```
$ scalingo --app {METABASE_APP} pgsql-console
\c {METABASE_DATABASE} impact
DROP SCHEMA impact CASCADE;
CREATE SCHEMA impact AUTHORIZATION impact;
quit
```
