<script>
    import { indicateursExternes } from './stores.js';

    export let toggleId = undefined
    export let fieldId = undefined
    export let fieldName = undefined
    export let indicateursExternesFieldId = undefined

    let field = document.getElementById(fieldId)
    let indicateursExternesField = document.getElementById(indicateursExternesFieldId)

    $: indicateursExternesField.value = JSON.stringify($indicateursExternes)

    $indicateursExternes = JSON.parse(indicateursExternesField.value)

    let checked = $indicateursExternes.includes(fieldName)
    if (checked) {
        field.getElementsByClassName("svelte-deja-fourni")[0].style.display = checked ? "block" : "none"
        field.getElementsByClassName("svelte-a-remplir")[0].style.display = checked ? "none" : "block"
    }

    const handleChange = () => {
        if (checked) {
            $indicateursExternes = [...$indicateursExternes, fieldName]
        } else {
            $indicateursExternes = $indicateursExternes.filter(name => name != fieldName)
        }
        field.getElementsByClassName("svelte-deja-fourni")[0].style.display = checked ? "block" : "none"
        field.getElementsByClassName("svelte-a-remplir")[0].style.display = checked ? "none" : "block"
    }
</script>

<div class="fr-toggle">
    <input type="checkbox" class="fr-toggle__input" id="{toggleId}" bind:checked on:change={handleChange}>
    <label class="fr-toggle__label" for="{toggleId}" data-fr-checked-label="Activé" data-fr-unchecked-label="Désactivé">Indicateur externe</label> 
</div>
