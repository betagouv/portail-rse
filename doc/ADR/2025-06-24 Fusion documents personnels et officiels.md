# Fusion des documents BDESE et Rapport CSRD personnels et officiels

## Problèmatique

Avec la mise en place d'une première version d'un système de droit pour permettre la collaboration d'utilisateurs d'une même entreprise (cf [ADR 2025-05-22 Invitation](./2025-05-22%20Invitation.md)), la notion de documents personnels et officiels (cf [ADR 2023-03-01 Habilitation](./2023-03-01%20Habilitation.md)) est devenue obsolète. Dès qu'un utilisateur est personnellement invité sur l'entreprise par un propriétaire de l'entreprise, il est logique qu'il soit habilité à travailler sur les mêmes documents que les autres utilisateurs de l'entreprise et non pas sur une version personnelle.

La confirmation de l'habilitation et les documents personnels deviennent dépréciés, mais il faut gérer l'existant (les entreprises qui possèdent actuellement plusieurs utilisateurs et plusieurs documents personnels concurrents).

## Solutions envisagées

### 1. Suppression des documents personnels

On supprime tous les documents personnels. Les utilisateurs doivent créer de nouveaux documents partagés depuis zéro.

Très simple et rapide mais des données sont perdues.

### 2. Fusion des documents personnels manuelle

On demande (via le support) à tous les utilisateurs concernés quels documents doivent être conservés pour devenir les documents officiels partagés de l'entreprise.

Il y a beaucoup d'utilisateurs concernés (même si les documents sont dans les faits très peu remplis), peut être pas tous joignables aujourd'hui. Cela va prendre du temps.
De plus, de nouveaux documents personnels peuvent être créés dans l'intervalle à moins de gérer les deux systèmes en parallèle dans le code : les documents personnels pour les anciens documents créés, les documents officiels pour les nouveaux. Lourd et complexe.

### 3. Fusion des documents personnels automatique

On choisit quelques critères pertinents (état d'avancement, date de dernière modification) pour permettre de sélectionner le meilleur candidat des documents personnels qui deviendra le document officiel partagé lors d'une migration automatique de données effectuée lors de la mise en place de la gestion des droits. On garde en base de données tous les rapports personnels mais ils ne sont plus accessibles par les utilisateurs.

Plus rapide car on est autonome.
On est capable de retrouver un ancien document personnel pour le rendre officiel si nécessaire a posteriori (suite à une demande au support par exemple).
On conserve dans le code un minimum de références aux propriétaires de documents/documents personnels pour afficher aux utilisateurs uniquement les documents officiels (en excluant les documents personnels) et pour être capable de faire rapidement l'inversion d'un rapport officiel et personnel suite à une demande au support.

## Choix

Choix 3 : pour le compromis entre vitesse/complexité sans perte de données définitive. Une intervention au support est toujours possible pour inverser un rapport personnel et officiel. A terme (après un délai suffisant à déterminer) on pourra supprimer tous les rapports personnels et terminer de nettoyer le code pour supprimer définitivement la notion de document personnel.
