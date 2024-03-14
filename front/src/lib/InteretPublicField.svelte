<script>
    const estInteretPublicId = "id_est_interet_public" // defined by django

    const estCoteeFieldset = document.getElementById("svelte-est-cotee-field")
    const estInteretPublicField = document.getElementById(estInteretPublicId)

    const displayEstCoteeField = () => {
      estCoteeFieldset.style.display = estInteretPublicField.checked ? "block" : "none"
    }

    estInteretPublicField.addEventListener(
      "change",
      displayEstCoteeField,
    );

    displayEstCoteeField()
</script>
