<script>
    import spinner from './assets/spinner.svg'

    export let siren = ""
    let loading = false
    let promise = async () => {}
    let denomination = ""

    const sirenFieldId = "id_siren" // defined by django
    const effectifFieldId = "id_effectif" // defined by django
    const effectifField = document.getElementById(effectifFieldId)
    const submitButton = document.getElementById(sirenFieldId).closest("form").querySelector("[type=submit]")
    submitButton.disabled = true

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
        if( siren.length !== 9 || isNaN(siren)){
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
        handleChange()
    }
    else {
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
                    <input type="search" name="siren" maxlength="9" minlength="9" class="fr-input" id="{sirenFieldId}" required bind:value={siren} on:change|preventDefault={handleChange}>
                    <button type="button" class="fr-btn" title="Rechercher" on:click|preventDefault={handleChange}>
                        Rechercher
                    </button>
                {:else}
                    <input type="text" name="siren" maxlength="9" minlength="9" class="fr-input" id="{sirenFieldId}" value="{siren}" readonly>
                    <img src="{spinner}" width="40" alt="Spinner d'attente">
                {/if}
                </div>
            </div>
            {#await promise then result}
                {#if denomination}
                    <p class="fr-mt-1w fr-mb-n1v">Entreprise : {denomination}</p>
                {/if}
            {:catch error}
                <p class="fr-error-text">{error.message}</p>
            {/await}
        </div>
    </div>
    <div class="fr-fieldset__element">
        <a class="fr-link" target="_blank" rel="noopener noreferrer" href="https://annuaire-entreprises.data.gouv.fr/">
            Trouvez votre SIREN sur l'Annuaire des entreprises
        </a>
    </div>
</fieldset>

<input type="hidden" name="denomination" value="{denomination}">
