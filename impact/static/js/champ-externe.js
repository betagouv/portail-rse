// Bascule "Information déjà fournie" des champs BDESE :
// met à jour la liste JSON des champs externes et affiche le bloc correspondant
for (const bascule of document.querySelectorAll("[data-champ-externe]")) {
  const conteneur = document.getElementById(bascule.dataset.conteneurId)
  const champsExternes = document.getElementById(bascule.dataset.champsExternesId)
  const nomChamp = bascule.dataset.champExterne
  const afficher = () => {
    conteneur.querySelector(".external-field").style.display = bascule.checked ? "" : "none"
    conteneur.querySelector(".internal-field").style.display = bascule.checked ? "none" : ""
  }
  bascule.addEventListener("change", () => {
    const noms = (JSON.parse(champsExternes.value) || []).filter(nom => nom !== nomChamp)
    if (bascule.checked) noms.push(nomChamp)
    champsExternes.value = JSON.stringify(noms)
    afficher()
  })
  afficher()
}
