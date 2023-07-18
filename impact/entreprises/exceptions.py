class EntrepriseNonQualifieeError(Exception):
    def __init__(self, message, entreprise):
        self.message = message
        self.entreprise = entreprise
        super().__init__(message, entreprise)
