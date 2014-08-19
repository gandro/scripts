#!/usr/bin/env python
import math
import random
import logging

#
# Implements the Wright System for single transferable vote elections.
# See: http://is.gd/dpmc_gov_au_wright_system_pdf
#

class Candidate():
    def __init__(self, name):
        self.name = name
        # Allocated votes
        self.votes = set()
        # Candidate’s Total Value of votes (Ctvv)
        self.total_value = 0.0

    def alloc_vote(self, vote):
        self.total_value += vote.value
        self.votes.add(vote)

    def __lt__(self, other):
        return other.total_value < self.total_value

    def __repr__(self):
        return "Candidate({} : {:5f})".format(self.name, self.total_value)

    def __hash__(self):
        return self.name.__hash__()

class Vote():
    def __init__(self, id, preference):
        self.id = id
        # voter’s preference in ascending order
        for c in preference: assert isinstance(c, Candidate)
        self.preference = preference
        # Value of the Vote (Vv)
        self.value = 1.0

    def get_preference(self):
        return self.preference[0] if self.preference else None

    def get_preference_excluding(self, excluding):
        for candidate in self.preference:
            if candidate not in excluding:
                return candidate

    def __repr__(self):
        return "Vote({})".format(self.id)

    def __hash__(self):
        return self.id.__hash__()

class WrightSystem():

    def __init__(self, vacancies, ballots):
        self.vacancies = vacancies

        self.provisional_winners = set()
        self.candidates = dict()
        self.votes = set()

        for id, preference in ballots.items():
            preference = [self.add_candidate(c) for c in preference]
            self.votes.add(Vote(id, preference))

        self.elect()

    def add_candidate(self, name):
        if name not in self.candidates:
            self.candidates[name] = Candidate(name)
        return self.candidates[name]

    #
    # Wright System
    #

    def elect(self):
        round_nr = 0

        while not self.check_all_vacancies_filled():
            round_nr += 1

            logging.info("Starting round no. {}:".format(round_nr))

            self.distribution_of_preferences()
            if self.check_all_vacancies_filled():
                return

            while self.check_if_candidates_surplus():
                self.calc_and_distribute_surplus()
                if self.check_all_vacancies_filled():
                    return

            logging.info("Votes after surplus distribution:")
            logging.info("=================================")
            for c in self.candidates.values():
                logging.info(c)
            logging.info("=================================")

            self.exclusion_of_candidates()


    def distribution_of_preferences(self):
        # reset
        self.provisional_winners = set()
        self.total_votes = 0.0
        for candidate in self.candidates.values():
            candidate.total_value = 0.0
            candidate.votes.clear()

        # (a) remove ballots exhausted-without-value
        exhausted = [v for v in self.votes if not v.preference]
        logging.info("Removing vote exhausted-without-value: {}".
                        format(exhausted))
        self.votes.difference_update(exhausted)

        for vote in self.votes:
            # (b) assign value of vote of one
            vote.value = 1.0

            # (c) ascertain and assign the Candidate’s Total Value of the Vote
            candidate = vote.get_preference()
            candidate.alloc_vote(vote)

            # (d) ascertain and assign the Total Vote (Tv) value
            self.total_votes += vote.value

        # (e) calculate the quota
        self.quota = math.floor(self.total_votes/(1+self.vacancies))+1.0
        logging.info("Calculated quota: {:5f}".format(self.quota))

        # provisional declaration of elected candidates
        self.provisional_winners = [c for c in self.candidates.values()
                                        if c.total_value >= self.quota]

    def check_all_vacancies_filled(self):
        return (len(self.candidates) <= self.vacancies
                or len(self.provisional_winners) >= self.vacancies)

    def get_winners(self):
        if len(self.candidates) <= self.vacancies:
            return list(self.candidates.values())
        elif len(self.provisional_winners) >= self.vacancies:
            return list(self.provisional_winners)
        else:
            raise Exception("tried to get winners without election!")

    def check_if_candidates_surplus(self):
        return any(c.total_value > self.quota for c in self.candidates.values())

    def calc_and_distribute_surplus(self):
        candidates_with_surplus = (c for c in self.candidates.values()
                                    if c.total_value > self.quota)
        candidate = max(candidates_with_surplus)

        # calculation of the Candidate’s Surplus Value
        surplus = candidate.total_value - self.quota

        logging.info("Surplus value of candidate '{}': {:5f}".
                        format(candidate.name, surplus))

        # calculation of the Surplus Transfer Value
        surplus_transfer_value = surplus / candidate.total_value

        for vote in candidate.votes:
            # calculation of new value of the vote
            vote.value *= surplus_transfer_value

            # get next preference exculding provisional winners
            excluding = self.provisional_winners
            next_preference = vote.get_preference_excluding(excluding)

            # exhausted ballot papers to be set aside
            if not next_preference:
                logging.info("Vote is exhausted-with-value: {}".format(vote))
                continue

            logging.info("Adding STV({:5f}) of {} to {}".
                            format(vote.value, vote, next_preference))
            next_preference.alloc_vote(vote)

        # set value to quota of candidate whose surplus has been distributed
        candidate.total_value = self.quota

         # update provisional elected candidates
        self.provisional_winners = [c for c in self.candidates.values()
                                        if c.total_value >= self.quota]

    def exclusion_of_candidates(self):
        min_total_val = min(c.total_value for c in self.candidates.values())
        minimum_votes = [c for c in self.candidates.values()
                    if c.total_value == min_total_val]

        if len(minimum_votes) > 1:
            logging.warning("Excluding candidate by lot!")

        excluded = random.choice(minimum_votes)

        logging.info("Excluding: {}".format(excluded))

        for vote in self.votes:
            if excluded in vote.preference:
                vote.preference.remove(excluded)

        del self.candidates[excluded.name]


VACANCIES = 4
INITIAL_BALLOTS = {
    1 : ["A", "B", "D", "C"],
    2 : ["A", "C", "B", "D", "E"],
    3 : ["C"],
    4 : ["C", "A", "E"],
    5 : ["C", "B", "A", "F", "E", "D", "G"],
    6 : ["C", "B", "D", "E"],
    7 : ["C", "F", "B", "D", "E", "H"],
    8 : ["C", "D", "F", "E", "H", "A"],
    9 : ["D", "E", "C"],
   10 : ["E", "B", "D", "C", "A", "F"],
   11 : ["E", "D", "C", "A"],
   12 : ["F"],
   13 : ["F", "C", "H"],
   14 : ["F", "G", "E", "I", "H", "J"],
   15 : ["F", "H", "G"],
   16 : ["G", "F", "E", "I"],
   17 : ["H", "F", "J", "A", "I"],
   18 : ["H", "G", "I", "F"],
   19 : ["I", "J", "F"],
   20 : ["I", "J", "H"],
   21 : ["J", "I", "H", "F", "E"],
}

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

ws = WrightSystem(VACANCIES, INITIAL_BALLOTS)
winners = ws.get_winners()
for winner in sorted(winners):
    print(winner)
