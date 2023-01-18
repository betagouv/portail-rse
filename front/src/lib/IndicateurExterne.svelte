<script>
    export let toggleId = undefined
    export let fieldId = undefined

    let field = document.getElementById(fieldId)
    let indicateursExternesField = document.getElementById("id_indicateurs_externes_in_step")

    let checked = JSON.parse(indicateursExternesField.value).includes(field.name)
    if (checked) {
        field.disabled = true
    }

    const handleToggle = () => {
        const oldIndicateursExternes = JSON.parse(indicateursExternesField.value)
        if (checked) {
            field.disabled = true
            indicateursExternesField.value = JSON.stringify([...oldIndicateursExternes, field.name])

        } else {
            field.disabled = false
            const newIndicateursExternes = oldIndicateursExternes.filter(fieldName => fieldName != field.name)
            indicateursExternesField.value = JSON.stringify(newIndicateursExternes)

        }
    }
</script>

<div class="fr-toggle">
    <input type="checkbox" class="fr-toggle__input" id="{toggleId}" bind:checked on:change={handleToggle}>
    <label class="fr-toggle__label" for="{toggleId}" data-fr-checked-label="Activé" data-fr-unchecked-label="Désactivé">Indicateur externe</label> 
</div>
