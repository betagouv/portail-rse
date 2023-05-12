<script>
    import spinner from './assets/spinner.svg';

    let siren = ""
    let loading = false
    let promise = async () => {}

    const sirenFieldId = "id_siren" // defined by django
    const submitButton = document.getElementById(sirenFieldId).closest("form").querySelector("[type=submit]")
    submitButton.disabled = true

    async function searchEntreprise(siren) {
        if( siren.length !== 9 || isNaN(siren)){
            throw new Error("Le siren est incorrect.")
        }
        loading = true
        const res = await fetch("/api/search-entreprise/" + siren)
        const json = await res.json();

        if (res.ok) {
            loading = false
            submitButton.disabled = false
            return json;
        } else {
            loading = false
            throw new Error(json['error'])
        }
    }

    const handleChange = () => {
        promise = searchEntreprise(siren)
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
            {#await promise then json}
                {#if json.denomination}
                    <p class="fr-mt-1w fr-mb-n1v">Entreprise : {json.denomination}</p>
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
