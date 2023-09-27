import ExternalFieldToggle from './lib/ExternalFieldToggle.svelte'
import GroupeFields from './lib/GroupeFields.svelte'
import SimulationChange from './lib/SimulationChange.svelte'
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

const searchEntrepriseElement = document.getElementById("svelte-search-entreprise")
if (searchEntrepriseElement) {
  new SearchEntreprise({
    target: searchEntrepriseElement,
    props: {
      siren: searchEntrepriseElement.dataset.siren
    },
    hydrate: true,
  })
}

const appartientGroupeFieldElement = document.getElementById("svelte-appartient-groupe-field")
if (appartientGroupeFieldElement) {
  new GroupeFields({
    target: appartientGroupeFieldElement,
  })
}

if (document.getElementById("svelte-simulation-result")) {
  new SimulationChange({
    target: document.getElementById("svelte-simulation-form")
  })
}
