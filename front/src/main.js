import IndicateurExterneToggle from './lib/IndicateurExterneToggle.svelte'

for (let indicateurExterneToggle of document.getElementsByClassName("svelte-indicateur-externe-toggle")) {
  new IndicateurExterneToggle({
    target: indicateurExterneToggle,
    props: {
      toggleId: indicateurExterneToggle.dataset.toggleId,
      fieldName: indicateurExterneToggle.dataset.fieldName,
      fieldContainerId: indicateurExterneToggle.dataset.fieldContainerId,
      indicateursExternesFieldId: indicateurExterneToggle.dataset.indicateursExternesFieldId
    }
  })
}
