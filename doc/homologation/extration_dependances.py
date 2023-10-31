import configparser
import json
import re


def main():
    print("Dépendances Python")
    extraire_pipfile()
    print("Dépendances Javascript")
    extraire_package_json()


def extraire_pipfile():
    config = configparser.ConfigParser()
    config.read("../../Pipfile")
    for environnement in ("prod", "dev"):
        section = "packages" if environnement == "prod" else "dev-packages"
        for bibliotheque, version in config[section].items():
            if match := re.search('version = (".*?")', version):
                version = match.group(1)
            print(f"{bibliotheque}\t{version}")


def extraire_package_json():
    with open("../../package.json") as f:
        config = json.loads(f.read())
    for bibliotheque, version in config["devDependencies"].items():
        print(f"{bibliotheque} -> {version}")


main()
