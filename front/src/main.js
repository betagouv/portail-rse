import ExternalFieldToggle from './lib/ExternalFieldToggle.svelte'
import GroupeFields from './lib/GroupeFields.svelte'
import SearchEntreprise from './lib/SearchEntreprise.svelte'

for (let externalFieldToggle of document.getElementsByClassName("svelte-external-field-toggle")) {
  new ExternalFieldToggle({
    target: externalFieldToggle,
    props: {
      toggleId: externalFieldToggle.dataset.toggleId,
      fieldName: externalFieldToggle.dataset.fieldName,
      fieldContainerId: externalFieldToggle.dataset.fieldContainerId,
      externalFieldsInStepFieldId: externalFieldToggle.dataset.externalFieldsInStepFieldId
    }
  })
}

if (document.getElementById("svelte-search-entreprise")) {
  let target = document.getElementById("svelte-search-entreprise")
  new SearchEntreprise({
    target: target,
    props: {
      siren: target.dataset.siren
    },
    hydrate: true,
  })
}

if (document.getElementById("svelte-appartient-groupe-field")) {
  let target = document.getElementById("svelte-appartient-groupe-field")
  new GroupeFields({
    target: target,
  })
}
