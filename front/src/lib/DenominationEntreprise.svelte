<script>
    export let denomination = undefined

    document.addEventListener(
        "infos-entreprise",
        (event) => {
            denomination = event.detail["denomination"]
        }
    )
</script>

{#if denomination}
<p class="denomination">
    <span class="denomination-label">{ denomination}</span>
</p>
{/if}
