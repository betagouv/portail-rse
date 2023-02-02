<script>
    import { externalFields } from './stores.js';

    export let toggleId = undefined
    export let fieldName = undefined
    export let fieldContainerId = undefined
    export let externalFieldsInStepFieldId = undefined

    let fieldContainer = document.getElementById(fieldContainerId)
    let externalFieldsInStepField = document.getElementById(externalFieldsInStepFieldId)

    $: externalFieldsInStepField.value = JSON.stringify($externalFields)

    $externalFields = JSON.parse(externalFieldsInStepField.value)

    let checked = $externalFields.includes(fieldName)

    const displayField = () => {
        fieldContainer.getElementsByClassName("svelte-external-field")[0].style.display = checked ? "block" : "none"
        fieldContainer.getElementsByClassName("svelte-internal-field")[0].style.display = checked ? "none" : "block"
    }

    const handleChange = () => {
        if (checked) {
            $externalFields = [...$externalFields, fieldName]
        } else {
            $externalFields = $externalFields.filter(name => name != fieldName)
        }
        displayField()
    }

    displayField()
</script>

<div class="fr-toggle fr-toggle--label-left fr-toggle--border-bottom">
    <input type="checkbox" class="fr-toggle__input" id="{toggleId}" bind:checked on:change={handleChange}>
    <label class="fr-toggle__label fr-text--sm" for="{toggleId}" data-fr-checked-label="Oui" data-fr-unchecked-label="Non">Information déjà fournie</label>
</div>
