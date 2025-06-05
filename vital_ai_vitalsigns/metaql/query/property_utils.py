from vital_ai_vitalsigns.metaql.constraint.metaql_property_constraint import OTHER_PROPERTY_DATA_CONSTRAINT_TYPE, \
    STRING_PROPERTY_DATA_CONSTRAINT_TYPE, BOOLEAN_PROPERTY_DATA_CONSTRAINT_TYPE, DATETIME_PROPERTY_DATA_CONSTRAINT_TYPE, \
    DOUBLE_PROPERTY_DATA_CONSTRAINT_TYPE, FLOAT_PROPERTY_DATA_CONSTRAINT_TYPE, \
    GEOLOCATION_PROPERTY_DATA_CONSTRAINT_TYPE, INTEGER_PROPERTY_DATA_CONSTRAINT_TYPE, \
    LONG_PROPERTY_DATA_CONSTRAINT_TYPE, TRUTH_PROPERTY_DATA_CONSTRAINT_TYPE, URI_PROPERTY_DATA_CONSTRAINT_TYPE


class PropertyUtils:

    @staticmethod
    def set_property_param_value(property_constraint_type, value, prop_params: dict):

        if property_constraint_type == OTHER_PROPERTY_DATA_CONSTRAINT_TYPE:
            other_value = str(value)
            prop_params["other_value"] = other_value

        if property_constraint_type == STRING_PROPERTY_DATA_CONSTRAINT_TYPE:
            string_value = str(value)
            prop_params["string_value"] = string_value

        if property_constraint_type == BOOLEAN_PROPERTY_DATA_CONSTRAINT_TYPE:
            boolean_value = bool(value)
            prop_params["boolean_value"] = boolean_value

        if property_constraint_type == DATETIME_PROPERTY_DATA_CONSTRAINT_TYPE:
            datetime_value = str(value)  # TODO set to datetime
            prop_params["datetime_value"] = datetime_value

        if property_constraint_type == DOUBLE_PROPERTY_DATA_CONSTRAINT_TYPE:
            double_value = float(value)
            prop_params["double_value"] = double_value

        if property_constraint_type == FLOAT_PROPERTY_DATA_CONSTRAINT_TYPE:
            float_value = float(value)
            prop_params["float_value"] = float_value

        if property_constraint_type == GEOLOCATION_PROPERTY_DATA_CONSTRAINT_TYPE:
            geolocation_value = str(value)  # TODO set to geolocation
            prop_params["geolocation_value"] = geolocation_value

        if property_constraint_type == INTEGER_PROPERTY_DATA_CONSTRAINT_TYPE:
            integer_value = int(value)
            prop_params["integer_value"] = integer_value

        if property_constraint_type == LONG_PROPERTY_DATA_CONSTRAINT_TYPE:
            long_value = int(value)
            prop_params["long_value"] = long_value

        if property_constraint_type == TRUTH_PROPERTY_DATA_CONSTRAINT_TYPE:
            truth_value = str(value)  # TODO set to Truth
            prop_params["truth_value"] = truth_value

        if property_constraint_type == URI_PROPERTY_DATA_CONSTRAINT_TYPE:
            uri_value = str(value)  # TODO validate as URI
            prop_params["uri_value"] = uri_value
