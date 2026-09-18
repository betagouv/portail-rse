# Metabase

Le Portail RSE utilise trois applications Scalingo associées chacune à une base de données PostgreSQL :
 - une application Django, déployée via Scalingo à partir de ce repo
 - une application Metabase, déployée via Scalingo
 - une BdD dédiée (Dedicated Resources) portail-rse-metabase-production-data-dr servant uniquement pour sa base de données PostgreSQL associée (Scalingo ne permet pas d'avoir plusieurs bdd associées à une seule application)

Metabase n'a pas d'accès à la base de données de l'application Django (cf l'ADR [2023-02-08 Metabase](ADR/2023-02-08%20Metabase)).
C'est l'application Django elle-même qui alimente la base de données séparée Metabase-data dans un schéma postgreSQL `portail_rse` dédié.


## Pré-requis

### Base de données dédiée

- [créer une base dédiée](https://doc.scalingo.com/databases/postgresql/dedicated-resources/getting-started/provisioning)
- [configurer la connexion réseau](https://doc.scalingo.com/databases/postgresql/dedicated-resources/getting-started/accessing#allowing-scalingo-apps-to-reach-a-dedicated-resources-database)

### Configuration de la base de données

Dans la base de données de Metabase-data :
  - création manuelle de l'utilisateur `metabase` depuis l'interface de scalingo avec des droits de lecture (read only)
  - création manuelle de l'utilisateur `portail_rse` depuis l'interface de scalingo avec des droits d'écriture
  - création manuelle du schéma `portail_rse` depuis une console pgsql :

```
$ scalingo --region osc-secnum-fr1 --app {PRODUCTION_APP} bash
$ psql {postgres://ADMIN_DATABASE_URL}
CREATE SCHEMA portail_rse AUTHORIZATION portail_rse;
```
  - définition des droits d'accès en lecture de l'utilisateur `metabase` sur les tables du schéma `portail_rse` :

```sql
GRANT USAGE ON SCHEMA portail_rse TO metabase;
GRANT SELECT ON ALL TABLES IN SCHEMA portail_rse TO metabase;
ALTER DEFAULT PRIVILEGES FOR ROLE portail_rse IN SCHEMA portail_rse GRANT SELECT ON TABLES TO metabase;
```

Avec le compte portail_rse
```sql
ALTER ROLE portail_rse SET search_path TO portail_rse;
```

Avec le compte metabase
```sql
ALTER ROLE metabase SET search_path TO portail_rse;
```

Les deux commandes précédentes sont nécessaires avec l'utilisation d'une base de données dédiées (dedicated resources).
En effet, le paramètre `currentSchema=portail_rse` qui était utilisé dans `METABASE_DATABASE_URL` n'est pas passé correctement.
(cela fonctionnait avec une app classique Scalingo.) Il faut donc définir quel est le schéma à utiliser d'une autre manière.


Dans l'application Django :
  - présence de la variable d'environnement `METABASE_DATABASE_URL` contenant les informations de connexion à la base de données de Metabase-data avec l'utilisateur `portail_rse`
  - création automatique des tables dans la base de données de Metabase via la commande de migration de django :

```
scalingo --app {DJANGO_APP} run python3 impact/manage.py migrate metabase --database metabase
```

Dans l'application Metabase :
  - ajout de la source de données `Portail RSE` depuis l'interface de Metabase configurée avec l'utilisateur `metabase` et seulement le schéma `portail_rse`. Le plus simple est de fournir l'URL posgresql:// de l'utilisateur `metabase`.


## Alimentation des données

L'alimentation des données peut être réalisée manuellement depuis l'application Django.

### Synchronisation depuis les API externes et Portail RSE -> Metabase

```
scalingo --app {DJANGO_APP} run scripts/sync_metabase.sh
```

### Synchronisation Portail RSE -> Metabase uniquement

```
scalingo --app {DJANGO_APP} run python3 impact/manage.py sync_metabase
```

Des paramètres permettent de ne faire qu'une partie de la synchronisation Portail RSE -> Metabase.

La synchronisation totale est programmée pour se lancer automatiquement via un cron toutes les nuits à minuit.


## Suppression manuelle des données

En cas de besoin :

```
$ scalingo --app {METABASE_DATA_APP} pgsql-console
\c {METABASE_DATA_DATABASE} portail_rse
DROP SCHEMA portail_rse CASCADE;
```

Cela supprime le schéma, il faut donc le recréer ensuite et attribuer à nouveau les droits d'accès à l'utilisateur `metabase`.

## Mise à jour de Metabase

Les versions disponibles sont visibles sur https://github.com/metabase/metabase/releases
La doc relative au support des versions est disponible sur https://www.metabase.com/version-support

Pour modifier la version de Metabase il faut :
  - déclencher un backup manuel de la bdd pour rollback au cas où la mise à jour se passe mal et noter la version de metabase actuelle
  - mettre à jour la version souhaitée dans la variable d'environnement `METABASE_VERSION` de l'application Metabase sur Scalingo
  - faire un nouveau déploiement (comme indiqué dans [la documentation de Scalingo](https://doc.scalingo.com/platform/getting-started/getting-started-with-metabase#updating-metabase))

  ```
  scalingo --app my-app deploy https://github.com/Scalingo/metabase-scalingo/archive/refs/heads/master.tar.gz
  ```

Si la mise à jour échoue :
  - restorer le dernier backup en suivant [la procédure de restore de scalingo depuis un container One-Off](https://doc.scalingo.com/databases/postgresql/shared-resources/guides/restoring#from-a-one-off-container)
  - redéployer l'ancienne version de metabase
