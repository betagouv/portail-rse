<script>
    const appartientGroupeId = "id_appartient_groupe" // defined by django

    const groupeFieldset = document.getElementById("svelte-groupe-fields")
    const appartientGroupeField = document.getElementById(appartientGroupeId)

    const displayGroupeFields = () => {
        groupeFieldset.style.display = appartientGroupeField.checked ? "block" : "none"
    }

    appartientGroupeField.addEventListener(
      "change",
      displayGroupeFields,
    );

    displayGroupeFields()

</script>
