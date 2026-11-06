// Affiche un bloc [data-affiche-si="<id>"] uniquement si la case à cocher <id> est cochée
for (const bloc of document.querySelectorAll("[data-affiche-si]")) {
  const caseACocher = document.getElementById(bloc.dataset.afficheSi)
  const afficher = () => {
    bloc.style.display = caseACocher.checked ? "" : "none"
  }
  caseACocher.addEventListener("change", afficher)
  afficher()
}
