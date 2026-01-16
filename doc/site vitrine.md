# Site vitrine

Fait avec Sites Conformes (ex-Sites Faciles).
Pour connaitre les raisons de ce choix, voir doc/ADR/2024-10-03 SitesFaciles.md

## Dépots git

Les développements amont se font sur https://github.com/numerique-gouv/sites-faciles
En tant que BetaGouv, nous n'avons pas de droits d'écriture sur ce dépôt. Il a donc été forké sur
https://github.com/betagouv/sites-faciles/

Nos modifications sont dans une branche spécifique `production-portail-rse`.

## Mises à jour

Il faut `rebase` la branche `production-portail-rse` sur un tag plus récent.

```
git rebase v1.14.0
```

Corriger les conflits le cas échéant.

Déployer en recette avec l'interface web de Scalingo.

Vérifier que la recette de Sites Faciles fonctionne.

Si c'est bon, déployer en production.
