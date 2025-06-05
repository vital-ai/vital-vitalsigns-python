from typing import List
from vital_ai_vitalsigns.query.solution import Solution


class SolutionList:

    # in-order list of solutions
    # has offset and limit that produced the list
    # may have query representation that produced the list

    def __init__(self, solution_list: List[Solution],
                 limit: int | None = None,
                 offset: int | None = None
                 ):

        self.solution_list = solution_list
        self.limit = limit
        self.offset = offset


