import Counter from './lib/Counter.svelte'

const counter = new Counter({
  target: document.getElementById('counter'),
})

export default counter
