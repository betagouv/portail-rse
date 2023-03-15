<script>
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

    <div class="fr-input-group">
        <label class="fr-label" for="id_siren">Votre numéro SIREN
            <span class="fr-hint-text">Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation</span>
        </label>
        <div class="fr-col-12 fr-col-sm-6">
            <div class="fr-search-bar" role="search">
            {#if ! recherche}
                <input type="search" name="siren" maxlength="9" minlength="9" class="fr-input" id="id_siren" bind:value={siren} on:change|preventDefault={handleChange}>
                <button class="fr-btn" title="Rechercher" on:click|preventDefault={handleChange}>
                    Rechercher
                </button>
                {:else}
                <input type="text" name="siren" maxlength="9" minlength="9" class="fr-input" id="id_siren" value="{siren}" readonly>
                <img src="/static/img/spinner.svg" width="40" alt="Spinner d'attente">
                {/if}
            </div>
        </div>
    </div>

    {#await promise then json}
        {#if json.raison_sociale}
            <p>Entreprise : {json.raison_sociale}</p>

            <div class="fr-input-group">
                <label class="fr-label" for="id_fonctions">Fonction(s) dans la société
                </label>
                <div class="fr-col-12 fr-col-sm-6">
                    <input type="text" name="fonctions" class="fr-input" id="id_fonctions" required>
                </div>
            </div>

            <input type="submit" value="Ajouter cette entreprise" class="fr-btn">
        {/if}
    {:catch error}
        <p class="fr-error-text">{error.message}</p>
    {/await}
