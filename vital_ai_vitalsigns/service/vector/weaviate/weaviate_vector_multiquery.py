

class WeaviateVectorMultiQuery:
    pass

# case of querying collection that has two or more vectors

# related PR: https://github.com/weaviate/weaviate/pull/4955

# case would be querying:
# a vector for the "content"
# and a vector for the "type"

# as example, a collection of Events with an
# event type such as "company founding"
# and content like "openai"
# which would have info about the founding of openai

# in some cases the number of close matches would be roughly equal in
# number, in which case the vector queries could be done in parallel
# and then intersected

# in other cases, the number of close matches in a vector may be
# significantly more than the others

# in such a case, it would be better to query using the more specific cases
# and then filter with the more generic case

# in the above example, there would be many "company founding" events
# and relatively few openai events.
# so it would be better to generate the openai events and then filter those down
# to the company founding event.

# it appears we can get a count of vectors near text or a vector
# via the api, using a distance/certainty.

# so we could get a count for "company founding" and "openai" with
# a relatively close distance/high certainty and if these counts are
# very different, order them accordingly

# initially could specify this directly by passing in a parameter to
# do them in order or in parallel, and initially we would have the in order
# case of content specific then filtered by type





