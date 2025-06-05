
# Use in TruthProperty
# Values:
# YES, NO, UNKNOWN, MU

# case like:
# node123.property123
# would be a valid property if property123 is a value property of
# the node
# would be a valid property with a truth unknown value if the
# property is valid for the node but no value it set
# would be a valid property with a truth mu value if the
# property does not exist for that node

# instead of these semantics, currently treating graph objects similar to dict
# with properties as keys

class Truth:
    pass
