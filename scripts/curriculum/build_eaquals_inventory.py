#!/usr/bin/env python3
"""Build EAQUALS Core Inventory JSON from Appendix D/E structure."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "eaquals_core_inventory.json"

LEVELS = ["A1", "A2", "B1", "B2", "C1"]


def item(
    domain: str,
    num: int,
    title: str,
    levels: list[str],
    *,
    section: str | None = None,
    examples: list[str] | None = None,
) -> dict:
    prefix = {"grammar": "gr", "functions": "fn", "discourse": "dc", "lexis": "lx", "topics": "tp"}[domain]
    row: dict = {
        "id": f"{prefix}-{num:03d}",
        "title": title,
        "levels": levels,
    }
    if section:
        row["section"] = section
    if examples:
        row["examples"] = examples
    if domain == "grammar":
        row["egp_refs"] = []
    if domain in ("lexis", "topics", "functions", "discourse"):
        row["content"] = None
    return row


def build() -> dict:
    functions = [
        item("functions", 2, "Understanding and Using Numbers", ["A1"]),
        item("functions", 3, "Understanding and Using Prices", ["A1"]),
        item("functions", 4, "Telling the time", ["A1"]),
        item("functions", 5, "Directions", ["A1"]),
        item("functions", 6, "Greetings", ["A1"]),
        item("functions", 7, "Giving personal information", ["A1"]),
        item("functions", 8, "Describing habits and routines", ["A1", "A2"]),
        item("functions", 9, "Describing habits and routines", ["A2"]),
        item("functions", 10, "Describing people", ["A2"]),
        item("functions", 11, "Describing things", ["A2"]),
        item("functions", 12, "Requests", ["A2"]),
        item("functions", 13, "Suggestions", ["A2"]),
        item("functions", 14, "Advice", ["A2"]),
        item("functions", 15, "Invitations", ["A2"]),
        item("functions", 16, "Offers", ["A2"]),
        item("functions", 17, "Arrangements / -ing to meet people", ["A2"]),
        item("functions", 18, "Obligation and necessity", ["A2"]),
        item("functions", 19, "Describing places", ["A2", "B1"]),
        item("functions", 20, "Describing past experiences and storytelling", ["A2"]),
        item("functions", 21, "Checking understanding", ["B1"]),
        item("functions", 22, "Describing experiences and events", ["B1"]),
        item("functions", 23, "Describing feelings and emotion", ["B1", "B2"]),
        item("functions", 24, "Expressing opinions; agreeing and disagreeing", ["B1"]),
        item("functions", 25, "Initiating and closing conversation", ["B1"]),
        item("functions", 26, "Managing interaction", ["B1"]),
        item("functions", 27, "Critiquing and reviewing", ["B2"]),
        item("functions", 28, "Describing hopes and plans", ["B2"]),
        item("functions", 29, "Developing an argument", ["B2", "C1"]),
        item("functions", 30, "Expressing abstract ideas", ["B2"]),
        item("functions", 31, "Expressing agreement and disagreement", ["B2"]),
        item("functions", 32, "Expressing reaction, e.g. indifference", ["B2", "C1"]),
        item("functions", 33, "Speculating and hypothesising", ["B2", "C1"]),
        item("functions", 34, "Synthesizing, evaluating, glossing info", ["B2", "C1"]),
        item("functions", 35, "Conceding a point", ["C1"]),
        item("functions", 36, "Defending a point of view persuasively", ["C1"]),
        item("functions", 37, "Expressing attitudes and feelings precisely", ["C1"]),
        item("functions", 38, "Expressing certainty, probability, doubt", ["C1"]),
        item("functions", 39, "Expressing opinions tentatively, hedging", ["C1"]),
    ]

    discourse = [
        item("discourse", 46, "Connecting words (and, but, because)", ["A1"], section="markers"),
        item("discourse", 47, "Linkers: sequential – past time", ["A2"], section="markers"),
        item("discourse", 48, "Connecting words expressing cause and effect, contrast", ["B1"], section="markers"),
        item("discourse", 49, "Linkers: although, in spite of, despite", ["B2"], section="markers"),
        item("discourse", 50, "Linking devices: logical markers", ["C1"], section="markers"),
        item("discourse", 51, "Markers to structure informal spoken discourse", ["B2"], section="markers"),
        item("discourse", 52, "Markers to structure formal speech and writing", ["C1"], section="markers"),
        item("discourse", 60, "Initiating and closing conversation", ["B1"], section="functions"),
        item("discourse", 61, "Checking understanding", ["B1"], section="functions"),
        item("discourse", 62, "Managing interaction", ["B1"], section="functions"),
        item("discourse", 63, "Taking the initiative in interaction", ["B2"], section="functions"),
        item("discourse", 64, "Encouraging another speaker to continue", ["B2"], section="functions"),
        item("discourse", 65, "Interacting informally, reacting", ["B2"], section="functions"),
    ]

    grammar = [
        item("grammar", 56, "To be (including questions and negatives)", ["A1"], section="verb_forms",
             examples=["We are from South America.", "Are you French? No I'm not."]),
        item("grammar", 57, "Have got (British)", ["A1"], section="verb_forms",
             examples=["Have you got any money?", "I've got all of his CDs."]),
        item("grammar", 58, "Imperatives (+/-)", ["A1", "A2"], section="verb_forms",
             examples=["Sit down, please.", "Don't talk to the driver."]),
        item("grammar", 59, "Questions", ["A1", "A2"], section="questions",
             examples=["Do you like dancing?", "What is your name?"]),
        item("grammar", 61, "Wh-questions in the past", ["A2"], section="questions",
             examples=["Where did she go to university?", "When did it happen?"]),
        item("grammar", 64, "Present simple", ["A1", "A2"], section="present",
             examples=["She eats fruit every day.", "The plane lands at six."]),
        item("grammar", 65, "Present continuous", ["A1", "A2"], section="present",
             examples=["It's raining again.", "I am staying with Hilary at the moment."]),
        item("grammar", 67, "Past simple", ["A1", "A2"], section="past",
             examples=["She fell and broke her leg.", "He gave me a nice present."]),
        item("grammar", 68, "Past simple (to be) / Past continuous", ["A1", "A2"], section="past",
             examples=["We were happy there.", "I was living in Spain when I met her."]),
        item("grammar", 69, "Used to", ["A2"], section="past",
             examples=["She used to be a ballet dancer."]),
        item("grammar", 74, "Going to", ["A1", "A2"], section="future",
             examples=["We are going to make a pizza this evening."]),
        item("grammar", 75, "Present continuous for the future (arrangements)", ["A2"], section="future",
             examples=["I'm seeing him at 11.00 this morning."]),
        item("grammar", 76, "Future time (will & going to)", ["A2", "B1"], section="future",
             examples=["I'll tell him about the party."]),
        item("grammar", 77, "Future continuous", ["B1", "B2"], section="future"),
        item("grammar", 78, "Future perfect / Future perfect continuous", ["B2", "C1"], section="future"),
        item("grammar", 81, "Present perfect", ["A2", "B1"], section="present_perfect",
             examples=["Have you ever been to Greece?", "I've known him for 5 years."]),
        item("grammar", 82, "Present perfect / Past simple", ["B1", "B2"], section="present_perfect"),
        item("grammar", 83, "Present perfect continuous", ["B1", "B2"], section="present_perfect"),
        item("grammar", 85, "I'd like", ["A1"], section="gerund_infinitive",
             examples=["I'd like a cup of coffee.", "I'd like to go home."]),
        item("grammar", 86, "Verb + -ing (like/hate/love)", ["A1", "A2"], section="gerund_infinitive",
             examples=["I love swimming.", "I hate being late."]),
        item("grammar", 87, "To + infinitive (express purpose)", ["A2"], section="gerund_infinitive",
             examples=["I go jogging to get fit."]),
        item("grammar", 88, "Verb + to + infinitive", ["A2", "B1"], section="gerund_infinitive",
             examples=["She wants to go home now."]),
        item("grammar", 90, "Zero and first conditional", ["A2", "B1"], section="conditionals",
             examples=["If I eat eggs I feel sick.", "If it rains, I will stay in."]),
        item("grammar", 91, "Second and third conditional", ["B1", "B2"], section="conditionals"),
        item("grammar", 92, "Mixed conditionals", ["B2", "C1"], section="conditionals"),
        item("grammar", 93, "Wish / if only & regrets", ["B2", "C1"], section="conditionals"),
        item("grammar", 95, "Phrasal verbs, common", ["A2"], section="phrasal_verbs",
             examples=["He got up at 6 o'clock.", "Put your coat on."]),
        item("grammar", 96, "Phrasal verbs, extended / splitting", ["B1", "B2"], section="phrasal_verbs"),
        item("grammar", 97, "Simple passive", ["B1"], section="passives"),
        item("grammar", 98, "All passive forms", ["B2", "C1"], section="passives"),
        item("grammar", 99, "Reported speech (range of tenses)", ["B1", "B2"], section="other_verbs"),
        item("grammar", 100, "Relative clauses", ["B1", "B2", "C1"], section="other_verbs"),
        item("grammar", 104, "Can/can't (ability)", ["A1"], section="modals_can",
             examples=["I can't swim.", "He can speak Spanish."]),
        item("grammar", 105, "Can/could (functional)", ["A1", "A2"], section="modals_can",
             examples=["Can I help?", "Could I use your phone?"]),
        item("grammar", 107, "Might, may", ["A2", "B1"], section="modals_possibility",
             examples=["She might come.", "John may know the answer."]),
        item("grammar", 108, "Possibly, probably, perhaps", ["B1"], section="modals_possibility"),
        item("grammar", 109, "Must/can't (deduction)", ["B1", "B2"], section="modals_possibility"),
        item("grammar", 112, "Must/mustn't", ["A2", "B1"], section="modals_obligation",
             examples=["You must get to work on time.", "You mustn't smoke here."]),
        item("grammar", 113, "Have to", ["A2", "B1"], section="modals_obligation",
             examples=["Students have to fill in a form."]),
        item("grammar", 115, "Should", ["A2", "B1"], section="modals_obligation",
             examples=["You should stay in and study tonight."]),
        item("grammar", 116, "Ought to", ["B2"], section="modals_obligation"),
        item("grammar", 117, "Need to / needn't", ["B2"], section="modals_obligation"),
        item("grammar", 118, "Should have / might have / etc.", ["B1", "B2"], section="modals_past"),
        item("grammar", 119, "Can't have / needn't have", ["B2", "C1"], section="modals_past"),
        item("grammar", 121, "Countable and uncountable nouns", ["A1", "A2"], section="nouns",
             examples=["How much money do you have?", "Do you like cheese?"]),
        item("grammar", 123, "There is / there are", ["A1"], section="nouns",
             examples=["There's a bank near the station.", "Are there many seats?"]),
        item("grammar", 125, "Simple personal pronouns", ["A1", "A2"], section="pronouns",
             examples=["I bought a dictionary.", "They live in Newcastle."]),
        item("grammar", 127, "Possessive adjectives", ["A1", "A2"], section="pronouns",
             examples=["This is my seat.", "Is this your pen?"]),
        item("grammar", 128, "Possessive 's", ["A1", "A2"], section="pronouns",
             examples=["It's Mary's turn to buy coffee."]),
        item("grammar", 129, "Possessive pronouns", ["A1", "A2"], section="pronouns",
             examples=["No. It's mine.", "Is that their car?"]),
        item("grammar", 131, "Prepositions, common", ["A1", "A2"], section="prepositions",
             examples=["He is sitting at the table.", "We went to Sardinia last year."]),
        item("grammar", 132, "Prepositional phrases (time and movement)", ["A2"], section="prepositions",
             examples=["On Tuesdays she goes to college."]),
        item("grammar", 133, "Prepositions of place and time (in/on/at)", ["A1", "A2"], section="prepositions",
             examples=["I'll see you in December.", "It starts at 6 o'clock."]),
        item("grammar", 135, "Articles: definite, indefinite", ["A1", "A2"], section="articles",
             examples=["She has a dog.", "Your jacket is on the chair."]),
        item("grammar", 136, "Articles with countable/uncountable", ["A2", "B1"], section="articles"),
        item("grammar", 137, "Zero article / superlatives with the", ["B2"], section="articles"),
        item("grammar", 141, "Determiners: basic (any, some, a lot of)", ["A1", "A2"], section="determiners",
             examples=["Do you have any cheese?", "I'd like some vegetables."]),
        item("grammar", 142, "Determiners: wider range", ["B1", "B2"], section="determiners"),
        item("grammar", 145, "Adjectives: common", ["A1", "A2"], section="adjectives",
             examples=["She is wearing a red skirt."]),
        item("grammar", 146, "Adjectives: demonstrative", ["A1", "A2"], section="adjectives",
             examples=["This pizza is really good.", "Those oranges look nice."]),
        item("grammar", 147, "Comparative and superlative adjectives", ["A1", "A2", "B1"], section="adjectives",
             examples=["She's taller than Michelle.", "Tom is the oldest in the class."]),
        item("grammar", 148, "Comparisons with fewer and less", ["B2"], section="adjectives"),
        item("grammar", 152, "Adverbs of frequency", ["A1", "A2"], section="adverbs",
             examples=["We always go shopping on Saturdays.", "I never go to the gym."]),
        item("grammar", 153, "Adverbs of place, manner and time", ["A2", "B1"], section="adverbs"),
        item("grammar", 154, "Adverbial phrases; word order", ["A2", "B1"], section="adverbs"),
        item("grammar", 155, "Comparative and superlative adverbs", ["B2"], section="adverbs"),
        item("grammar", 156, "Inversion with negative adverbials", ["C1"], section="adverbs"),
        item("grammar", 161, "Intensifiers: very basic (very, really)", ["A1", "A2"], section="intensifiers",
             examples=["She's a very tall girl.", "John is a really good friend."]),
        item("grammar", 162, "Intensifiers: too, enough", ["B1"], section="intensifiers"),
        item("grammar", 163, "Wide range (extremely, much too)", ["B2", "C1"], section="intensifiers"),
        item("grammar", 164, "Complex question tags", ["B2"], section="questions"),
        item("grammar", 165, "Narrative tenses", ["B2", "C1"], section="past"),
        item("grammar", 166, "Inversion / cleft sentences (advanced)", ["C1"], section="other_verbs"),
    ]

    lexis = [
        item("lexis", 167, "Nationalities and countries", ["A1", "A2"]),
        item("lexis", 168, "Personal information", ["A1", "A2"]),
        item("lexis", 169, "Food and drink", ["A1", "A2"]),
        item("lexis", 170, "Things in the town, shops and shopping", ["A1", "A2", "B1"]),
        item("lexis", 171, "Travel and services vocabulary", ["A1", "A2", "B1"]),
        item("lexis", 172, "Verbs, basic", ["A1", "A2"]),
        item("lexis", 173, "Clothes", ["A2"]),
        item("lexis", 174, "Colours", ["A2"]),
        item("lexis", 175, "Dimensions", ["A2"]),
        item("lexis", 176, "Ways of travelling", ["A2"]),
        item("lexis", 177, "Collocation", ["B1", "B2", "C1"]),
        item("lexis", 178, "Colloquial language", ["B1", "B2", "C1"]),
        item("lexis", 179, "Approximating (vague language)", ["C1"]),
        item("lexis", 180, "Formal and informal registers", ["C1"]),
        item("lexis", 181, "Idiomatic expressions", ["C1"]),
        item("lexis", 182, "Eliminating false friends", ["C1"]),
    ]

    topics = [
        item("topics", 190, "Family life", ["A2"]),
        item("topics", 191, "Hobbies and pastimes", ["A2", "B1"]),
        item("topics", 192, "Holidays", ["A2", "B1"]),
        item("topics", 193, "Work and jobs", ["A2", "B1"]),
        item("topics", 194, "Shopping", ["A2", "B1"]),
        item("topics", 195, "Leisure activities", ["A2", "B1"]),
        item("topics", 196, "Education", ["B1", "B2", "C1"]),
        item("topics", 197, "Film", ["B1", "B2", "C1"]),
        item("topics", 198, "Books and literature", ["B2", "C1"]),
        item("topics", 199, "News, lifestyles and current affairs", ["B1", "B2", "C1"]),
        item("topics", 200, "Media", ["B1", "B2", "C1"]),
        item("topics", 201, "Arts", ["B2", "C1"]),
        item("topics", 202, "Scientific development", ["C1"]),
        item("topics", 203, "Technical and legal language", ["C1"]),
    ]

    return {
        "meta": {
            "source": "EAQUALS_British_Council_Core_Curriculum_April2011",
            "appendix": "D",
            "url": "https://www.eaquals.org/wp-content/uploads/EAQUALS_British_Council_Core_Curriculum_April2011.pdf",
            "levels": LEVELS,
            "note": "Grammar includes Appendix E examples; functions/lexis/topics are level shells only.",
        },
        "domains": {
            "functions": functions,
            "discourse": discourse,
            "grammar": grammar,
            "lexis": lexis,
            "topics": topics,
        },
    }


def main() -> None:
    payload = build()
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    counts = {k: len(v) for k, v in payload["domains"].items()}
    print(f"Wrote {OUT}")
    print("Counts:", counts)


if __name__ == "__main__":
    main()
