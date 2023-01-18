import IndicateurExterneToggle from './lib/IndicateurExterneToggle.svelte'

for (var indicateurExterneToggle of document.getElementsByClassName("svelte-indicateur-externe-toggle")) {
  new IndicateurExterneToggle({
    target: indicateurExterneToggle,
    props: {
      toggleId: indicateurExterneToggle.dataset.toggleId,
      fieldId: indicateurExterneToggle.dataset.fieldId,
      indicateursExternesFieldId: indicateurExterneToggle.dataset.indicateursExternesFieldId
    }
  })
}
