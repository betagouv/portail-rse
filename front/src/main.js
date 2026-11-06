import ExternalFieldToggle from './lib/ExternalFieldToggle.svelte'
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
