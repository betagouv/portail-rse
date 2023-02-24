<script>
    export let csrfToken = undefined

    let siren = ""
    let recherche = false
    let promise

    async function searchEntreprise(siren) {
        const res = await fetch("/api/search-entreprise/" + siren)
        const json = await res.json();

        if (res.ok) {
            return json;
        } else {
            throw new Error(json['error'])
        }
    }

    const handleChange = () => {
        recherche = true
        promise = searchEntreprise(siren)
    }
</script>


<form action="/entreprises/add" method="post">
    <input type="hidden" name="csrfmiddlewaretoken" value="{csrfToken}">
    <div class="fr-input-group">
        <label class="fr-label" for="id_siren">Votre numéro SIREN
            <span class="fr-hint-text">Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation</span>
        </label>
        <div class="fr-col-12 ">
            <input type="text" name="siren" maxlength="9" minlength="9" class="fr-input" id="id_siren" bind:value={siren} on:change={handleChange}>
        </div>
    </div>
    {#if recherche}
        {#await promise}
            <p>...</p>
        {:then json}
            <p>Entreprise : {json.raison_sociale}</p>

            <div class="fr-input-group">
                <label class="fr-label" for="id_fonctions">Fonction(s) dans la société
                </label>
                <div class="fr-col-12 ">
                    <input type="text" name="fonctions" class="fr-input" id="id_fonctions" required>
                </div>
            </div>

            <input type="submit" value="Ajouter cette entreprise" class="fr-btn">
        {:catch error}
            <p>{error.message}</p>
        {/await}
    {/if}
</form>
