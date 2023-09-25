<script>
    import spinner from './assets/spinner.svg'
    import ErrorField from './ErrorField.svelte'

    export let csrfToken = undefined
    export let siren = ""
    export let denomination = ""
    export let effectif = ""
    export let trancheBilan = ""
    export let trancheChiffreAffaires = ""
    export let effectifGroupe = ""
    export let trancheBilanConsolide = ""
    export let trancheChiffreAffairesConsolide = ""
    export let appartientGroupe = false
    export let comptesConsolides = false
    export let errors = {}

    let loading = false
    let promise = async () => {}

    // defined by Django
    const sirenFieldId = "id_siren"
    const csrfTokenFieldName = "csrfmiddlewaretoken"
    const denominationFieldId = "id_denomination"
    const effectifFieldId = "id_effectif"
    const trancheBilanFieldId = "id_tranche_bilan"
    const trancheChiffreAffairesFieldId = "id_tranche_chiffre_affaires"
    const effectifGroupeFieldId = "id_effectif_groupe"
    const trancheBilanConsolideFieldId = "id_tranche_bilan_consolide"
    const trancheChiffreAffairesConsolideFieldId = "id_tranche_chiffre_affaires_consolide"
    const appartientGroupeFieldId = "id_appartient_groupe"
    const comptesConsolidesFieldId = "id_comptes_consolides"

    async function searchEntreprise(siren) {
        if( siren.length !== 9 || isNaN(siren)){
            errors["siren"] = ["Le siren est incorrect."]
            return
        }
        loading = true
        const res = await fetch("/api/search-entreprise/" + siren)
        const json = await res.json();

        if (res.ok) {
            loading = false
            errors["siren"] = undefined
            denomination = json.denomination
            effectif = json.effectif
        } else {
            loading = false
            errors["siren"] = [json['error']]
        }
    }

    const handleChange = () => {
        denomination = ""
        promise = searchEntreprise(siren)
    }
</script>

<form class="fr-mt-6w" on:submit|preventDefault>
<fieldset class="fr-fieldset" aria-label="SIREN de l'entreprise">
    <div class="fr-fieldset__element">
        <div class="fr-input-group {errors.siren ? 'fr-input-group--error' : ''}">
            <label class="fr-label" for="{sirenFieldId}">Votre numéro SIREN
                <span class="fr-hint-text">Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation ou sur l'Annuaire des Entreprises</span>
            </label>
            <div class="fr-col-12 fr-col-sm-6 fr-mt-1w">
                <div class="fr-search-bar" role="search">
                {#if ! loading}
                    <input type="search" name="siren" maxlength="9" minlength="9" class="fr-input {errors.siren ? 'fr-input--error' : ''}" id="{sirenFieldId}" required bind:value={siren} on:change|preventDefault={handleChange}>
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
            {/await}
            <ErrorField id="siren-error-desc-error" errors={errors.siren} />
        </div>
    </div>
    <div class="fr-fieldset__element">
        <a class="fr-link" target="_blank" rel="noopener noreferrer" href="https://annuaire-entreprises.data.gouv.fr/">
            Trouvez votre SIREN sur l'Annuaire des entreprises
        </a>
    </div>
</fieldset>
</form>

{#if denomination}
<form action="/reglementations" method="post">
    <input type="hidden" name="{csrfTokenFieldName}" value="{csrfToken}">
    <input type="hidden" name="siren" value="{siren}">
    <input type="hidden" name="denomination" value="{denomination}" id="{denominationFieldId}">

    <div class="fr-select-group {errors.effectif ? 'fr-select-group--error' : ''}">
        <label class="fr-label" for="{effectifFieldId}">Effectif
            <span class="fr-hint-text">Vérifiez et confirmez le nombre de salariés</span>
        </label>
        <div class="fr-col-12 ">
            <select name="effectif" class="fr-select {errors.effectif ? 'fr-select--error' : ''}" required id="{effectifFieldId}"
                aria-describedby={errors.effectif ? 'effectif-error-desc-error' : null}
                bind:value={effectif}
            >
                <option value="">---------</option>
                <option value="0-49">moins de 50 salariés</option>
                <option value="50-249">entre 50 et 249 salariés</option>
                <option value="250-299">entre 250 et 299 salariés</option>
                <option value="300-499">entre 300 et 499 salariés</option>
                <option value="500-4999">entre 500 et 4 999 salariés</option>
                <option value="5000-9999">entre 5 000 et 9 999 salariés</option>
                <option value="10000+">10 000 salariés ou plus</option>
            </select>
        </div>
        <ErrorField id="effectif-error-desc-error" errors={errors.effectif} />
    </div>

    <div class="fr-select-group {errors.tranche_chiffre_affaires ? 'fr-select-group--error' : ''}">
        <label class="fr-label" for="{trancheChiffreAffairesFieldId}">Chiffre d&#x27;affaires
            <span class="fr-hint-text">Montant net du chiffre d'affaires de l'exercice clos</span>
        </label>
        <div class="fr-col-12 ">
            <select name="tranche_chiffre_affaires" class="fr-select {errors.tranche_chiffre_affaires ? 'fr-select--error' : ''}" required id="{trancheChiffreAffairesFieldId}"
                aria-describedby={errors.tranche_chiffre_affaires ? 'tranche_chiffre_affaires-error-desc-error' : null}
                bind:value={trancheChiffreAffaires}
            >
                <option value="">---------</option>
                <option value="0-700k">moins de 700k€</option>
                <option value="700k-12M">entre 700k€ et 12M€</option>
                <option value="12M-40M">entre 12M€ et 40M€</option>
                <option value="40M-50M">entre 40M€ et 50M€</option>
                <option value="50M-100M">entre 50M€ et 100M€</option>
                <option value="100M+">100M€ ou plus</option>
            </select>
        </div>
        <ErrorField id="tranche_chiffre_affaires-error-desc-error" errors={errors.tranche_chiffre_affaires} />
    </div>

    <div class="fr-select-group {errors.tranche_bilan ? 'fr-select-group--error' : ''}">
        <label class="fr-label" for="{trancheBilanFieldId}">Bilan
            <span class="fr-hint-text">Total du bilan de l'exercice clos</span>
        </label>
        <div class="fr-col-12 ">
            <select name="tranche_bilan" class="fr-select {errors.tranche_bilan ? 'fr-select--error' : ''}" required id="{trancheBilanFieldId}"
                aria-describedby={errors.tranche_bilan ? 'tranche_bilan-error-desc-error' : null}
                bind:value={trancheBilan}
            >
                <option value="">---------</option>
                <option value="0-350k">moins de 350k€</option>
                <option value="350k-6M">entre 350k€ et 6M€</option>
                <option value="6M-20M">entre 6M€ et 20M€</option>
                <option value="20M-43M">entre 20M€ et 43M€</option>
                <option value="43M-100M">entre 43M€ et 100M€</option>
                <option value="100M+">100M€ ou plus</option>
            </select>
        </div>
        <ErrorField id="tranche_bilan-error-desc-error" errors={errors.tranche_bilan} />
    </div>

    <fieldset class="fr-fieldset">
        <legend class="fr-fieldset__legend">Groupe d'entreprises</legend>
        <div class="fr-fieldset__element">
            <div class="fr-checkbox-group">
                <input type="checkbox" name="appartient_groupe" class="fr-input" id="{appartientGroupeFieldId}" bind:checked={appartientGroupe}>
                <label class="fr-label" for="{appartientGroupeFieldId}">L'entreprise appartient à un groupe composé d'une société-mère et d'une ou plusieurs filiales
                    <span class="fr-hint-text"></span>
                </label>
            </div>
        </div>

        {#if appartientGroupe}
            <div class="fr-fieldset__element">
                <div class="fr-select-group {errors.effectif_groupe ? 'fr-select-group--error' : ''}">
                    <label class="fr-label" for="{effectifGroupeFieldId}">Effectif du groupe
                        <span class="fr-hint-text">Nombre de salariés employés par les entreprises du groupe</span>
                    </label>
                    <div class="fr-col-12 ">
                        <select name="effectif_groupe" class="fr-select {errors.effectif_groupe ? 'fr-select--error' : ''}" id="{effectifGroupeFieldId}"
                        aria-describedby={errors.effectif_groupe ? 'effectif_groupe-error-desc-error' : null}
                        bind:value={effectifGroupe}
                        >
                        <option value="">---------</option>
                        <option value="0-49">moins de 50 salariés</option>
                        <option value="50-249">entre 50 et 249 salariés</option>
                        <option value="250-499">entre 250 et 499 salariés</option>
                        <option value="500-4999">entre 500 et 4 999 salariés</option>
                        <option value="5000-9999">entre 5 000 et 9 999 salariés</option>
                        <option value="10000+">10 000 salariés ou plus</option>
                        </select>
                    </div>
                    <ErrorField id="effectif_groupe-error-desc-error" errors={errors.effectif_groupe} />
                </div>
            </div>

            <div class="fr-fieldset__element">
                <div class="fr-checkbox-group">
                    <input type="checkbox" name="comptes_consolides" class="fr-input" id="{comptesConsolidesFieldId}" bind:checked={comptesConsolides}>
                    <label class="fr-label" for="{comptesConsolidesFieldId}">Le groupe d'entreprises établit des comptes consolidés
                        <span class="fr-hint-text"></span>
                    </label>
                </div>
            </div>

            {#if comptesConsolides}
                <div class="fr-fieldset__element">
                    <div class="fr-select-group {errors.tranche_chiffre_affaires_consolide ? 'fr-select-group--error' : ''}">
                        <label class="fr-label" for="{trancheChiffreAffairesConsolideFieldId}">Chiffre d'affaires consolidé du groupe
                            <span class="fr-hint-text"></span>
                        </label>
                        <div class="fr-col-12 ">
                            <select name="tranche_chiffre_affaires_consolide" class="fr-select {errors.tranche_chiffre_affaires_consolide ? 'fr-select--error' : ''}" id="{trancheChiffreAffairesConsolideFieldId}"
                                aria-describedby={errors.tranche_chiffre_affaires_consolide ? 'tranche_chiffre_affaires_consolide-error-desc-error' : null}
                                bind:value={trancheChiffreAffairesConsolide}
                            >
                                <option value="">---------</option>
                                <option value="0-700k">moins de 700k€</option>
                                <option value="700k-12M">entre 700k€ et 12M€</option>
                                <option value="12M-40M">entre 12M€ et 40M€</option>
                                <option value="40M-50M">entre 40M€ et 50M€</option>
                                <option value="50M-100M">entre 50M€ et 100M€</option>
                                <option value="100M+">100M€ ou plus</option>
                            </select>
                        </div>
                        <ErrorField id="tranche_chiffre_affaires_consolide-error-desc-error" errors={errors.tranche_chiffre_affaires_consolide} />
                    </div>
                </div>

                <div class="fr-fieldset__element">
                    <div class="fr-select-group {errors.tranche_bilan_consolide ? 'fr-select-group--error' : ''}">
                        <label class="fr-label" for="{trancheBilanConsolideFieldId}">Bilan consolidé du groupe
                            <span class="fr-hint-text"></span>
                        </label>
                        <div class="fr-col-12 ">
                            <select name="tranche_bilan_consolide" class="fr-select {errors.tranche_bilan_consolide ? 'fr-select--error' : ''}" id="{trancheBilanConsolideFieldId}"
                                aria-describedby={errors.tranche_bilan_consolide ? 'tranche_bilan_consolide-error-desc-error' : null}
                                bind:value={trancheBilanConsolide}
                            >
                                <option value="">---------</option>
                                <option value="0-350k">moins de 350k€</option>
                                <option value="350k-6M">entre 350k€ et 6M€</option>
                                <option value="6M-20M">entre 6M€ et 20M€</option>
                                <option value="20M-43M">entre 20M€ et 43M€</option>
                                <option value="43M-100M">entre 43M€ et 100M€</option>
                                <option value="100M+">100M€ ou plus</option>
                            </select>
                        </div>
                        <ErrorField id="tranche_bilan_consolide-error-desc-error" errors={errors.tranche_bilan_consolide} />
                    </div>
                </div>
            {/if}
        {/if}
    </fieldset>
    <input type="submit" value="Vérifier mes obligations" class="fr-btn">
</form>
{/if}
