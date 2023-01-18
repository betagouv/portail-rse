import IndicateurExterneToggle from './lib/IndicateurExterneToggle.svelte'

for (let indicateurExterneToggle of document.getElementsByClassName("svelte-indicateur-externe-toggle")) {
  new IndicateurExterneToggle({
    target: indicateurExterneToggle,
    props: {
      toggleId: indicateurExterneToggle.dataset.toggleId,
      fieldId: indicateurExterneToggle.dataset.fieldId,
      fieldName: indicateurExterneToggle.dataset.fieldName,
      indicateursExternesFieldId: indicateurExterneToggle.dataset.indicateursExternesFieldId
    }
  })
}
