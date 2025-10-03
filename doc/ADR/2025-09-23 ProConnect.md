# Intégration de ProConnect au Portail RSE

## Problématique

La gestion technique de l'identité des utilisateurs et de leur rattachement à une ou plusieurs entreprises est actuellement intégralement implémentée dans le Portail RSE.

La responsabilité d'une identification correcte et des aspects de sécurité afférents incombe donc au Portail RSE.

Il est possible de déporter certaines des problèmatiques d'identification vers des prestataires tiers, permettant :
- une simplification du code.
- une amélioration de la sécurité,
- une délégation de responsabilité de la gestion de cette partie.

### ProConnect

Dans un souci de simplification et de délégation, la gestion de l'identifiaction et du rattachement des utilisateurs peut être déportée vers un autre service de l'état conçu à ces fins : [ProConnect](https://www.proconnect.gouv.fr/).

Utiliser un *fournisseur d'identité* (FI) tiers ou devenir *fournisseur de service* (FS) est généralement reconnu comme une bonne pratique en terme de sécurité et se généralise dans le développement des produits de l'écosystème beta.gouv.fr.

Sur le plan technique, la gestion des mots de passe et le choix d'une entreprise pour la session courante sont déportés vers ProConnect.

L'application du Portail garde la responsabilité de la *gestion des droits* (RBAC) qui vient se greffer sur les données d'identification fournies par ProConnect.

### Utilisation conjointe avec le système d'identification actuel

Pour assurer une expérience utilisateur aussi fluide que possible, l'actuelle solution d'identification (fournie par Django) est dans *un premier temps* conservée pour permettre aux utilisateurs *déjà inscrits* de pouvoir se connecter.

ProConnect assurera l'identification

Un nouvel utilisateur ne pourra par contre plus créer de compte sur le Portail RSE via Django : l'identification via ProConnect sera la seule option possible pour une connexion initiale.

## Solution envisagée

Le choix du prestataire d'identité est fixé (ProConnect), mais pas celui de la librairie technique permettant une connexion à ProConnect via [OIDC](https://openid.net/developers/how-connect-works/).

### 1. mozilla-oidc-connect

Github : https://github.com/mozilla/mozilla-django-oidc

Une librairie fournie par Mozilla au code relativement concis, lisible et léger.

Satisfait *largement* aux besoins de connexion via un FS/FI OIDC, avec quelques problèmes mineurs (listés en *issues*) dans un contexte ProConnect et facilement contournables.

Dans un cas idéal, aucun code n'est nécessaire pour utiliser cette librairie, la totalité de la configuration étant possible via un large éventail de `settings` Django.

Il s'agit aussi d'un projet qui a largement été utilisé par des produits *beta* pour leur connexion à ProConnect.

Son gros défaut reste une maintenance très réduite et l'absence de prise en compte de certaines PR pouvant faciliter la connexion à ProConnect et une plus grande compatibilité avec la spécification OIDC.

### 2. django-lasuite

Github : https://github.com/suitenumerique/django-lasuite

Ce projet est largement basé sur `mozilla-django-oidc` pour la partie connectique OIDC, qu'il reprends en corrigeant certains bugs bloquant en attente de correction et surtout en fournissant *une version adaptée spécifiquement à ProConnect*.

Il est constitué d'autres outils permettant d'autres action dans le cadre de l'implémentation d'une connexion OIDC, mais qui ne sont pas pertinents dans notre cas d'utilisation.

Comme `mozilla-django-oidc`, il est presque entièrement configurable via les `settings` Django.

Seules quelques adaptations mineures au contexte peuvent nécessiter la surcharge de certaines méthodes du `backend` d'identification fourni.

Le projet est activement maintenu par l'équipe de *la Suite Numérique*.

### 3. Django OAuth Toolkit

Github : https://github.com/django-oauth/django-oauth-toolkit

Projet de l'équipe JazzBand, il se concentre sur OAuth et dispose d'une bonne conformité aux standards (rfc) et plus d'une certaine popularité.

Il est par contre plus complexe à mettre en oeuvre que les deux précédents et est plus centré sur OAuth que OIDC.

## Choix

- L'absence de maintenance de `mozilla-django-oidc` l'élimine d'office, malgré ses qualités,
- `Django OAuth Toolkit` est un bon produit, mais étonnament assez peu utilisé chez beta.gouv.fr,
- `django-lasuite` est vite devenu une référence au sein de beta.gouv.fr de part son adaptation aux contraintes et spécificités de ProConnect.

**choix** : `django-lasuite`
qui allie un code léger, complètement utilisable par le biais de la configuration Django dans la majorité des cas et reprends à son compte tous les avantages de `mozilla-django-oidc` avec une maintenance suivie et une parfaite adaptation au contexte ProConnect.
