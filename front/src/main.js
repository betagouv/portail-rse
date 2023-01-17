import IndicateurExterne from './lib/IndicateurExterne.svelte'

for (var indicateurExterne of document.getElementsByClassName("svelte-indicateur-externe")) {
  new IndicateurExterne({
    target: indicateurExterne,
    props: {
      toggleId: indicateurExterne.dataset.toggleId,
      fieldId: indicateurExterne.dataset.fieldId
    }
  })
}
