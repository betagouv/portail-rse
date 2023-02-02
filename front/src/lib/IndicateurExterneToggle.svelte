<script>
    import { indicateursExternes } from './stores.js';

    export let toggleId = undefined
    export let fieldName = undefined
    export let fieldContainerId = undefined
    export let indicateursExternesFieldId = undefined

    let fieldContainer = document.getElementById(fieldContainerId)
    let indicateursExternesField = document.getElementById(indicateursExternesFieldId)

    $: indicateursExternesField.value = JSON.stringify($indicateursExternes)

    $indicateursExternes = JSON.parse(indicateursExternesField.value)

    let checked = $indicateursExternes.includes(fieldName)

    const displayIndicateur = () => {
        fieldContainer.getElementsByClassName("svelte-indicateur-externe")[0].style.display = checked ? "block" : "none"
        fieldContainer.getElementsByClassName("svelte-indicateur-interne")[0].style.display = checked ? "none" : "block"
    }

    const handleChange = () => {
        if (checked) {
            $indicateursExternes = [...$indicateursExternes, fieldName]
        } else {
            $indicateursExternes = $indicateursExternes.filter(name => name != fieldName)
        }
        displayIndicateur()
    }

    displayIndicateur()
</script>

<div class="fr-toggle fr-toggle--label-left fr-toggle--border-bottom">
    <input type="checkbox" class="fr-toggle__input" id="{toggleId}" bind:checked on:change={handleChange}>
    <label class="fr-toggle__label fr-text--sm" for="{toggleId}" data-fr-checked-label="Oui" data-fr-unchecked-label="Non">Information déjà fournie</label>
</div>
