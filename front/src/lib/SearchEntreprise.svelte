<script>
    import spinner from './assets/spinner.svg'
    import AutoComplete from "simple-svelte-autocomplete"

    export let siren = ""
    export let denomination = ""
    let entreprises = []
    let loading = false
    let promise = async () => {}

    // defined by django
    const sirenFieldId = "id_siren"
    const sirenFieldName = "siren"
    const denominationFieldName = "denomination"

    const submitButton = document.getElementById(sirenFieldId).closest("form").querySelector("[type=submit]")


    async function searchEntreprise(siren) {
        /*if (siren.length !== 9 || isNaN(siren)){
            const event = new CustomEvent("siren-incorrect")
            document.dispatchEvent(event)
            throw new Error("Le siren est incorrect.")
        }*/
        loading = true
        const res = await fetch("/api/search-entreprise/" + siren)
        const json = await res.json()
        entreprises = json

        if (true || res.ok) {
            loading = false
            submitButton.disabled = false
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
        const event = new CustomEvent("siren-incorrect")
        document.dispatchEvent(event)
    }

    const handleSelectionEntreprise = (siren) => {
        let entrepriseSelectionnee = entreprises[0]
        for (let entreprise of entreprises ){
            if (entreprise.siren == siren) {
                entrepriseSelectionnee = entreprise
                break
            }
        }
        entreprises = [entrepriseSelectionnee]
        denomination = entreprises[0].denomination
        const event = new CustomEvent("infos-entreprise", {detail: entreprises[0]})
        document.dispatchEvent(event)
    }

    if (!siren) {
        submitButton.disabled = true
    }


const colors = ["White", "Red", "Yellow", "Green", "Blue", "Black"]
let selectedColor

function getItems(keyword) {

    return [
                {
                "siren": "889297453",
                "effectif": "0-9",
                "denomination": "entreprise A",
                "categorie_juridique_sirene": 5308,
                "code_pays_etranger_sirene": None,
                },
                {
                    "siren": "987654321",
                    "effectif": "50-249",
                    "denomination": "entreprise B",
                    "categorie_juridique_sirene": 5800,
                    "code_pays_etranger_sirene": None,
                }
            ]

  //const url = "/api/my-items/?format=json&name=" + encodeURIComponent(keyword)

  //const response = await fetch(url)
  /*
  const response = await fetch("/api/search-entreprise/" + keyword)

  const json = await response.json()
    console.log(json.results)
  return json.results
  */
}

</script>

<style>

</style>



<fieldset class="fr-fieldset" aria-label="SIREN de l'entreprise">
    <div class="fr-fieldset__element">
        <div class="fr-input-group">
            <label class="fr-label" for="{sirenFieldId}">Votre numéro SIREN
                <span class="fr-hint-text">Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation ou sur l'Annuaire des Entreprises</span>
            </label>
            <div class="fr-col-12 fr-col-sm-6 fr-mt-1w">
                <div class="fr-search-bar" role="search">
                <AutoComplete
                    searchFunction="{getItems}"
                    delay="200"
                    localFiltering={false}
                    noInputStyles
                    inputClassName="fr-input"
                    labelFieldName="siren"

                    bind:selectedItem="{selectedColor}"
                />

                </div>
            </div>
            <div class="fr-my-1w">
                <a class="fr-link" target="_blank" rel="noopener noreferrer" href="https://annuaire-entreprises.data.gouv.fr/">
                    Trouvez votre SIREN sur l'Annuaire des entreprises
                </a>
            </div>
            {#await promise then result}
            {#if entreprises.length == 1}
                {#if denomination}
                    <p class="fr-my-2w denomination">Entreprise : {denomination}</p>
                {/if}
            {:else if entreprises.length >= 2}
                <ul class="fr-btns-group fr-btns-group--inline-sm">
                    {#each entreprises as entreprise, index (entreprise.siren)}
                    <li>
                        <button  class="fr-btn" on:click={handleSelectionEntreprise(entreprise.siren)}>{entreprise.denomination} ({entreprise.siren})</button>
                    </li>
                    {/each}
                </ul>
            {/if}
            {:catch error}
                <p class="fr-error-text">{error.message}</p>
            {/await}
        </div>
    </div>
</fieldset>

<hr />


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
            {#if entreprises.length == 1}
                {#if denomination}
                    <p class="fr-my-2w denomination">Entreprise : {denomination}</p>
                {/if}
            {:else if entreprises.length >= 2}
                <ul class="fr-btns-group fr-btns-group--inline-sm">
                    {#each entreprises as entreprise, index (entreprise.siren)}
                    <li>
                        <button  class="fr-btn" on:click={handleSelectionEntreprise(entreprise.siren)}>{entreprise.denomination} ({entreprise.siren})</button>
                    </li>
                    {/each}
                </ul>
            {/if}
            {:catch error}
                <p class="fr-error-text">{error.message}</p>
            {/await}
        </div>
    </div>
</fieldset>

<input type="hidden" name="{denominationFieldName}" value="{denomination}">
