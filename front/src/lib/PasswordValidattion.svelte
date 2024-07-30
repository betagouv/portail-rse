<script>
    let password1 = ""
    let password2 = ""
    let showPassword1 = false
    let showPassword2 = false

    // defined by django
    const password1FieldId = "id_password1"
    const password1FieldName = "password1"
    const password2FieldId = "id_password2"
    const password2FieldName = "password2"
    // équivalent de string.punctuation utilisé côté serveur dans password_validation.py
    const specialChars = /[!"#$%&'()*+,-./:;<=>?@[\\\]^_`{|}~]/

    const password1Field = document.getElementById(password1FieldId)
    const password2Field = document.getElementById(password2FieldId)

    $: isEmpty = password1 === ""
    $: isTooShort = password1.length < 12
    $: containsLowercase = /[a-z]/.test(password1)
    $: containsUppercase = /[A-Z]/.test(password1)
    $: containsDigit = /[0-9]/.test(password1)
    $: containsSpecialChar = specialChars.test(password1)
    $: passwordsAreIdentical = password1 === password2

    $: password1Field.type = showPassword1 ? "text" : "password"
    $: password2Field.type = showPassword2 ? "text" : "password"
</script>

<fieldset class="fr-fieldset" aria-label="Définition du mot de passe">
    <div class="fr-fieldset__element">
        <div class="fr-password">
            <label class="fr-label" for="{password1FieldId}">
                Mot de passe
                <span class="fr-hint-text">
                    Votre mot de passe ne doit pas trop ressembler à vos autres informations personnelles et ne doit pas être un mot de passe couramment utilisé.
                    Il doit contenir au minimum 12 caractères et au moins une minuscule, une majuscule, un chiffre et un caractère spécial.
                </span>
            </label>
            <div class="fr-input-wrap">
                <input type="password" name="{password1FieldName}" autocomplete="new-password" class="fr-password__input fr-input" aria-describedby="{password1FieldId}-input-messages" aria-required="true" required id="{password1FieldId}" bind:value={password1}>
            </div>
            <div class="fr-messages-group" id="{password1FieldId}-input-messages" aria-live="assertive">
                <p class="fr-message">Votre mot de passe doit contenir :</p>
                <p class="fr-message {isEmpty ? "fr-message--info" : isTooShort ? "fr-message--error" : "fr-message--valid"}">12 caractères minimum</p>
                <p class="fr-message {isEmpty ? "fr-message--info" : containsLowercase ? "fr-message--valid" : "fr-message--error"}">1 minuscule minimum</p>
                <p class="fr-message {isEmpty ? "fr-message--info" : containsUppercase ? "fr-message--valid" : "fr-message--error"}">1 majuscule minimum</p>
                <p class="fr-message {isEmpty ? "fr-message--info" : containsDigit ? "fr-message--valid" : "fr-message--error"}">1 chiffre minimum</p>
                <p class="fr-message {isEmpty ? "fr-message--info" : containsSpecialChar ? "fr-message--valid" : "fr-message--error"}">1 caractère spécial minimum</p>
            </div>
            <div class="fr-password__checkbox fr-checkbox-group fr-checkbox-group--sm">
                <input aria-label="Afficher le mot de passe" id="{password1FieldId}-show" type="checkbox" bind:checked={showPassword1}>
                <label class="fr-password__checkbox fr-label" for="{password1FieldId}-show">
                    Afficher
                </label>
            </div>
        </div>
    </div>

    <div class="fr-fieldset__element">
        <div class="fr-password">
            <label class="fr-label" for="{password2FieldId}">
                Confirmation du mot de passe
            </label>
            <div class="fr-input-wrap">
                <input type="password" name="{password2FieldName}" autocomplete="new-password" class="fr-password__input fr-input" aria-describedby="{password2FieldId}-input-messages" aria-required="true" required id="{password2FieldId}" bind:value={password2}>
            </div>
            <div class="fr-messages-group" id="{password2FieldId}-input-messages" aria-live="assertive">
                <p class="fr-message {isEmpty ? "fr-message--info" : passwordsAreIdentical ? "fr-message--valid" : "fr-message--error"}">Les mots de passe doivent être identiques</p>
            </div>
            <div class="fr-password__checkbox fr-checkbox-group fr-checkbox-group--sm">
                <input aria-label="Afficher le mot de passe" id="{password2FieldId}-show" type="checkbox" bind:checked={showPassword2}>
                <label class="fr-password__checkbox fr-label" for="{password2FieldId}-show">
                    Afficher
                </label>
            </div>
        </div>
    </div>
</fieldset>
