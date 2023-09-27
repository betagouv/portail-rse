<script>
    const simulationResult = document.getElementById("svelte-simulation-result")

    const setDeprecated = () => {
        simulationResult.classList.add("deprecated")
    }

    const form = document.getElementById("svelte-simulation-form")
    const inputs = form.elements

    for (let input of inputs) {
      input.addEventListener(
        "change",
        setDeprecated,
      )
    }
</script>
