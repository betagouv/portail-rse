<script>
    import SearchEntreprise from './SearchEntreprise.svelte'

    export let siren = ""
    export let denomination = ""

    // defined by django
    const categorieJuridiqueFieldId = "id_categorie_juridique_sirene"
    const codePaysEtrangerFieldId = "id_code_pays_etranger_sirene"
    const codeNAFFieldId = "id_code_NAF"
    const effectifFieldId = "id_effectif"
    const trancheChiffreAffairesFieldId = "id_tranche_chiffre_affaires"
    const appartientGroupeFieldId = "id_appartient_groupe"
    const comptesConsolidesFieldId = "id_comptes_consolides"
    const trancheChiffreAffairesConsolideFieldId = "id_tranche_chiffre_affaires_consolide"

    const categorieJuridiqueField = document.getElementById(categorieJuridiqueFieldId)
    const codePaysEtrangerField = document.getElementById(codePaysEtrangerFieldId)
    const codeNAFField = document.getElementById(codeNAFFieldId)
    const effectifField = document.getElementById(effectifFieldId)
    const trancheChiffreAffairesField = document.getElementById(trancheChiffreAffairesFieldId)
    const appartientGroupeField = document.getElementById(appartientGroupeFieldId)
    const comptesConsolidesField = document.getElementById(comptesConsolidesFieldId)
    const trancheChiffreAffairesConsolideField = document.getElementById(trancheChiffreAffairesConsolideFieldId)

    const simulationFields = document.getElementById("svelte-simulation-fields")

    const showSimulationFields = () => {
        if (simulationFields) {
            simulationFields.style.display = "block"
        }
    }

    const hideSimulationFields = () => {
        if (simulationFields) {
            simulationFields.style.display = "none"
        }
    }

    const resetSimulationFields = () => {
        if (simulationFields) {
            for(let checkboxField of simulationFields.querySelectorAll('[type="checkbox"]')) {
                checkboxField.checked = false
            }
            for(let selectField of simulationFields.getElementsByTagName("select")) {
                selectField.value = ""
            }
            const event = new Event("change");
            appartientGroupeField.dispatchEvent(event);
            comptesConsolidesField.dispatchEvent(event);
        }
    }

    const updateSimulationFields = (infos) => {
        resetSimulationFields()
        denomination = infos.denomination
        effectifField.value = infos.effectif
        categorieJuridiqueField.value = infos.categorie_juridique_sirene
        codePaysEtrangerField.value = infos.code_pays_etranger_sirene
        codeNAFField.value = infos.code_NAF
        if (infos.tranche_chiffre_affaires) {
            // si l'API ne renvoie pas de chiffre
            // d'affaires, ne pas préremplir le champ
            // pour garder le label par défaut
            trancheChiffreAffairesField.value = infos.tranche_chiffre_affaires
        }
        if (infos.tranche_chiffre_affaires_consolide) { // si chiffre d'affaires consolidé, alors est un groupe avec compte consolidé
            appartientGroupeField.checked = true
            comptesConsolidesField.checked = true
            trancheChiffreAffairesConsolideField.value = infos.tranche_chiffre_affaires_consolide
            const event = new Event("change");
            appartientGroupeField.dispatchEvent(event);
            comptesConsolidesField.dispatchEvent(event);
        }
    }

    document.addEventListener(
        "infos-entreprise",
        (event) => {
            showSimulationFields()
            updateSimulationFields(event.detail)
        }
    )

    document.addEventListener(
        "siren-incorrect",
        () => {hideSimulationFields()}
    )

    if (siren) {
        showSimulationFields()
    }
    else {
        hideSimulationFields()
    }
</script>

<SearchEntreprise siren={siren} denomination={denomination} />
