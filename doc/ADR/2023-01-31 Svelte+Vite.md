# Choix de Svelte + Vite pour le front

## Problèmatique

Jusqu'à maintenant tout le front était géré via le templating de django côté serveur et le design system de l'Etat (dsfr) pour les composants, qui suffisaient pour les besoins classiques (formulaires, affichage des pages statiques...).

Avec la notion d'indicateurs externes, on souhaite ajouter un comportement dynamique plus évolué sur les formulaires de la réglementation BDESE.
Au niveau de chaque indicateur l'utilisateur doit pouvoir sélectionner à l'aide d'un interrupteur que l'indicateur est un indicateur extene : l'utilisateur a déjà remplit par ailleurs cet indicateur dans un autre document et ne souhaite pas le remplir sur la plateforme.
Si l'utilisateur sélectionne un indicateur comme indicateur externe, le champ du formulaire correspondant à l'indicateur doit changer d'aspect et l'information doit être transmise lors de la soumission du formulaire. Cette information doit être retransmise ultérieurement dans le document pdf BDESE généré par la plateforme (l'utilisateur peut alors lui-même annexer les autres documents remplis ailleurs lorsqu'il transmet sa BDESE au CSE ou aux représentants du personnel).
Il s'agit d'un premier besoin "évolué", d'autres sont déjà envisagés (par exemple rendre dynamique le formulaire de création de compte avec appel intermédiaire à l'API recherche entreprise pour validation du siren).

## Solutions envisagées

- utiliser des morceaux de script js injectés sur les pages concernés via le templating
N'ajoute pas de dépendance.
Devient très vite peu maintenable quand les besoins côté front se multiplient et se complexifient.
Non testable.

- [htmx](https://htmx.org/)
D'après la documentation, la bibliothèque htmx donne accès à des fonctionnalités de navigateur modernes (Ajax, Websockets, transitions CSS, évènements envoyés par le serveur) directement en HTML, sans avoir à manipuler de javascript. Les développeurs utilisent des attributs HTML supplémentaires pour obtenir un contenu et des mises à jour dynamiques.
> L'approche htmx diffère des autres frameworks frontaux tels que Vue.js et React, où l'application côté client utilise JavaScript pour demander des informations au serveur et les recevoir au format JSON. Avec HTMX, lorsque vous faites une demande au serveur, le point de terminaison renverra du Html entièrement formé et mettra à jour une partie de la page. Vous pouvez intégrer HTMX à n'importe quelle technologie côté serveur puisque la logique d'application se produit sur le backend.
https://morioh.com/p/a780c4cb3ab2

htmx rencontre un certain succès parmi les développeurs django. D'autres startups d'état ont récemment commencé à l'utiliser (comme itou).
Plus testable que du script js pur car les routes utilisées par les composants htmx et leur rendu peuvent être testées comme les autres vues.
Très léger.
Permet d'ajouter du comportement htmx de façon incrémentale dans le projet en conservant le templating déjà en place.
Mais parait peu adapté pour notre premier cas d'application concernant les indicateurs externes : multiples routes à mettre en place (une par indicateur) ou paramétrage du composant peu évident, multiples requêtes serveurs (une par indicateur).

- [Svelte](https://svelte.dev/) + [Vite](https://vitejs.dev/)
Svelte est un framework front moderne de plus en plus mature. On l'utilise déjà sur d'autres projets de Yaal Coop.
Testable.
Assez léger.
Associé à Vite, il permet d'ajouter du comportement dynamique géré par svelte de façon incrémentale dans le projet en conservant le templating déjà en place, via [l'intégration Backend](https://vitejs.dev/guide/backend-integration.html). Une librairie [django-vite](https://github.com/MrBin99/django-vite) existe déjà pour l'intégration avec django.
Rend possible un basculement en douceur vers une séparation complète entre le serveur (back) et le front du projet si celui-ci continue d'évoluer et se complexifier.
Sur notre premier cas d'application concernant les indicateurs externes : n'ajoute pas de route côté serveur, utilise la route existante de soumission du formulaire en gérant dynamiquement la valeur d'un champ supplémentaire correspondant aux indicateurs externes sélectionnés.

- Autres frameworks front (React, VueJS...)
Frameworks plus anciens/matures que Svelte, avec une plus grande communauté existante.
Testables.
Plus lourds et moins performants que Svelte.
Expérience développeur moins agréable, courbe d'apprentissage plus raide.
[Comparaison Svelte, Angular, React, VueJS](https://javascript-conference.com/blog/svelte-vs-angular-vs-react-vs-vue-who-wins/)

## Choix

Svelte pour l'évolution facilitée et notre connaissance préalable.
