<script>
    export let denomination = "undefined"

    document.addEventListener(
        "infos-entreprise",
        (event) => {
            denomination = event.detail["denomination"]
        }
    )
</script>

<p class="denomination">
    <span class="denomination-label">{ denomination}</span>
</p>
