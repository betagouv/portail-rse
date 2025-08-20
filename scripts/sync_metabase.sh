#!/bin/bash

# Exécute les commandes de gestion Django pour synchroniser les données avec Metabase
python manage.py sync_egapro
python manage.py sync_bges
python manage.py sync_metabase
