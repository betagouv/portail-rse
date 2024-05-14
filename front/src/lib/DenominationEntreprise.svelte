<script>
    export let denomination = undefined

    document.addEventListener(
        "infos-entreprise",
        (event) => {
            denomination = event.detail["denomination"]
        }
    )
</script>

<h4 class="denomination">{ denomination}</h4>
