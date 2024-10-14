Processus de travail

1. création d'une PR en draft indiquant la solution technique envisagée avec un lien vers la carte Trello dans la colonne "En cours" indiquant le besoin. Eventuelle discussion technique et validation de la solution choisie. La solution pourra évoluer lorsqu'on se rendra compte de problèmes inattendus lors de l'implémentation.
2. développement du code sur la nouvelle branche
3. demande d'une revue de code via la PR. On entre dans une boucle de discussion, modification du code jusqu'à ce que ce soit jugé satisfaisant.
4. déploiement de la branche sur la recette, notification de Claudia ou de la/les personnes pertinentes sur la fiche Trello (et parfois sur Mattermost) avec un éventuel commentaire (si nécessaire) pour préciser le comportement et comment tester, passage de la carte Trello dans la colonne "En recette"
5. test fonctionnel de la recette par Claudia ou la/les personnes pertinentes (une carte Trello en haut de la colonne "En recette" récapitule comment faire une recette)
6. si le comportement est satisfaisant lors du test, la personne qui a fait la recette déplace la carte dans la colonne "Recette OK". Sinon la personne déplace la carte dans la colonne "Recette KO" en précisant les éléments à modifier. Dans ce cas, la fiche repassera à "En cours" quand on retravaille dessus, etc.
7. une fois que la recette est validée, on met à jour la branche si nécessaire et on la rappatrie dans la branche main avec un merge via la PR pour garder l'historique des commits quand on a fait des commits significatifs (ce qui est préconisé) mais garder un lien avec l'historique de la PR et faciliter un rollback éventuel (?). Si l'historique des commits sur la branche n'est pas significatif/propre, un squash est une solution pertinente. Puis déploiement de main en production et déplacement de la carte Trello dans la colonne "Terminé".

NB : selon les tâches, certaines étapes peuvent être sautées ou modifiées. Par exemple, quand c'est purement technique, il n'y a pas de recettage par d'autres personnes que des devs.
