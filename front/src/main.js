import DenominationEntreprise from './lib/DenominationEntreprise.svelte'
import ExternalFieldToggle from './lib/ExternalFieldToggle.svelte'
import GroupeFields from './lib/GroupeFields.svelte'
import InteretPublicField from './lib/InteretPublicField.svelte'
import SimulationResult from './lib/SimulationResult.svelte'
import SimulationForm from './lib/SimulationForm.svelte'
import SearchEntreprise from './lib/SearchEntreprise.svelte'
import SeeMoreOrLess from './lib/SeeMoreOrLess.svelte'

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
      siren: searchEntrepriseElement.dataset.siren,
      denomination: searchEntrepriseElement.dataset.denomination
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

const estInteretPublicFieldElement = document.getElementById("svelte-est-interet-public-field")
if (estInteretPublicFieldElement) {
  new InteretPublicField({
    target: estInteretPublicFieldElement,
  })
}

const SimulationFormElement = document.getElementById("svelte-search-entreprise-in-simulation-form")
if (SimulationFormElement) {
  new SimulationForm({
    target: SimulationFormElement,
    props: {
      siren: SimulationFormElement.dataset.siren,
      denomination: SimulationFormElement.dataset.denomination
    },
    hydrate: true,
  })
}

if (document.getElementById("svelte-simulation-result")) {
  new SimulationResult({
    target: document.getElementById("svelte-simulation-form")
  })
}

const denominationEntrepriseElement = document.getElementById("svelte-denomination-entreprise")
if (denominationEntrepriseElement) {
  new DenominationEntreprise({
    target: denominationEntrepriseElement,
    props: {
      denomination: denominationEntrepriseElement.dataset.denomination
    },
    hydrate: true,
  })
}

const VoirPlusMoinsElement = document.getElementById("svelte-voir-plus-moins")
if (VoirPlusMoinsElement) {
  new SeeMoreOrLess({
    target: VoirPlusMoinsElement
  })
}
