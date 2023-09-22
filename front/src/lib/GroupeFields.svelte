<script>
    const appartientGroupeId = "id_appartient_groupe" // defined by django
    const etablitComptesConsolidesId = "id_comptes_consolides" // defined by django

    const groupeFieldset = document.getElementById("svelte-groupe-fields")
    const appartientGroupeField = document.getElementById(appartientGroupeId)

    const comptesConsolidesFields = document.getElementById("svelte-comptes-consolides-fields")
    const etablitComptesConsolidesField = document.getElementById(etablitComptesConsolidesId)

    const displayGroupeFields = () => {
        groupeFieldset.style.display = appartientGroupeField.checked ? "block" : "none"
    }

    const displayComptesConsolidesFields = () => {
      comptesConsolidesFields.style.display = etablitComptesConsolidesField.checked ? "block" : "none"
    }

    appartientGroupeField.addEventListener(
      "change",
      displayGroupeFields,
    );

    etablitComptesConsolidesField.addEventListener(
      "change",
      displayComptesConsolidesFields,
    );

    displayGroupeFields()
    displayComptesConsolidesFields()
</script>
