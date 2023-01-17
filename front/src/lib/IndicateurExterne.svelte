<script>
    export let toggleId = undefined
    export let fieldId = undefined

    let checked = false

    const handleToggle = () => {
        if (checked) {
            document.getElementById(fieldId).disabled = true
        } else {
            document.getElementById(fieldId).disabled = false
        }

    }
</script>

<div class="fr-toggle">
    <input type="checkbox" class="fr-toggle__input" aria-describedby="{toggleId}-hint-text" id="{toggleId}" bind:checked on:change={handleToggle}>
    <label class="fr-toggle__label" for="{toggleId}" data-fr-checked-label="Activé" data-fr-unchecked-label="Désactivé">Indicateur externe</label> 
</div>
