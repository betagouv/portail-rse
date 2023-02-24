import ExternalFieldToggle from './lib/ExternalFieldToggle.svelte'
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
      csrfToken: target.dataset.csrfToken
    }
  })
}
