"""
Hinglish and Code-Mixed Semantic Normalizer.
Enriches Romanized Hindi and colloquial chat phrases with English semantic tags
so that dense vector embeddings bridge concepts seamlessly.
"""

import re

HINGLISH_DICT = {
    # Housing, Flat & Rent
    "kiraya": "rent monthly payment lease housing accommodation",
    "kamra": "room bedroom master space dwelling",
    "kamre": "rooms bedrooms flats",
    "ghar": "home house flat apartment residence",
    "flat": "flat apartment housing 3BHK accommodation",
    "shifting": "moving relocation shift pack move in",
    "broker": "agent middleman realtor broker landlord",
    "dalal": "broker agent fee middleman",
    "deposit": "security advance deposit payment upfront guarantee",
    "advance": "upfront security deposit advance token payment",
    "fridge": "refrigerator kitchen appliance electronic cooling food storage",
    "refrigerator": "fridge appliance kitchen cooling",
    "chabi": "keys key handover lock possession",
    "agreement": "contract lease rent agreement paperwork documentation",
    "landlord": "owner landlord property owner broker",
    "makaan": "house building flat property",
    "makan": "house building flat property",
    "bijli": "electricity power utility bill",
    "paani": "water supply utility bill",
    "maid": "housekeeper cleaning cook helper",
    "bhk": "bedroom hall kitchen apartment flat",

    # Travel, Roadtrip & Mountain Trip
    "gaadi": "car vehicle automobile transport SUV ride drive motor",
    "gadi": "car vehicle automobile transport SUV ride drive motor",
    "pahad": "mountain hills hillstation nature summit peaks",
    "pahadon": "mountains hills hillstation holiday getaway nature high country",
    "cottage": "cabin wooden accommodation cottage stay hotel room homestay lodge",
    "stay": "accommodation hotel room cottage homestay resort airbnb lodging",
    "hotel": "hotel stay cottage room booking accommodation lodge",
    "airbnb": "homestay cottage stay accommodation booking",
    "manali": "Manali Himachal hill station mountain destination getaway",
    "kasol": "Kasol Himachal mountains hill valley getaway",
    "himachal": "Himachal mountains northern hills destination vacation trip",
    "scorpio": "Scorpio SUV car vehicle four wheeler transport automobile",
    "suv": "car vehicle Scorpio automobile transport four wheeler",
    "altitude": "height elevation mountain sickness high altitude acute mountain illness",
    "chakkar": "dizziness dizzy sick unwell vomiting nausea vertigo mountain sickness ill",
    "tabiyat": "health condition sick unwell illness fever recovery unwell",
    "bimar": "sick ill unwell fever cold illness health medical",
    "petrol": "fuel gas diesel toll expenses car fuel refuel",
    "diesel": "fuel gas petrol expenses car transport",
    "toll": "toll plaza tax road expense travel cost highway charge",
    "rasta": "road route highway way journey path drive route",
    "pahunch": "reach arrive arrival reached reached destination",
    "nikal": "leave depart start journey departure checkout commence",
    "bonfire": "campfire bonfire night party outdoor fire logs warmth",
    "driver": "driver chauffeur self drive piloting navigate steering",
    "selfdrive": "self drive driving vehicle own drive chauffeur free",
    "chalaunga": "will drive driving piloting navigate steering vehicle",
    "chalayega": "will drive driving vehicle driver chauffeur",
    "servicing": "inspection maintenance tuning repair vehicle check mechanics",
    "tyre": "wheels tires inspection vehicle condition air pressure",

    # Finance, Accounts & Budget
    "hisab": "accounts budget finance expense tracking money accounting calculation ledger",
    "hisaab": "accounts budget finance expense tracking money accounting calculation ledger",
    "kitab": "record book ledger sheet spreadsheet excel track records accounting table",
    "paisa": "money cash payment amount cost funds currency budget financial",
    "paise": "money cash payment amount cost funds currency budget financial",
    "rupaye": "rupees INR money currency cash funds expenditure",
    "rs": "rupees INR money payment cash cost sum",
    "inr": "rupees money currency payment cost sum",
    "hazaar": "thousand 1000 rupees k amount figure quantity",
    "hazar": "thousand 1000 rupees k amount figure quantity",
    "k": "thousand 1000 rupees",
    "lakh": "hundred thousand 100000 lac financial sum amount",
    "lac": "hundred thousand 100000 lakh financial sum amount",
    "split": "divide share equally split splitwise contribution per head breakdown",
    "chaunvan": "fifty four 54 54000 monthly rent amount figure sum",
    "dhaii": "two and half 2.5 250000 deposit advance sum figure amount",
    "dhai": "two and half 2.5 250000 deposit advance sum figure amount",
    "kharcha": "expense spend cost budget expenditure outlay spending money",
    "kharch": "expense spend cost budget expenditure outlay spending money",
    "udhaar": "loan borrow lend due payback debt outstanding credit",
    "gpay": "upi payment google pay transfer online transaction sent paid",
    "phonepe": "upi payment transfer online transaction sent paid",
    "paytm": "upi payment transfer online transaction sent paid",
    "transfer": "sent paid transferred transaction payment settlement completed",
    "bheja": "sent transferred paid remitted delivered wired",
    "bhejdia": "sent transferred paid remitted delivered wired",
    "bhej": "send transfer pay remit forward wire",
    "chuka": "repay settle clear payback balance debt",
    "settle": "settle payment accounts clear splitwise done reconciled",
    "budget": "budget financial cap limit maximum expenditure ceiling allowance",

    # Tech, Software & Hackathon
    "repo": "repository GitHub git code codebase version control software project",
    "deck": "presentation slides pitch deck pitchdeck software showcase slides deck",
    "pitch": "presentation pitch deck pitchdeck startup showcase demo proposal",
    "screen": "screen display interface UI demo recording video walkthrough",
    "recording": "recording video demo capture screen recording walkthrough presentation",
    "video": "video recording demo presentation clip upload media footage",
    "demo": "demonstration prototype showcase preview software trial presentation",
    "fork": "fork clone branch copy repository github git",
    "code": "programming codebase software implementation code python logic",
    "backend": "server API endpoints backend database FastAPI server logic web service",
    "frontend": "user interface UI client web React frontend visual components screens",
    "routes": "API endpoints URL routes backend controllers handlers service",
    "models": "database schema models tables entities Postgres database schema",
    "database": "database storage DB Postgres SQLite SQL tables persistence relational",
    "postgres": "Postgres PostgreSQL relational database SQL DB storage data persistent",
    "nosql": "NoSQL document MongoDB non-relational database storage store",
    "banate": "build develop create implement program engineer code construct",
    "banayenge": "will build develop create implement program code construct",
    "sambhalta": "handle manage develop responsible build take ownership implement",
    "sambhalunga": "will handle manage develop build take ownership implement",
    "tareekh": "date deadline schedule timeline day calendar cutoff",
    "deadline": "deadline final due date submission cutoff time limit closing",
    "submit": "submit file deliver upload hand in finalize entry present",
    "upload": "upload submit publish push host video deck files web",
    "raat": "night evening midnight late night time clock dusk",
    "barah": "twelve 12 midnight 12:00 AM clock hour midday",
    "hackathon": "competition coding challenge hackathon startup project sprint event",

    # Confirmation, Agreement & Decisions
    "pakka": "confirmed sure definite settled locked finalized agreed guaranteed",
    "fix": "fixed confirmed agreed settled locked decided immutable",
    "sorted": "done resolved settled finalized fixed cleared complete agreed",
    "done": "done completed confirmed agreed finished settled executed",
    "theek": "okay fine alright agreed confirm understood approved acknowledged",
    "thik": "okay fine alright agreed confirm understood approved acknowledged",
    "sahi": "correct right accurate perfect sounds good agree spot on",
    "badhiya": "great excellent awesome sounds good good plan fine",
    "chalo": "let us proceed begin commence start agree embark decide",
    "final": "final finalized confirmed locked decided conclusive definitive",
    "decide": "decided decision conclusion settlement agreement finalized determined",
    "faisla": "decision choice resolution ruling verdict determination",

    # Conversational Markers
    "yaar": "friend buddy pal companion fellow",
    "bhai": "brother bro dude friend guy fellow teammate",
    "bhaii": "brother bro dude friend guy fellow teammate",
    "bro": "brother buddy mate friend pal dude",
    "acha": "okay good understood alright well noted acknowledged",
    "achha": "okay good understood alright well noted acknowledged",
    "kal": "tomorrow yesterday upcoming day previous day",
    "aaj": "today tonight current day presently",
    "parso": "day after tomorrow day before yesterday future",
    "subah": "morning AM early hours daybreak",
    "shaam": "evening PM dusk sunset twilight",
    "dopahar": "afternoon midday noon lunch time",
    "zyada": "more extra excessive high surplus surplus",
    "kam": "less lower cheap minimal modest economical",
    "sab": "everyone all everybody team entire members group",
    "karo": "do execute perform complete finish carry out",
    "scene": "plan situation status context update arrangement",
    "milte": "meet catchup assemble gather convene congregate",
    "swiggy": "food delivery restaurant meal dinner lunch snacks online order",
    "zomato": "food delivery restaurant meal dinner lunch snacks online order",
    "biryani": "food lunch dinner ordering restaurant meal feast",
    "chai": "tea beverage refreshment break beverage beverage",
    "nashta": "breakfast morning snacks meal food refreshment"
}


def normalize_text(text: str) -> str:
    """
    Appends semantic English concept glosses to code-mixed Hinglish text.
    Extracts tokens, matches against HINGLISH_DICT, and yields an enriched representation.
    """
    if not text:
        return ""
    tokens = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    matched_glosses = set()

    for token in tokens:
        if token in HINGLISH_DICT:
            gloss_words = HINGLISH_DICT[token].split()
            matched_glosses.update(gloss_words)

    if matched_glosses:
        gloss_str = " ".join(sorted(matched_glosses))
        return f"{text} | [SEMANTIC_TAGS: {gloss_str}]"
    return text


def clean_query_text(query: str) -> str:
    """
    Removes extraneous punctuation and normalizes whitespace in search queries.
    """
    cleaned = re.sub(r"[^\w\s\-\:\.\,\?]", " ", query)
    return " ".join(cleaned.split())
