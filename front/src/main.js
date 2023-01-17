import Counter from './lib/Counter.svelte'
import IndicateurExterne from './lib/IndicateurExterne.svelte'

const counter = new Counter({
  target: document.getElementById('counter'),
})

for (var indicateurExterne of document.getElementsByClassName("svelte-indicateur-externe")) {
  new IndicateurExterne({
    target: indicateurExterne,
    props: {
      toggleId: indicateurExterne.dataset.toggleId,
      fieldId: indicateurExterne.dataset.fieldId
    }
  })
}

export default counter
