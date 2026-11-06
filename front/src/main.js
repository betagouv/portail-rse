import PasswordValidattion from './lib/PasswordValidattion.svelte'

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
