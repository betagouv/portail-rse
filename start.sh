#! /bin/bash

python impact/manage.py collectstatic --no-input

# En supposant qu'il y avait au moins 8 cores sur la machine et d'après la doc de gunicorn le nombre de workers conseillé est (2 x $num_cores) + 1
# https://docs.gunicorn.org/en/stable/design.html#how-many-workers
# Ce n'était pas concluant (explosion de la mémoire)
gunicorn --workers=3 --pythonpath=impact impact.wsgi --log-file -
