from nltk.corpus import wordnet
import nltk
from nltk.corpus.reader import Synset


def process_relationships(synset):
    relationships = {
        "Hypernyms": synset.hypernyms(),
        "Hyponyms": synset.hyponyms(),
        "Instance Hypernyms": synset.instance_hypernyms(),
        "Instance Hyponyms": synset.instance_hyponyms(),
        "Member Meronyms": synset.member_meronyms(),
        "Part Meronyms": synset.part_meronyms(),
        "Substance Meronyms": synset.substance_meronyms(),
        "Member Holonyms": synset.member_holonyms(),
        "Part Holonyms": synset.part_holonyms(),
        "Substance Holonyms": synset.substance_holonyms(),
        "Entailments": synset.entailments(),
        "Causes": synset.causes(),
        "Also See": synset.also_sees(),
        "Verb Groups": synset.verb_groups(),
        "Similar To": synset.similar_tos()
    }

    # Collect antonyms separately
    antonyms = []
    for lemma in synset.lemmas():
        if lemma.antonyms():
            antonyms.extend(lemma.antonyms())
    relationships["Antonyms"] = antonyms

    for relation_name, related_synsets in relationships.items():
        if related_synsets:  # Only print if there are related synsets
            print(f"{relation_name}:")
            for related_synset in related_synsets:
                print(f"  {related_synset.name()}")
                # - {related_synset.definition()
            print()


def main():
    print('Test Wordnet')
    nltk.download('wordnet')

    """
    AdjectiveSynsetNode
    AdverbSynsetNode
    NounSynsetNode
    VerbSynsetNode
    """

    """
    Edge_hasWordnetPointer
        Edge_WordnetAlsoSee
        Edge_WordnetAntonym
        Edge_WordnetAttribute
        Edge_WordnetCause
        Edge_WordnetDerivationallyRelatedForm
        Edge_WordnetDerivedFromAdjective
        Edge_WordnetDomainOfSynset_Region
        Edge_WordnetDomainOfSynset_Topic
        Edge_WordnetDomainOfSynset_Usage
        Edge_WordnetEntailment
        Edge_WordnetHypernym
        Edge_WordnetHyponym
        Edge_WordnetInstanceHypernym
        Edge_WordnetInstanceHyponym
        Edge_WordnetMemberHolonym
        Edge_WordnetMemberMeronym
        Edge_WordnetMemberOfThisDomain_Region
        Edge_WordnetMemberOfThisDomain_Topic
        Edge_WordnetMemberOfThisDomain_Usage
        Edge_WordnetPartHolonym
        Edge_WordnetParticiple
        Edge_WordnetPartMeronym
        Edge_WordnetPertainym_PertainsToNouns
        Edge_WordnetSimilarTo
        Edge_WordnetSubstanceHolonym
        Edge_WordnetSubstanceMeronym
        Edge_WordnetVerbGroup
    """

    syns = wordnet.synsets("jump")

    # wordnet.all_synsets('n')

    """
    'n': Noun
    'v': Verb
    'a': Adjective
    's': Adjective Satellite
    'r': Adverb
    """

    print(syns)

    for synset in wordnet.all_eng_synsets('n'):

        print(f"Synset: {synset.name()}")
        print(f"Definition: {synset.definition()}")
        process_relationships(synset)
        print("=" * 60)

    # for synset in wordnet.all_synsets():
        print(synset)
        print("Definition:", synset.definition())
        print("Examples:", synset.examples())
        print("Lemmas:", synset.lemmas())
        print()

        print(f"Synset: {synset}")
        print(f"Definition: {synset.definition()}")

        # Hypernyms (more general terms)
        hypernyms = synset.hypernyms()
        print("Hypernyms:", hypernyms)

        # Hyponyms (more specific terms)
        hyponyms = synset.hyponyms()
        print("Hyponyms:", hyponyms)

        # Instance Hypernyms (specific instances of the term)
        instance_hypernyms = synset.instance_hypernyms()
        print("Instance Hypernyms:", instance_hypernyms)

        # Instance Hyponyms (specific instances of the term)
        instance_hyponyms = synset.instance_hyponyms()
        print("Instance Hyponyms:", instance_hyponyms)

        # Member Meronyms (members of the term)
        member_meronyms = synset.member_meronyms()
        print("Member Meronyms:", member_meronyms)

        # Part Meronyms (parts of the term)
        part_meronyms = synset.part_meronyms()
        print("Part Meronyms:", part_meronyms)

        # Substance Meronyms (substances of the term)
        substance_meronyms = synset.substance_meronyms()
        print("Substance Meronyms:", substance_meronyms)

        # Member Holonyms (wholes that the term is a member of)
        member_holonyms = synset.member_holonyms()
        print("Member Holonyms:", member_holonyms)

        # Part Holonyms (wholes that the term is a part of)
        part_holonyms = synset.part_holonyms()
        print("Part Holonyms:", part_holonyms)

        # Substance Holonyms (wholes that the term is a substance of)
        substance_holonyms = synset.substance_holonyms()
        print("Substance Holonyms:", substance_holonyms)

        # Entailments (verbs that entail the synset verb)
        entailments = synset.entailments()
        print("Entailments:", entailments)

        # Causes (verbs that cause the synset verb)
        causes = synset.causes()
        print("Causes:", causes)

        # Also See (related terms)
        also_sees = synset.also_sees()
        print("Also See:", also_sees)

        # Verb Groups (verbs that are similar in meaning)
        verb_groups = synset.verb_groups()
        print("Verb Groups:", verb_groups)

        # Similar To (adjectives that are similar in meaning)
        similar_tos = synset.similar_tos()
        print("Similar To:", similar_tos)

        # Antonyms (opposites)
        antonyms = []
        for lemma in synset.lemmas():
            if lemma.antonyms():
                antonyms.extend(lemma.antonyms())
        print("Antonyms:", antonyms)

        print("=" * 60)


if __name__ == "__main__":
    main()
