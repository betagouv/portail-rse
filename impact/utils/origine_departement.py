"""script générant de connaitre la position et le département des entreprises inscrites

suppose qu'une extraction des entreprises soit fournie (entreprises.csv) contenant un siren par ligne, par exemple depuis metabase
"""

import time

import requests

RECHERCHE_ENTREPRISE_TIMEOUT = 10


DEPARTEMENTS = {
    "01": "Ain",
    "02": "Aisne",
    "03": "Allier",
    "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes",
    "07": "Ardèche",
    "08": "Ardennes",
    "09": "Ariège",
    "10": "Aube",
    "11": "Aude",
    "12": "Aveyron",
    "13": "Bouches-du-Rhône",
    "14": "Calvados",
    "15": "Cantal",
    "16": "Charente",
    "17": "Charente-Maritime",
    "18": "Cher",
    "19": "Corrèze",
    "20": "Corse",  # approximation
    "2A": "Corse-du-Sud",
    "2B": "Haute-Corse",
    "21": "Côte-d'Or",
    "22": "Côtes-d'Armor",
    "23": "Creuse",
    "24": "Dordogne",
    "25": "Doubs",
    "26": "Drôme",
    "27": "Eure",
    "28": "Eure-et-Loir",
    "29": "Finistère",
    "30": "Gard",
    "31": "Haute-Garonne",
    "32": "Gers",
    "33": "Gironde",
    "34": "Hérault",
    "35": "Ille-et-Vilaine",
    "36": "Indre",
    "37": "Indre-et-Loire",
    "38": "Isère",
    "39": "Jura",
    "40": "Landes",
    "41": "Loir-et-Cher",
    "42": "Loire",
    "43": "Haute-Loire",
    "44": "Loire-Atlantique",
    "45": "Loiret",
    "46": "Lot",
    "47": "Lot-et-Garonne",
    "48": "Lozère",
    "49": "Maine-et-Loire",
    "50": "Manche",
    "51": "Marne",
    "52": "Haute-Marne",
    "53": "Mayenne",
    "54": "Meurthe-et-Moselle",
    "55": "Meuse",
    "56": "Morbihan",
    "57": "Moselle",
    "58": "Nièvre",
    "59": "Nord",
    "60": "Oise",
    "61": "Orne",
    "62": "Pas-de-Calais",
    "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées",
    "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin",
    "68": "Haut-Rhin",
    "69": "Rhône",
    "70": "Haute-Saône",
    "71": "Saône-et-Loire",
    "72": "Sarthe",
    "73": "Savoie",
    "74": "Haute-Savoie",
    "75": "Paris",
    "76": "Seine-Maritime",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "79": "Deux-Sèvres",
    "80": "Somme",
    "81": "Tarn",
    "82": "Tarn-et-Garonne",
    "83": "Var",
    "84": "Vaucluse",
    "85": "Vendée",
    "86": "Vienne",
    "87": "Haute-Vienne",
    "88": "Vosges",
    "89": "Yonne",
    "90": "Territoire de Belfort",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
    "98": "Outre-mer",  # cas particulier
    # En outre-mer
    "971": "Guadeloupe",
    "972": "Martinique",
    "973": "Guyane",
    "974": "La Réunion",
    "976": "Mayotte",
}


def run():
    compteur = 0
    compteur_succes = 0
    compteur_echec = 0
    with open("entreprises-part.csv") as f_src, open("results.csv", "w") as f_dst:
        for ligne in f_src.readlines():
            siren = ligne.replace("\n", "")
            succes, donnees = recup_donnees(siren)
            if succes:
                coordonnees = donnees["coordonnees"]
                code_postal = donnees["code_postal"]
                departement = extrait_departement(code_postal)
                try:
                    nom_departement = DEPARTEMENTS[departement]
                except KeyError:
                    nom_departement = ""
                output = f"{siren},{coordonnees},{code_postal},{departement},{nom_departement}\n"
                f_dst.write(output)
                compteur_succes += 1
            else:
                print(donnees)
                compteur_echec += 1
            compteur += 1
            if compteur % 100 == 0:
                print(
                    f"{compteur} ENTREPRISES RECHERCHEES, {compteur_succes} SUCCES, {compteur_echec} ECHECS"
                )
            time.sleep(0.15)
    print(f"NB SUCCES = {compteur_succes}")
    print(f"NB ECHECS = {compteur_echec}")


def recup_donnees(siren):
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siren}&page=1&per_page=1&mtm_campaign=portail-rse"
    response = requests.get(url, timeout=RECHERCHE_ENTREPRISE_TIMEOUT)
    if response.status_code == 200 and response.json()["total_results"]:
        data = response.json()["results"][0]
        try:
            code_postal = data["siege"]["code_postal"]
        except KeyError:  # KeyError: 'code_postal'
            return False, f"ERREUR CODE POSTAL keyerror {siren}"
        if not code_postal:
            return False, f"ERREUR CODE POSTAL None {siren}"
        try:
            if "NON-DIFFUSIBLE" in code_postal:
                return False, f"ERREUR NON DIFFUSIBLE {siren}"
            code_postal = f"{code_postal:0>5}"
        except (
            KeyError
        ):  # TypeError: unsupported format string passed to NoneType.__format__, KeyError: 'code_postal'
            return False, f"ERREUR CODE POSTAL {code_postal} {siren}"
        try:
            coordonnees = data["siege"]["coordonnees"].replace(",", " ")
        except (
            AttributeError
        ):  # AttributeError: 'NoneType' object has no attribute 'replace'
            return False, f"ERREUR COORDONNEES {siren}"
        return True, {"code_postal": code_postal, "coordonnees": coordonnees}
    else:
        return False, f"ERREUR NON TROUVE {siren}"


def extrait_departement(code_postal):
    if code_postal[:2] == "97":
        return code_postal[:3]

    return code_postal[:2]
