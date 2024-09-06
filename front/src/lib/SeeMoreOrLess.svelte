<script>
    // nécessite les trois id svelte-voir-plus-moins, svelte-voir-plus-moins-contenu et svelte-voir-plus-moins-label
    // sur la page.
    // suppose qu'il n'y a qu'un seul bloc plus/moins sur la page
    const content = document.getElementById("svelte-voir-plus-moins-contenu")
    const label = document.getElementById("svelte-voir-plus-moins-label")

    const newLink = (prefixActionLabel, actionLabel, action) => {
      let link = document.createElement('span');
      link.classList.add("fr-link");
      link.classList.add("mimic-link");
      let linkText = document.createTextNode(actionLabel);
      link.appendChild(linkText);
      link.addEventListener("click", () => action());

      while (label.firstChild) {
        label.removeChild(label.firstChild);
      }

      if (prefixActionLabel.length) {
        let prefixNode  = document.createTextNode(prefixActionLabel);
        label.appendChild(prefixNode)
      }
      label.appendChild(link);
    }

    const showContent = () => {
      content.style.display = "inline"
      newLink("", "Voir moins", hideContent)
    }

    const hideContent = () => {
      content.style.display = "none"
      newLink("... ", "Voir plus", showContent)
    }

    hideContent()
</script>
