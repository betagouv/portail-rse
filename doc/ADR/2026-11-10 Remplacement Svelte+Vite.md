# Remplacement de Svelte + Vite par du JS vanilla

Remplace l'ADR [Choix de Svelte + Vite pour le front](2023-01-31%20Svelte+Vite.md).

## Problématique

Svelte + Vite avait été choisi pour gérer les indicateurs externes de la BDESE, en anticipant d'autres besoins dynamiques côté front.

Depuis, le comportement dynamique du projet est principalement géré avec [htmx](https://htmx.org/), directement dans les templates django.
Svelte n'était plus utilisé que pour quelques petits composants :

- l'interrupteur des indicateurs externes de la BDESE,
- l'affichage conditionnel de champs dans les formulaires de qualification et d'anticipation,
- la validation du mot de passe.

Maintenir Svelte et Vite pour ces composants implique une chaîne de compilation dédiée (Vite, django-vite, dépendances npm), un processus supplémentaire en développement et deux façons différentes d'ajouter du comportement dynamique.

## Solutions envisagées

- conserver Svelte + Vite
Aucun travail de migration.
Oblige à garder une chaîne de compilation et des dépendances coûteuses à maintenir pour peu de composants.

- réécrire les composants avec htmx
Cohérent avec le reste du projet.
Inutile pour des comportements purement locaux à la page (affichage/masquage de champs, validation du mot de passe) qui ne nécessitent pas d'échange avec le serveur.

- réécrire les composants en JS vanilla
Pas de dépendance ni de compilation : les scripts sont servis directement comme fichiers statiques.
Les scripts restent courts et sont pilotés par des attributs `data-*` dans les templates.
Les attributs générés par les templates peuvent être testés comme les autres vues.

## Choix

- JS vanilla pour les comportements locaux à la page
- HTMX pour tout ce qui nécessite un échange avec le serveur
- Svelte, Vite et django-vite sont supprimés du projet

Si des interactions complexes dans le futur surviennent, elles seront faites soit avec HTMX, soit en JS.
