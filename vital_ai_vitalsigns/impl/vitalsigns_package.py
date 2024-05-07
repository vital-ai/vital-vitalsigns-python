class VitalSignsPackage:
    vitalsigns_core_package = 'vital_ai_vitalsigns_core'
    vital_domain_package = 'vital_ai_domain'

    # TODO add lookup methods for registered domains
    @classmethod
    def get_package(cls, owl_url: str):
        return 'ai_vital_aimp'
