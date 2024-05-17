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

    const submitButton = document.getElementById(sirenFieldId).closest("form").querySelector("[type=submit]")


    async function searchEntreprise(siren) {
        if (siren.length !== 9 || isNaN(siren)){
            const event = new CustomEvent("siren-incorrect")
            document.dispatchEvent(event)
            throw new Error("Le siren est incorrect.")
        }
        loading = true
        const res = await fetch("/api/search-entreprise/" + siren)
        const json = await res.json()

        if (res.ok) {
            loading = false
            submitButton.disabled = false
            denomination = json.denomination
            const event = new CustomEvent("infos-entreprise", {detail: json})
            document.dispatchEvent(event)
        } else {
            loading = false
            const event = new CustomEvent("siren-incorrect")
            document.dispatchEvent(event)
            throw new Error(json['error'])
        }
    }

    const handleChange = () => {
        submitButton.disabled = true
        promise = searchEntreprise(siren)
    }

    if (!siren) {
        submitButton.disabled = true
    }
</script>

<fieldset class="fr-fieldset" aria-label="SIREN de l'entreprise">
    <div class="fr-fieldset__element">
        <div class="fr-input-group">
            <label class="fr-label" for="{sirenFieldId}">Saisissez le numéro SIREN de votre entreprise</label>
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
