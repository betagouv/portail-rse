import ExternalFieldToggle from './lib/ExternalFieldToggle.svelte'
import GroupeFields from './lib/GroupeFields.svelte'
import SearchEntreprise from './lib/SearchEntreprise.svelte'
import SimulationForm from './lib/SimulationForm.svelte'

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

if (document.getElementById("svelte-simulation-form")) {
  let target = document.getElementById("svelte-simulation-form")
  let formData = JSON.parse(document.getElementById("svelte-form-data").textContent)
  new SimulationForm({
    target: target,
    props: {
      csrfToken: formData.csrfToken,
      siren: formData.siren,
      denomination: formData.denomination,
      effectif: formData.effectif,
      trancheChiffreAffaires: formData.tranche_chiffre_affaires,
      trancheBilan: formData.tranche_bilan,
      effectifGroupe: formData.effectif_groupe,
      trancheChiffreAffairesConsolide: formData.tranche_chiffre_affaires_consolide,
      trancheBilanConsolide: formData.tranche_bilan_consolide,
      comptesConsolides: formData.comptes_consolides,
      appartientGroupe: formData.appartient_groupe,
      errors: formData.errors,
    }
  })
}

if (document.getElementById("svelte-appartient-groupe-field")) {
  let target = document.getElementById("svelte-appartient-groupe-field")
  new GroupeFields({
    target: target,
  })
}
