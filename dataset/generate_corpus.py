"""
Generates realistic 4200+ Hinglish group chat messages spanning 6 months (May-Oct 2024)
with 8 participants, 3 major decision threads, realistic messiness (typos, one-word replies,
forwards, banter), and 40 gold-standard benchmark queries with >= 10 zero-lexical overlap test cases.
"""

import os
import json
import random
from datetime import datetime, timedelta

TARGET_DIR = r"D:\group-chat-search\dataset"
os.makedirs(TARGET_DIR, exist_ok=True)

random.seed(42)

PARTICIPANTS = [
    "Kabir Sharma",    # Organizer, tech lead
    "Priya Patel",     # Budget & finance tracker
    "Rohan Mehta",     # Impulsive, memes, driver
    "Ananya Iyer",     # Foodie, aesthetic, design
    "Vikram Malhotra", # Backend dev, practical, blunt
    "Tanvi Joshi",     # Flat coordinator, logistics
    "Arjun Nair",      # Night owl, chill, brief
    "Sneha Rao"        # UI/UX designer, structured
]

# Personality weights for filler generation
P_WEIGHTS = [0.16, 0.14, 0.15, 0.13, 0.12, 0.12, 0.08, 0.10]

START_DATE = datetime(2024, 5, 1, 9, 0, 0)
END_DATE = datetime(2024, 10, 31, 23, 30, 0)
TOTAL_DAYS = (END_DATE - START_DATE).days # ~183 days

# --------------------------------------------------------------------------
# Filler message pools
# --------------------------------------------------------------------------
ONE_WORD_REPLIES = [
    "haan", "hn", "k", "ok", "done", "lol", "sahi", "sahi hai", "theek", "thik",
    "badhiya", "cool", "sorted", "yo", "hmm", "acha", "achha", "nope", "yep",
    "mast", "pakka", "sure", "wait", "ruko", "dekhte", "chal", "chalo", "arrey"
]

TYPO_SHORT_MSGS = [
    "kal milte h", "bhejdia bhai", "tmrw subah call krta hu", "pls check mail",
    "shyd kal hoga", "thnx bro", "omw abhi", "traffic bohot zyada h",
    "gpay kr dia", "ok bro done", "kaha ho sab?", "reachd office",
    "battery low h", "laptop charge pe lgaya", "meeting me hu brb",
    "bhai call pick kr", "bhejo link", "kisi k paas charger h?", "sorted bro"
]

FORWARDED_MSGS = [
    "[Forwarded]: Bengaluru weather forecast: heavy rains expected over weekend.",
    "[Forwarded]: 10 Best cafes to work from in Indiranagar and Koramangala.",
    "[Forwarded]: IRCTC Tatkal booking tips: new guidelines effective this month.",
    "[Forwarded]: GitHub Universe announces new developer copilot features.",
    "[Forwarded]: HDFC Bank alert: scheduled UPI maintenance tonight 1am to 3am.",
    "[Forwarded]: Bangalore Metro Purple line service frequency increased.",
    "[Forwarded]: Swiggy One offers 20% discount on gourmet meals this week."
]

FOOD_COFFEE_MSGS = [
    "lunch ka kya scene hai?", "aaj Meghna biryani order karein?", "chai sutta break anyone?",
    "swiggy pe 150 off mil raha hai, saath me order karte hain",
    "Third Wave coffee pe baithte hain shaam ko", "bhai bhook lag rahi hai",
    "Rameshwaram Cafe ka podi ghee dosa crave ho raha hai",
    "pizza mangwaye kya?", "aaj lunch ghar se laya hu",
    "kisi ko cold coffee peeni hai?", "diet chal rahi hai bro, no junk",
    "Treat kab de raha hai Kabir?", "aaj dinner bahar karte hain"
]

WORK_TECH_BANTER = [
    "prod build fail ho gaya yaar", "client ne requirements change kar di phirse",
    "Docker container memory leak kar raha tha, restart kiya",
    "PR review kar do koi pls", "merge conflict solve karte karte 2 ghante chale gaye",
    "Monday blues hit ho rahe hain bohot gande", "standup me kya bolu samajh nahi aa raha",
    "kisi ko typescript error samajh aata hai?", "bhai git push force mat karna koi bhi",
    "OpenAI ka new model benchmark dekh rahe ho?", "cursor vs copilot debate chal rahi hai twitter pe",
    "WFH approval mil gaya iss Friday ka", "sprint planning boring chal rahi hai"
]

MEME_BANTER = [
    "ye meme dekh kar hasi nahi ruk rahi lol", "literally us in meetings haha",
    "bhai ye reel kisne dekhi?", "dead laughing bro", "meme of the day award",
    "ye stickers kahan se milte hain?", "send sticker pack link",
    "humara life status yahi hai filhal"
]

DAILY_CHATTER = [
    "good morning folks", "kaafi thand ho gayi hai subah subah", "aaj mausam bohot mast hai",
    "gym kaun kaun ja raha hai aaj?", "kisine IPL match dekha kal raat ka?",
    "last over me match palat gaya bhai", "weekend ka kya plan ban raha hai?",
    "bhai bohot neend aa rahi hai", "kal jaldi uthna padega", "weekend kab aayega yaar"
]

# --------------------------------------------------------------------------
# Main Thread Messages (3 Concrete Threads)
# --------------------------------------------------------------------------
# Thread A: Himachal Mountain Trip (Target Dates: June 2 to June 21, 2024)
THREAD_A_EVENTS = [
    # (Day_offset_from_June1, sender, text, tag)
    (2, "Kabir Sharma", "guys summer me ek proper road trip banti hai, kya bolte ho?", "A_intro"),
    (2, "Rohan Mehta", "haan yaar chalte hain, Goa bohot garmi hogi abhi", "A_banter"),
    (2, "Sneha Rao", "pahadon me chalte hain, weather pleasant hoga", "A_banter"),
    (3, "Kabir Sharma", "chalo Manali fix hai, pahadon me chalte hain", "A_dest_final"), # KEY 1 (Zero overlap)
    (3, "Priya Patel", "dates batao pehle, office leaves manage karni padengi", "A_banter"),
    (4, "Vikram Malhotra", "mid June sahi rahega monsoon se pehle", "A_banter"),
    (5, "Kabir Sharma", "14 se 18 June pakka, leave apply kar lo sab", "A_dates_final"), # KEY 2
    (6, "Sneha Rao", "main Airbnb aur cottages dekh rahi hu Old Manali side", "A_banter"),
    (7, "Sneha Rao", "Old Manali me wooden cottage mil gaya, 1200 per night", "A_stay_final"), # KEY 3 (Zero overlap)
    (7, "Ananya Iyer", "view kaisa hai cottage ka? wooden balcony honi chahiye", "A_banter"),
    (7, "Sneha Rao", "apple orchard ke beech me hai, view zabardast hai", "A_banter"),
    (8, "Rohan Mehta", "gaadi ka kya scene hai? bus se nahi jana mujhe", "A_banter"),
    (8, "Vikram Malhotra", "Scorpio book kar li, self drive, Rohan chalayega", "A_transport_final"), # KEY 4 (Zero overlap)
    (9, "Priya Patel", "budget ceiling kitna rakhein per person?", "A_banter"),
    (9, "Kabir Sharma", "per head 8500 se zyada nahi, Priya track karegi", "A_budget_final"), # KEY 5 (Zero overlap)
    (10, "Priya Patel", "okay sab log 4000 advance GPay kar do booking ke liye", "A_banter"),
    (11, "Arjun Nair", "4k transfer kar diya Priya check kar lo", "A_banter"),
    (12, "Rohan Mehta", "gaadi ki servicing aur tyre check karwa liye hain", "A_vehicle_check"), # KEY 6 (Zero overlap)
    (13, "Kabir Sharma", "packing list: warm jacket, power bank, running shoes", "A_banter"),
    (14, "Rohan Mehta", "Delhi bypass cross kar liya, sham tak Manali pahunch jayenge", "A_travel"),
    (15, "Ananya Iyer", "cottage ke garden me bonfire shuru ho gaya hai, sab aa jao", "A_bonfire"), # KEY 7
    (16, "Ananya Iyer", "Kabir ko altitude pe chakkar aa rahe the, rest karna pada", "A_sickness"), # KEY 8 (Zero overlap)
    (17, "Sneha Rao", "Solang valley me paragliding bohot fun thi", "A_banter"),
    (18, "Rohan Mehta", "return journey start ho gayi hai, Delhi by 10pm", "A_banter"),
    (20, "Priya Patel", "trip ke sare expenses splitwise pe dal diye hain, settle up kar lo", "A_splitwise") # KEY 9
]

# Thread B: Flat Hunting in Indiranagar (Target Dates: July 5 to August 16, 2024)
THREAD_B_EVENTS = [
    (5, "Tanvi Joshi", "Indiranagar me 3BHK search karte hain, office ke paas", "B_intro"), # Day from July 1
    (6, "Priya Patel", "max budget kitna rakhein per person rent ka?", "B_banter"),
    (8, "Tanvi Joshi", "brokers se baat chal rahi hai, 2-3 flats shortlisted hain", "B_banter"),
    (10, "Tanvi Joshi", "Ramesh broker ka number hai, 3BHK dikhayega kal", "B_broker"), # KEY 10
    (11, "Kabir Sharma", "kal shaam 6 baje flat dekhne chalte hain saath me", "B_banter"),
    (12, "Kabir Sharma", "flat dekh liya, balcony bohot badi hai aur ventilation mast", "B_visit"),
    (15, "Priya Patel", "owner rent negotiate karne ko ready hai kya?", "B_banter"),
    (18, "Tanvi Joshi", "kiraya chaunvan hazaar hai, teen logon me split hoga", "B_rent_final"), # KEY 11 (Zero overlap: 54k)
    (19, "Arjun Nair", "18k per head, Indiranagar ke location ke hisab se deal achhi hai", "B_banter"),
    (20, "Tanvi Joshi", "broker bol raha hai dhaii lakh advance mangta hai", "B_deposit_final"), # KEY 12 (Zero overlap: 2.5L)
    (22, "Priya Patel", "deposit ke liye thoda time mangte hain owner se", "B_banter"),
    (25, "Priya Patel", "bada kamra Tanvi ko, uska furniture zyada hai", "B_bedroom_allot"), # KEY 13
    (28, "Tanvi Joshi", "pehli August ko shifting final, tempo book karo", "B_shifting_date"), # KEY 14
    (31, "Kabir Sharma", "packing boxes le aaya hu main, packing start karte hain", "B_banter"),
    # August events (Day 32 = Aug 1)
    (33, "Arjun Nair", "purana fridge mere ghar se shift karwa denge", "B_fridge_supply"), # KEY 15 (Zero overlap, Aug 2)
    (35, "Sneha Rao", "curtains aur rugs IKEA se order karein?", "B_banter"),
    (36, "Priya Patel", "main sara hisab kitab excel sheet me track karungi", "B_excel_track"), # KEY 16 (Zero overlap, Aug 5)
    (38, "Vikram Malhotra", "Airtel Xstream fiber lagwa diya hai 300 Mbps", "B_wifi_install"), # KEY 17
    (42, "Ananya Iyer", "housewarming dinner kab rakh rahe hain?", "B_banter"),
    (46, "Ananya Iyer", "Independence Day pe flat pe biryani party fix hai", "B_party_aug15") # KEY 18 (Aug 15)
]

# Thread C: ChatPulse Hackathon Project (Target Dates: Sept 4 to Oct 16, 2024)
THREAD_C_EVENTS = [
    (4, "Kabir Sharma", "AI Hackathon Bangalore announced, 5 Lakhs prize pool", "C_intro"), # Day from Sept 1
    (5, "Kabir Sharma", "group chat search tool banate hain, semantic search wala", "C_idea_final"), # KEY 19
    (6, "Sneha Rao", "concept cool hai, WhatsApp exports search karna bohot painful hota hai", "C_banter"),
    (8, "Vikram Malhotra", "FastAPI backend aur React frontend, Postgres use karte hain", "C_tech_final"), # KEY 20
    (9, "Priya Patel", "database scalable hona chahiye for thousands of messages", "C_banter"),
    (10, "Vikram Malhotra", "backend routes aur database models main sambhalta hoon", "C_backend_owner"), # KEY 21 (Zero overlap)
    (12, "Sneha Rao", "Figma designs complete ho gaye, dark mode minimal rakha hai", "C_ui_figma"), # KEY 22
    (14, "Ananya Iyer", "Hinglish queries support honi chahiye, code-mixed search is key", "C_banter"),
    (15, "Sneha Rao", "pachees tareekh raat barah baje se pehle deck submit karni hai", "C_deadline_final"), # KEY 23 (Zero overlap: Sept 25)
    (17, "Vikram Malhotra", "SentenceTransformers multilingual model implement kar diya backend me", "C_banter"),
    (18, "Kabir Sharma", "repo bana diya hai, sab log fork kar lo", "C_repo_created"), # KEY 24
    (20, "Arjun Nair", "sample chat export parse ho gaya successfully", "C_banter"),
    (23, "Sneha Rao", "slide deck ke bullet points finalize kar liye hain", "C_banter"),
    (24, "Kabir Sharma", "pitch deck submit ho gayi on portal, now preparing for demo round", "C_banter"),
    # Oct events (Day 31 = Oct 1)
    (31, "Sneha Rao", "screen recording kar ke upload karo, 3 min max", "C_video_req"), # KEY 25 (Oct 1)
    (34, "Vikram Malhotra", "final demo video YouTube unlisted link pe upload kar di", "C_video_uploaded"), # KEY 26 (Oct 4)
    (38, "Ananya Iyer", "judges Q&A slot mila hai Saturday morning", "C_banter"),
    (42, "Kabir Sharma", "guys we secured 2nd place in the AI category!", "C_results_win") # KEY 27 (Oct 12)
]

# Additional specific micro-decision messages across participants
MICRO_EVENTS = [
    # (Date, sender, text, tag)
    (datetime(2024, 5, 8, 14, 20), "Rohan Mehta", "kisine meri car key dekhi hai kya desk pe?", "M_car_key"),
    (datetime(2024, 5, 15, 20, 10), "Ananya Iyer", "Friday dinner at Toit brewery reserve kar diya maine 8 baje", "M_toit_reserve"),
    (datetime(2024, 5, 22, 11, 45), "Vikram Malhotra", "new MacBook Pro M3 arrive ho gaya office me", "M_macbook"),
    (datetime(2024, 6, 25, 16, 30), "Priya Patel", "Amazon Prime Day sale me air fryer discount pe mil raha hai", "M_airfryer"),
    (datetime(2024, 7, 2, 19, 15), "Sneha Rao", "desk plant khareeda hai maine nursery se, Monstera", "M_plant"),
    (datetime(2024, 7, 22, 21, 5), "Arjun Nair", "gym membership renew kar li Cult play Indiranagar", "M_cult"),
    (datetime(2024, 8, 10, 18, 40), "Tanvi Joshi", "sofa dry cleaning service book ki hai Urban Company se", "M_sofa_clean"),
    (datetime(2024, 8, 22, 15, 10), "Kabir Sharma", "Badminton court book kiya hai Playo pe Saturday 7am", "M_badminton"),
    (datetime(2024, 9, 2, 12, 35), "Ananya Iyer", "Filter coffee machine order kar di office kitchen ke liye", "M_coffee_machine"),
    (datetime(2024, 9, 28, 22, 15), "Rohan Mehta", "F1 Singapore GP live streaming watch party mere room me", "M_f1_party"),
    (datetime(2024, 10, 20, 17, 50), "Sneha Rao", "Diwali sweets box gift distribute ho rahe hain reception pe", "M_diwali_sweets"),
    (datetime(2024, 10, 28, 20, 30), "Priya Patel", "flat electricity bill 4200 rupees aaya hai split kar lo", "M_elec_bill"),
    (datetime(2024, 10, 30, 19, 15), "Kabir Sharma", "Halloween costume party at rooftop cafe tomorrow", "M_halloween")
]


def generate_full_corpus():
    """Generates all 4,200+ messages interleaved chronologically."""
    messages = []
    
    # 1. Place thread A messages (June 2024)
    june_start = datetime(2024, 6, 1, 10, 0, 0)
    for day_off, sender, text, tag in THREAD_A_EVENTS:
        ts = june_start + timedelta(days=day_off, hours=random.randint(10, 21), minutes=random.randint(0, 59))
        messages.append({"sender": sender, "timestamp": ts, "text": text, "tag": tag})

    # 2. Place thread B messages (July - August 2024)
    july_start = datetime(2024, 7, 1, 10, 0, 0)
    for day_off, sender, text, tag in THREAD_B_EVENTS:
        ts = july_start + timedelta(days=day_off, hours=random.randint(10, 21), minutes=random.randint(0, 59))
        messages.append({"sender": sender, "timestamp": ts, "text": text, "tag": tag})

    # 3. Place thread C messages (Sept - October 2024)
    sept_start = datetime(2024, 9, 1, 10, 0, 0)
    for day_off, sender, text, tag in THREAD_C_EVENTS:
        ts = sept_start + timedelta(days=day_off, hours=random.randint(10, 21), minutes=random.randint(0, 59))
        messages.append({"sender": sender, "timestamp": ts, "text": text, "tag": tag})

    # 4. Place micro events
    for ts, sender, text, tag in MICRO_EVENTS:
        messages.append({"sender": sender, "timestamp": ts, "text": text, "tag": tag})

    # Current count of tagged messages ~ 65
    tagged_count = len(messages)
    target_filler_count = 4250 - tagged_count

    # 5. Generate fillers uniformly across May 1 to Oct 31
    start_epoch = START_DATE.timestamp()
    end_epoch = END_DATE.timestamp()
    total_sec = end_epoch - start_epoch

    filler_pools = [
        (ONE_WORD_REPLIES, 0.35),
        (TYPO_SHORT_MSGS, 0.20),
        (FOOD_COFFEE_MSGS, 0.15),
        (WORK_TECH_BANTER, 0.15),
        (DAILY_CHATTER, 0.08),
        (MEME_BANTER, 0.05),
        (FORWARDED_MSGS, 0.02)
    ]
    pool_choices, pool_weights = zip(*filler_pools)

    for _ in range(target_filler_count):
        # Pick random timestamp
        rand_sec = random.uniform(0, total_sec)
        rand_dt = datetime.fromtimestamp(start_epoch + rand_sec)
        
        # Avoid middle of night (2am to 8am)
        hour = rand_dt.hour
        if 2 <= hour < 8:
            rand_dt = rand_dt.replace(hour=random.choice([9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21, 22]))

        sender = random.choices(PARTICIPANTS, weights=P_WEIGHTS)[0]
        chosen_pool = random.choices(pool_choices, weights=pool_weights)[0]
        text = random.choice(chosen_pool)

        messages.append({
            "sender": sender,
            "timestamp": rand_dt,
            "text": text,
            "tag": "filler"
        })

    # Sort strictly by timestamp
    messages.sort(key=lambda m: m["timestamp"])

    # Assign sequential 1-indexed IDs and format ISO timestamps
    final_corpus = []
    tag_to_id = {}

    for idx, m in enumerate(messages, 1):
        iso_ts = m["timestamp"].strftime("%Y-%m-%dT%H:%M:%S")
        entry = {
            "id": idx,
            "sender": m["sender"],
            "timestamp": iso_ts,
            "text": m["text"]
        }
        final_corpus.append(entry)
        if m["tag"] != "filler":
            tag_to_id[m["tag"]] = idx

    return final_corpus, tag_to_id


def build_benchmark_queries(tag_to_id, corpus_map):
    """
    Constructs 40 gold-standard evaluation queries:
    - 16 Semantic queries
    - 12 Attributed queries
    - 12 Temporal queries
    Guarantees AT LEAST 10 zero-lexical overlap test cases.
    """
    # Helper to fetch message snippet for reference
    def get_msg(tag):
        mid = tag_to_id[tag]
        return mid, corpus_map[mid]["text"], corpus_map[mid]["sender"], corpus_map[mid]["timestamp"]

    queries = [
        # =========================================================================
        # 16 SEMANTIC QUERIES (with 10+ ZERO-LEXICAL OVERLAP CASES)
        # =========================================================================
        {
            "id": 1,
            "query": "When was the vacation destination finalized?",
            "answer_message_id": tag_to_id["A_dest_final"],
            "query_type": "semantic",
            "zero_lexical_overlap": True,
            "rationale": "Query has no common words with target: 'chalo Manali fix hai, pahadon me chalte hain'"
        },
        {
            "id": 2,
            "query": "Who volunteered to manage the shared finances?",
            "answer_message_id": tag_to_id["B_excel_track"],
            "query_type": "semantic",
            "zero_lexical_overlap": True,
            "rationale": "Query has no common words with target: 'main sara hisab kitab excel sheet me track karungi'"
        },
        {
            "id": 3,
            "query": "What was the agreed monthly apartment payment?",
            "answer_message_id": tag_to_id["B_rent_final"],
            "query_type": "semantic",
            "zero_lexical_overlap": True,
            "rationale": "Query has no common words with target: 'kiraya chaunvan hazaar hai, teen logon me split hoga'"
        },
        {
            "id": 4,
            "query": "Did anyone get sick during the mountain getaway?",
            "answer_message_id": tag_to_id["A_sickness"],
            "query_type": "semantic",
            "zero_lexical_overlap": True,
            "rationale": "Query has no common words with target: 'Kabir ko altitude pe chakkar aa rahe the, rest karna pada'"
        },
        {
            "id": 5,
            "query": "Who agreed to supply the kitchen cooling appliance?",
            "answer_message_id": tag_to_id["B_fridge_supply"],
            "query_type": "semantic",
            "zero_lexical_overlap": True,
            "rationale": "Query has no common words with target: 'purana fridge mere ghar se shift karwa denge'"
        },
        {
            "id": 6,
            "query": "What is the team's software presentation deadline?",
            "answer_message_id": tag_to_id["C_deadline_final"],
            "query_type": "semantic",
            "zero_lexical_overlap": True,
            "rationale": "Query has no common words with target: 'pachees tareekh raat barah baje se pehle deck submit karni hai'"
        },
        {
            "id": 7,
            "query": "Where are travelers staying during the hill station holiday?",
            "answer_message_id": tag_to_id["A_stay_final"],
            "query_type": "semantic",
            "zero_lexical_overlap": True,
            "rationale": "Query has no common words with target: 'Old Manali me wooden cottage mil gaya, 1200 per night'"
        },
        {
            "id": 8,
            "query": "Who is responsible for constructing the server endpoints?",
            "answer_message_id": tag_to_id["C_backend_owner"],
            "query_type": "semantic",
            "zero_lexical_overlap": True,
            "rationale": "Query has no common words with target: 'backend routes aur database models main sambhalta hoon'"
        },
        {
            "id": 9,
            "query": "What was the landlord's upfront financial security requirement?",
            "answer_message_id": tag_to_id["B_deposit_final"],
            "query_type": "semantic",
            "zero_lexical_overlap": True,
            "rationale": "Query has no common words with target: 'broker bol raha hai dhaii lakh advance mangta hai'"
        },
        {
            "id": 10,
            "query": "Did someone inspect the vehicle condition before departure?",
            "answer_message_id": tag_to_id["A_vehicle_check"],
            "query_type": "semantic",
            "zero_lexical_overlap": True,
            "rationale": "Query has no common words with target: 'gaadi ki servicing aur tyre check karwa liye hain'"
        },
        {
            "id": 11,
            "query": "Which car was booked for the road trip?",
            "answer_message_id": tag_to_id["A_transport_final"],
            "query_type": "semantic",
            "zero_lexical_overlap": False,
            "rationale": "Target: 'Scorpio book kar li, self drive, Rohan chalayega'"
        },
        {
            "id": 12,
            "query": "What is the per person budget cap for Manali?",
            "answer_message_id": tag_to_id["A_budget_final"],
            "query_type": "semantic",
            "zero_lexical_overlap": False,
            "rationale": "Target: 'per head 8500 se zyada nahi, Priya track karegi'"
        },
        {
            "id": 13,
            "query": "When did we lock the trip travel dates?",
            "answer_message_id": tag_to_id["A_dates_final"],
            "query_type": "semantic",
            "zero_lexical_overlap": False,
            "rationale": "Target: '14 se 18 June pakka, leave apply kar lo sab'"
        },
        {
            "id": 14,
            "query": "When is the official moving date for the flat?",
            "answer_message_id": tag_to_id["B_shifting_date"],
            "query_type": "semantic",
            "zero_lexical_overlap": False,
            "rationale": "Target: 'pehli August ko shifting final, tempo book karo'"
        },
        {
            "id": 15,
            "query": "What startup product are we building for the hackathon?",
            "answer_message_id": tag_to_id["C_idea_final"],
            "query_type": "semantic",
            "zero_lexical_overlap": False,
            "rationale": "Target: 'group chat search tool banate hain, semantic search wala'"
        },
        {
            "id": 16,
            "query": "Where can the team find the new project GitHub repository?",
            "answer_message_id": tag_to_id["C_repo_created"],
            "query_type": "semantic",
            "zero_lexical_overlap": False,
            "rationale": "Target: 'repo bana diya hai, sab log fork kar lo'"
        },

        # =========================================================================
        # 12 ATTRIBUTED QUERIES (Sender specified in natural language)
        # =========================================================================
        {
            "id": 17,
            "query": "what did Priya say about the trip budget ceiling",
            "answer_message_id": tag_to_id["A_budget_final"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Priya Patel"
        },
        {
            "id": 18,
            "query": "what did Tanvi say about the broker for the 3BHK flat",
            "answer_message_id": tag_to_id["B_broker"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Tanvi Joshi"
        },
        {
            "id": 19,
            "query": "what did Vikram suggest for the backend tech stack",
            "answer_message_id": tag_to_id["C_tech_final"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Vikram Malhotra"
        },
        {
            "id": 20,
            "query": "what did Rohan report about the vehicle servicing",
            "answer_message_id": tag_to_id["A_vehicle_check"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Rohan Mehta"
        },
        {
            "id": 21,
            "query": "what was Sneha's proposal for the wooden cottage in Old Manali",
            "answer_message_id": tag_to_id["A_stay_final"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Sneha Rao"
        },
        {
            "id": 22,
            "query": "what did Priya say about tracking expenses in excel",
            "answer_message_id": tag_to_id["B_excel_track"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Priya Patel"
        },
        {
            "id": 23,
            "query": "what did Arjun offer regarding the refrigerator",
            "answer_message_id": tag_to_id["B_fridge_supply"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Arjun Nair"
        },
        {
            "id": 24,
            "query": "what was Kabir's announcement about the hackathon results",
            "answer_message_id": tag_to_id["C_results_win"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Kabir Sharma"
        },
        {
            "id": 25,
            "query": "what did Ananya say about Kabir's altitude sickness",
            "answer_message_id": tag_to_id["A_sickness"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Ananya Iyer"
        },
        {
            "id": 26,
            "query": "what did Sneha specify about the demo video duration limit",
            "answer_message_id": tag_to_id["C_video_req"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Sneha Rao"
        },
        {
            "id": 27,
            "query": "what did Priya mention about bedroom allotment in the flat",
            "answer_message_id": tag_to_id["B_bedroom_allot"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Priya Patel"
        },
        {
            "id": 28,
            "query": "what did Vikram say about uploading the demo video to YouTube",
            "answer_message_id": tag_to_id["C_video_uploaded"],
            "query_type": "attributed",
            "zero_lexical_overlap": False,
            "sender_filter": "Vikram Malhotra"
        },

        # =========================================================================
        # 12 TEMPORAL QUERIES (Time bounded natural language queries)
        # =========================================================================
        {
            "id": 29,
            "query": "what trip plans were decided in the first week of June",
            "answer_message_id": tag_to_id["A_dest_final"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-06-01 to 2024-06-07"
        },
        {
            "id": 30,
            "query": "what was agreed about the cottage stay during early June",
            "answer_message_id": tag_to_id["A_stay_final"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-06-05 to 2024-06-10"
        },
        {
            "id": 31,
            "query": "what happened during the road trip on June 15 or 16",
            "answer_message_id": tag_to_id["A_bonfire"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-06-15 to 2024-06-17"
        },
        {
            "id": 32,
            "query": "what did we discuss regarding flat hunting in early July",
            "answer_message_id": tag_to_id["B_intro"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-07-01 to 2024-07-10"
        },
        {
            "id": 33,
            "query": "what rent decisions were finalized in the middle of July",
            "answer_message_id": tag_to_id["B_rent_final"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-07-15 to 2024-07-22"
        },
        {
            "id": 34,
            "query": "what was confirmed regarding the deposit in late July",
            "answer_message_id": tag_to_id["B_deposit_final"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-07-20 to 2024-07-31"
        },
        {
            "id": 35,
            "query": "what shifting plans were made in early August",
            "answer_message_id": tag_to_id["B_fridge_supply"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-08-01 to 2024-08-08"
        },
        {
            "id": 36,
            "query": "what party was planned around Independence Day in August",
            "answer_message_id": tag_to_id["B_party_aug15"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-08-10 to 2024-08-17"
        },
        {
            "id": 37,
            "query": "what hackathon ideas were proposed in early September",
            "answer_message_id": tag_to_id["C_idea_final"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-09-01 to 2024-09-08"
        },
        {
            "id": 38,
            "query": "what deadline was set in mid September for the hackathon",
            "answer_message_id": tag_to_id["C_deadline_final"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-09-12 to 2024-09-20"
        },
        {
            "id": 39,
            "query": "what video submission requirements were discussed in early October",
            "answer_message_id": tag_to_id["C_video_req"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-10-01 to 2024-10-06"
        },
        {
            "id": 40,
            "query": "what contest results were shared in mid October",
            "answer_message_id": tag_to_id["C_results_win"],
            "query_type": "temporal",
            "zero_lexical_overlap": False,
            "date_range": "2024-10-10 to 2024-10-16"
        }
    ]

    return queries


def export_as_whatsapp_txt(corpus, filepath):
    """Writes realistic WhatsApp exported format (.txt)."""
    with open(filepath, "w", encoding="utf-8") as f:
        for m in corpus:
            dt = datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S")
            date_str = dt.strftime("%d/%m/%y, %I:%M %p")
            f.write(f"[{date_str}] {m['sender']}: {m['text']}\n")


if __name__ == "__main__":
    print("Generating full synthetic group chat corpus...")
    corpus, tag_to_id = generate_full_corpus()
    corpus_map = {m["id"]: m for m in corpus}

    print(f"Total messages generated: {len(corpus)}")
    unique_senders = set(m["sender"] for m in corpus)
    print(f"Unique participants ({len(unique_senders)}): {sorted(list(unique_senders))}")
    print(f"Time range: {corpus[0]['timestamp']} to {corpus[-1]['timestamp']}")

    # Save chat_corpus.json
    json_path = os.path.join(TARGET_DIR, "chat_corpus.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)
    print(f"Saved: {json_path}")

    # Save chat_export.txt
    txt_path = os.path.join(TARGET_DIR, "chat_export.txt")
    export_as_whatsapp_txt(corpus, txt_path)
    print(f"Saved: {txt_path}")

    # Generate benchmark queries
    queries = build_benchmark_queries(tag_to_id, corpus_map)
    zero_count = sum(1 for q in queries if q.get("zero_lexical_overlap"))
    print(f"Generated {len(queries)} benchmark queries with {zero_count} zero-lexical overlap test cases.")

    bench_path = os.path.join(TARGET_DIR, "benchmark_queries.json")
    with open(bench_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2, ensure_ascii=False)
    print(f"Saved: {bench_path}")

    # Sanity checks
    assert len(corpus) >= 4000, f"Expected >= 4000 messages, got {len(corpus)}"
    assert len(unique_senders) == 8, f"Expected 8 senders, got {len(unique_senders)}"
    assert len(queries) == 40, f"Expected 40 queries, got {len(queries)}"
    assert zero_count >= 10, f"Expected >= 10 zero overlap queries, got {zero_count}"
    print("All Phase 1 sanity assertions passed perfectly!")
