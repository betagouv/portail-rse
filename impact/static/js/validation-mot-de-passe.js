// Indique pendant la saisie si le mot de passe respecte les règles et si la confirmation est identique
// équivalent de string.punctuation utilisé côté serveur dans password_validation.py
const caracteresSpeciaux = /[!"#$%&'()*+,-./:;<=>?@[\\\]^_`{|}~]/
const regles = {
  longueur: (mdp) => mdp.length >= 12,
  minuscule: (mdp) => /[a-z]/.test(mdp),
  majuscule: (mdp) => /[A-Z]/.test(mdp),
  chiffre: (mdp) => /[0-9]/.test(mdp),
  special: (mdp) => caracteresSpeciaux.test(mdp),
  identique: (mdp, confirmation) => mdp === confirmation,
}

for (const bloc of document.querySelectorAll("[data-validation-mot-de-passe]")) {
  const [motDePasse, confirmation] = bloc.querySelectorAll(".fr-password__input")
  const verifier = () => {
    const vide = motDePasse.value === ""
    for (const message of bloc.querySelectorAll("[data-regle]")) {
      const valide = regles[message.dataset.regle](motDePasse.value, confirmation.value)
      message.classList.toggle("fr-message--info", vide)
      message.classList.toggle("fr-message--valid", !vide && valide)
      message.classList.toggle("fr-message--error", !vide && !valide)
    }
  }
  motDePasse.addEventListener("input", verifier)
  confirmation.addEventListener("input", verifier)
}
