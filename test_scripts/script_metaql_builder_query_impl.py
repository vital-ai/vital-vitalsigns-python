import json

from vital_ai_vitalsigns.metaql.constraint.metaql_constraint import COMPARATOR_TYPE_STRING_CONTAINS
from vital_ai_vitalsigns.metaql.constraint.metaql_property_constraint import TARGET_TYPE_NODE, \
    STRING_PROPERTY_DATA_CONSTRAINT_TYPE
from vital_ai_vitalsigns.metaql.constraint_list.metaql_constraint_list import AND_CONSTRAINT_LIST_TYPE
from vital_ai_vitalsigns.metaql.metaql_builder import MetaQLBuilder
from vital_ai_vitalsigns.metaql.metaql_parser import MetaQLParser
from vital_ai_vitalsigns.metaql.metaql_query import METAQL_SELECT_QUERY
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.properties.Property_hasName import Property_hasName


def main():

    print('Test MetaQL Query Impl')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    account_uri = "urn:account123"
    account_id = "account123"
    login_uri = "urn:login123"

    jwt_str = ""

    prop_constraint = MetaQLBuilder.build_property_constraint(
        property_constraint_type=STRING_PROPERTY_DATA_CONSTRAINT_TYPE,
        target=TARGET_TYPE_NODE,
        property_uri=Property_hasName.get_uri(),
        comparator=COMPARATOR_TYPE_STRING_CONTAINS,
        string_value="John"
    )

    constraint_list = MetaQLBuilder.build_constraint_list(
        constraint_list_type=AND_CONSTRAINT_LIST_TYPE,
        constraint_list=[prop_constraint]
    )

    root_arc = MetaQLBuilder.build_root_arc(
        constraint_list_list=[constraint_list]
    )

    metaql_query = MetaQLBuilder.build_metaql_query(
        metaql_query_type=METAQL_SELECT_QUERY,
        root_arc=root_arc,
    )

    metaql_request = MetaQLBuilder.build_metaql_request(
        account_uri=account_uri,
        account_id=account_id,
        login_uri=login_uri,
        jwt_str=jwt_str,

        metaql_query=metaql_query,
    )

    # print(metaql_request)

    metaql_request_json = json.dumps(metaql_request, indent=4)

    print(metaql_request_json)

    # parse json into typed dicts

    metaql_query = MetaQLParser.parse_metaql_request_json(metaql_request_json)

    print(metaql_query)

    # typed dicts into query implementation


if __name__ == "__main__":
    main()
