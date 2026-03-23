"""Game data models and constants."""

# Category definitions with descriptions
categories = {
    "Einser": "Zähle nur die Einser",
    "Zweier": "Zähle nur die Zweier",
    "Dreier": "Zähle nur die Dreier",
    "Vierer": "Zähle nur die Vierer",
    "Fünfer": "Zähle nur die Fünfer",
    "Sechser": "Zähle nur die Sechser",
    "Dreierpasch": "Drei gleiche Augen, Summe aller Augen zählen",
    "Viererpasch": "Vier gleiche Augen, Summe aller Augen zählen",
    "Full House": "3 gleiche Augen und 2 gleiche Augen, 25 Punkte",
    "Kleine Straße": "4 aufeinanderfolgende Augen, 30 Punkte",
    "Große Straße": "5 aufeinanderfolgende Augen, 40 Punkte",
    "Kniffel": "5 gleiche Augen, 50 Punkte",
    "Chance": "Summe aller Augen",
}

# Fixed score categories
fixed_scores = {
    "Full House": 25,
    "Kleine Straße": 30,
    "Große Straße": 40,
    "Kniffel": 50,
}

# Upper section categories
upper_section = ["Einser", "Zweier", "Dreier", "Vierer", "Fünfer", "Sechser"]
