# Mise en place d'invitation

## Problèmatique

Pour permettre aux utilisateurs d'une même entreprise de travailler ensemble dans le portail, une première version d'un système de droit est mis en place.
Tous les utilisateurs deviennent « propriétaires » de l'entreprise. Des droits d'écriture et lecture sont prévus dans une étape ultérieure.

Pour éviter qu'un nouvel utilisateur ne s'inscrive directement et obtienne automatiquement des droits d'administration, on veut :
 - bloquer toute nouvelle inscription sur l'entreprise s'il y a déjà au moins un propriétaire
 - ajouter un système d'invitation pour permettre l'arrivée de nouveaux membres

Plusieurs façons de réaliser le système d'invitation ont été envisagées.

## Solutions envisagées

### 1. Code contenant l'ensemble des informations

Lorsqu'un propriétaire fait une invitation, le lien d'invitation envoyé contient les informations pour créer le compte. Rien n'est créé en BdD.

Paramètres du lien : e-mail, entreprise, "proprietaire", date de l'invitation, hash d'authentification

L'invité arrive sur la page de création du compte, les informations sont préremplies grâce aux paramètres contenu dans le lien.

- si le compte n'existe pas : création du compte et devient propriétaire de l'entreprise
- si le compte existe et pas la relation avec l'entreprise :
  - si utilisateur connecté : devient propriétaire de l'entreprise
  - sinon : lui demander de se connecter
- si le compte existe et la relation avec l'entreprise existe aussi :
  - si utilisateur connecté : rediriger vers la page de l'entreprise et afficher un message de type "Déjà fait"
  - sinon : lui demander de se connecter

L'authentification peut se baser sur les fonctions sign() et verify() de la doc [Python](https://docs.python.org/3/library/hashlib.html#keyed-hashing) ou sur les tokens d'authentification de [django-sesame](https://pypi.org/project/django-sesame/).

### 2. Invitation en base de données

Lorsqu'un propriétaire fait une invitation, un objet Invitation est créé en base. Le lien d'invitation envoyé contient le minimum d'information pour retrouver l'invitation.

Quand l'invité tente de s'inscrire sur le portail, on vérifie en base si une invitation correspondante existe et n'est pas expirée. Dans ce cas, on crée le compte et supprime l'invitation en même temps. La cinématique reste similaire au cas 1.

- L'ensemble des propriétaires peut savoir qui a déjà été invité et quand.
- On peut voir le nombre d'invitation en cours dans l'admin django.


## Choix

Choix 2 : La possibilité d'afficher les invitations en cours/expirée aux propriétaires et le fait qu'on puisse aussi avoir de la visibilité sur les invitations l'ont emporté.
