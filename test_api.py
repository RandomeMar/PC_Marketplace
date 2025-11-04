import rapidfuzz


choices = ["Cool guy", "cool girl", "Really awesome COOL GUY", "Bad girl", "cool awesome really ugly guy is not awesome", "cxol guy"]
choices = [choice.lower().strip() for choice in choices]

query = "COOL GUY".lower()

decision = rapidfuzz.process.extract(query, choices, scorer=rapidfuzz.fuzz.token_set_ratio, limit=10)

for i in decision:
    print(i)