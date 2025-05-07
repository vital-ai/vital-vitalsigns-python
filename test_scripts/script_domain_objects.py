import logging
from datetime import datetime
from com_vitalai_aimp_domain.model.Payment import Payment
from com_vitalai_domain_wordnet.model.SynsetNode import SynsetNode
from vital_ai_domain.model.Account import Account
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.VitalSegment import VitalSegment


def main():

    print('Hello World')

    before_time = datetime.now()

    logging.basicConfig(level=logging.INFO)

    print(f"Initializing ontologies... ")

    vs = VitalSigns()

    after_time = datetime.now()

    delta = after_time - before_time

    delta_seconds = delta.total_seconds()

    print(f"Initialized Ontologies in: {delta_seconds} seconds.")

    # vs.get_registry().build_registry()

    account = Account()
    account.URI = 'urn:account123'
    account.accountID = 'account123'
    account.name = 'Account123'

    print(account.to_json())
    print(account.to_rdf())

    payment = Payment()
    payment.URI = 'urn:payment123'
    payment.name = 'Payment Name'

    print(payment.to_json())
    print(payment.to_rdf())

    node = SynsetNode()
    node.URI = 'urn:node123'
    print(node.to_json())

    vital_segment = VitalSegment()
    vital_segment.URI = URIGenerator.generate_uri()

    # vital_segment.name = namespace
    # vital_segment.segmentGraphURI = target_graph_uri
    # vital_segment.segmentTenantID = namespace
    vital_segment.segmentGlobal = True # False
    # vital_segment.segmentID = target_graph_uri

    # add json for index state
    # vital_segment.segmentStateJSON = "[]"

    rdf_string = vital_segment.to_rdf()

    print(f"{rdf_string}")

    json_string = vital_segment.to_json()

    print(f"{json_string}")

if __name__ == "__main__":
    main()
