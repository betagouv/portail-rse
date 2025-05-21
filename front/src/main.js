import ExternalFieldToggle from './lib/ExternalFieldToggle.svelte'
import GroupeFields from './lib/GroupeFields.svelte'
import InteretPublicField from './lib/InteretPublicField.svelte'
import PasswordValidattion from './lib/PasswordValidattion.svelte'

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

const passwordValidationElement = document.getElementById("svelte-password-validation")
if (passwordValidationElement) {
  new PasswordValidattion({
    target: passwordValidationElement,
    props: {
      password1FieldName: passwordValidationElement.dataset.password1FieldName,
      password2FieldName: passwordValidationElement.dataset.password2FieldName,
    },
    hydrate: true,
  })
}
