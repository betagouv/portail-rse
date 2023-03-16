<script>
    import spinner from './assets/spinner.svg';
    let siren = ""
    let recherche = false
    let promise = async () => {}

    async function searchEntreprise(siren) {
        if( siren.length !== 9){
            recherche = false
            throw new Error("Le siren est incorrect.")
        }
        const res = await fetch("/api/search-entreprise/" + siren)
        const json = await res.json();

        if (res.ok) {
            recherche = false
            return json;
        } else {
            recherche = false
            throw new Error(json['error'])
        }
    }

    const handleChange = () => {
        recherche = true
        promise = searchEntreprise(siren)
    }
</script>

<fieldset class="fr-fieldset fr-mb-3w" aria-label="SIREN de l'entreprise">
    <div class="fr-fieldset__element fr-mb-2w">
        <div class="fr-input-group">
            <label class="fr-label" for="id_siren">Votre numéro SIREN
                <span class="fr-hint-text">Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation ou sur l'Annuaire des Entreprises</span>
            </label>
            <div class="fr-col-12 fr-col-sm-6">
                <div class="fr-search-bar" role="search">
                {#if ! recherche}
                    <input type="search" name="siren" maxlength="9" minlength="9" class="fr-input" id="id_siren" required bind:value={siren} on:change|preventDefault={handleChange}>
                    <button class="fr-btn" title="Rechercher" on:click|preventDefault={handleChange}>
                        Rechercher
                    </button>
                    {:else}
                    <input type="text" name="siren" maxlength="9" minlength="9" class="fr-input" id="id_siren" value="{siren}" readonly>
                    <img src="{spinner}" width="40" alt="Spinner d'attente">
                    {/if}
                </div>
            </div>
            {#await promise then json}
                {#if json.raison_sociale}
                    <p>Entreprise : {json.raison_sociale}</p>
                {/if}
            {:catch error}
                <p class="fr-error-text">{error.message}</p>
            {/await}
        </div>
    </div>
    <div class="fr-mt-n1v fr-fieldset__element">
        <a class="fr-link" target="_blank" rel="noopener noreferrer" href="https://annuaire-entreprises.data.gouv.fr/">
            Trouvez votre SIREN sur l'Annuaire des entreprises
        </a>
    </div>
</fieldset>
