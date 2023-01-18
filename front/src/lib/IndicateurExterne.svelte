<script>
    import { indicateursExternes } from './stores.js';

    export let toggleId = undefined
    export let fieldId = undefined

    let field = document.getElementById(fieldId)
    let indicateursExternesField = document.getElementById("id_indicateurs_externes_in_step")

    let checked = $indicateursExternes.includes(field.name)
    if (checked) {
        field.disabled = true
    }

    const handleToggle = () => {
        if (checked) {
            $indicateursExternes = [...$indicateursExternes, field.name]
            indicateursExternesField.value = JSON.stringify($indicateursExternes)
        } else {
            $indicateursExternes = $indicateursExternes.filter(fieldName => fieldName != field.name)
            indicateursExternesField.value = JSON.stringify($indicateursExternes)
        }
        field.disabled = checked
    }
</script>

<div class="fr-toggle">
    <input type="checkbox" class="fr-toggle__input" id="{toggleId}" bind:checked on:change={handleToggle}>
    <label class="fr-toggle__label" for="{toggleId}" data-fr-checked-label="Activé" data-fr-unchecked-label="Désactivé">Indicateur externe</label> 
</div>
