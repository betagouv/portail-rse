<script>
    import { indicateursExternes } from './stores.js';

    export let toggleId = undefined
    export let fieldId = undefined

    let field = document.getElementById(fieldId)
    let indicateursExternesField = document.getElementById("id_indicateurs_externes_in_step")

    $: indicateursExternesField.value = JSON.stringify($indicateursExternes)

    let checked = $indicateursExternes.includes(field.name)
    if (checked) {
        field.disabled = true
    }

    const handleToggle = () => {
        if (checked) {
            $indicateursExternes = [...$indicateursExternes, field.name]
        } else {
            $indicateursExternes = $indicateursExternes.filter(fieldName => fieldName != field.name)
        }
        field.disabled = checked
    }
</script>

<div class="fr-toggle">
    <input type="checkbox" class="fr-toggle__input" id="{toggleId}" bind:checked on:change={handleToggle}>
    <label class="fr-toggle__label" for="{toggleId}" data-fr-checked-label="Activé" data-fr-unchecked-label="Désactivé">Indicateur externe</label> 
</div>
