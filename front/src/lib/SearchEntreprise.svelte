<script>
    import spinner from './assets/spinner.svg'

    export let siren = ""
    export let denomination = ""
    let loading = false
    let promise = async () => {}

    // defined by django
    const sirenFieldId = "id_siren"
    const sirenFieldName = "siren"
    const denominationFieldName = "denomination"
    const categorieJuridiqueFieldId = "id_categorie_juridique_sirene"
    const codePaysEtrangerFieldId = "id_code_pays_etranger_sirene"
    const effectifFieldId = "id_effectif"
    const trancheChiffreAffairesFieldId = "id_tranche_chiffre_affaires"

    const categorieJuridiqueField = document.getElementById(categorieJuridiqueFieldId)
    const codePaysEtrangerField = document.getElementById(codePaysEtrangerFieldId)
    const effectifField = document.getElementById(effectifFieldId)
    const trancheChiffreAffairesField = document.getElementById(trancheChiffreAffairesFieldId)
    const submitButton = document.getElementById(sirenFieldId).closest("form").querySelector("[type=submit]")

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

    async function searchEntreprise(siren) {
        if (siren.length !== 9 || isNaN(siren)){
            hideSimulationFields()
            throw new Error("Le siren est incorrect.")
        }
        loading = true
        const res = await fetch("/api/search-entreprise/" + siren)
        const json = await res.json()

        if (res.ok) {
            loading = false
            submitButton.disabled = false
            denomination = json.denomination
            if (effectifField) {
                effectifField.value = json.effectif
            }
            if (categorieJuridiqueField) {
                categorieJuridiqueField.value = json.categorie_juridique_sirene
            }
            if (codePaysEtrangerField) {
                codePaysEtrangerField.value = json.code_pays_etranger_sirene
            }
            if (trancheChiffreAffairesField && json.chiffre_affaires) {
                //                             ^ si l'API ne renvoie pas de chiffre
                //                               d'affaires, ne pas préremplir le champ
                //                               pour garder le label par défaut
                trancheChiffreAffairesField.value = json.tranche_chiffre_affaires
            }
            showSimulationFields()
        } else {
            loading = false
            hideSimulationFields()
            throw new Error(json['error'])
        }
    }

    const handleChange = () => {
        submitButton.disabled = true
        promise = searchEntreprise(siren)
    }

    if (siren) {
        showSimulationFields()
    }
    else {
        submitButton.disabled = true
        hideSimulationFields()
    }
</script>

<fieldset class="fr-fieldset" aria-label="SIREN de l'entreprise">
    <div class="fr-fieldset__element">
        <div class="fr-input-group">
            <label class="fr-label" for="{sirenFieldId}">Votre numéro SIREN
                <span class="fr-hint-text">Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation ou sur l'Annuaire des Entreprises</span>
            </label>
            <div class="fr-col-12 fr-col-sm-6 fr-mt-1w">
                <div class="fr-search-bar" role="search">
                {#if ! loading}
                    <input type="search" name="{sirenFieldName}" maxlength="9" minlength="9" class="fr-input" id="{sirenFieldId}" required bind:value={siren} on:change|preventDefault={handleChange}>
                    <button type="button" class="fr-btn" title="Rechercher" on:click|preventDefault={handleChange}>
                        Rechercher
                    </button>
                {:else}
                    <input type="text" name="{sirenFieldName}" maxlength="9" minlength="9" class="fr-input" id="{sirenFieldId}" value="{siren}" readonly>
                    <img src="{spinner}" width="40" alt="Spinner d'attente">
                {/if}
                </div>
            </div>
            <div class="fr-my-1w">
                <a class="fr-link" target="_blank" rel="noopener noreferrer" href="https://annuaire-entreprises.data.gouv.fr/">
                    Trouvez votre SIREN sur l'Annuaire des entreprises
                </a>
            </div>
            {#await promise then result}
                {#if denomination}
                    <p class="fr-my-2w denomination">Entreprise : {denomination}</p>
                {/if}
            {:catch error}
                <p class="fr-error-text">{error.message}</p>
            {/await}
        </div>
    </div>
</fieldset>

<input type="hidden" name="{denominationFieldName}" value="{denomination}">
