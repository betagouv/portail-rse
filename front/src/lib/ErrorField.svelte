<script>
    export let errors = undefined
    export let id = undefined
</script>

{#if errors}
<p id={id} class="fr-error-text">
    {#each errors as error}
    {error}
    {/each}
</p>
{/if}
