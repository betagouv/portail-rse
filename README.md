# Plateforme Impact

https://beta.gouv.fr/startups/plateforme.impact.html


## développement local


```
export SECRET_KEY=fake-secret-key
export API_ENTREPRISE_TOKEN=xxx
. ./venv/bin/activate
python3 impact/manage.py runserver
```


Il est nécessaire d'installer le paquet système `libpq-dev` pour avoir `pg_config`.