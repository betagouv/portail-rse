# Contenus statiques avec Sites-Faciles

## Problématique

Faciliter le remplissage de contenu statique sans dépendre de compétences de développement pour :
1. fournir des réglementations et infos visant directement le public
2. fournir un contenu pour le référencement

## Solutions mises en place

### 1. Tout le monde peut faire des PR

Une première étape a été de montrer comment faire des modifications directement sur le code statique en ayant un compte Github. Les développeurs vérifient les diffs des PR pour éviter les accidents. Validation des modifications sur la recette.
Des modifications ont bien été réalisées mais ça n'est pas le plus simple pour des non-devs.

Cela répond surtout au premier besoin.

### 2. Sites-faciles

Le projet [sites-faciles](https://sites-faciles.beta.numerique.gouv.fr/) promet de « Créer, publier, et gérer le site de votre administration en quelques clics ».
Il est basé sur Wagtail, qui est un CMS basé sur Django. Il est paramétré pour fournir automatiquement un thème DSFR.
C'est un socle technique déjà utilisé par l'équipe technique pour le service principal.

Sites-faciles répond aux deux besoins.

### 3. Wordpress ou autres CMS

Cette solution n'a pas été vraiment évaluée vu l'intérêt de sites-faciles.

## Choix

Choix 2 : "Sites-faciles"

Il est toujours possible au reste de l'équipe de réaliser des PR mais la majorité du contenu devrait être mise sur sites-faciles donc son intérêt devrait s'amenuiser avec le temps.
