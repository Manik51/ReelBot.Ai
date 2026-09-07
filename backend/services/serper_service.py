import json
import random
import re
import requests
from typing import List, Dict, Any

class SerperService:
    SERPER_SEARCH_URL = "https://google.serper.dev/news"
    SERPER_GENERAL_URL = "https://google.serper.dev/search"

    TREND_QUERIES_POOL = [
        # True Crime & Cold Cases
        {"q": "true crime cold case DNA breakthrough solved news", "emoji": "🧬", "category": "DNA Breakthrough"},
        {"q": "unsolved murder mystery cold case investigation latest", "emoji": "🕵️‍♂️", "category": "Cold Case"},
        {"q": "serial killer cold case evidence found police", "emoji": "💀", "category": "True Crime"},
        {"q": "mysterious disappearance person vanished without trace", "emoji": "🔍", "category": "Disappearance"},
        {"q": "famous heist bank robbery million dollars missing", "emoji": "💰", "category": "Unsolved Heist"},
        
        # Ocean & Deep Sea Mysteries
        {"q": "deep ocean discovery bizarre creature anomaly sonar", "emoji": "🌊", "category": "Ocean Mystery"},
        {"q": "shipwreck discovered underwater treasure gold diving", "emoji": "🚢", "category": "Lost Shipwreck"},
        {"q": "underwater ancient ruins city discovered ocean floor", "emoji": "🏛️", "category": "Sunken City"},
        
        # Ancient & Historical Mysteries
        {"q": "ancient tomb discovered cursed relic excavation archaeologists", "emoji": "🏺", "category": "Ancient Curse"},
        {"q": "mysterious ancient artifact unexplained technology discovery", "emoji": "📜", "category": "Ancient Mystery"},
        {"q": "pyramid hidden chamber secret discovered radar scan", "emoji": "🔺", "category": "Hidden Chambers"},
        
        # Bizarre & Unexplained Incidents
        {"q": "bizarre unexplained phenomenon scientists baffled news", "emoji": "👁️", "category": "Unexplained Anomaly"},
        {"q": "mysterious radio signal detected deep space telescope", "emoji": "📻", "category": "Cosmic Signal"},
        {"q": "airplane vanished radar flight mystery disappearance", "emoji": "✈️", "category": "Aviation Mystery"},
        {"q": "classified declassified military secret files revelation", "emoji": "🔒", "category": "Declassified Files"},
        {"q": "strange forest disappearance hikers national park mystery", "emoji": "🌲", "category": "Forest Mystery"},
        
        # High-Stakes Crimes & Heists
        {"q": "museum art diamond heist thief escaped police", "emoji": "💎", "category": "Master Heist"},
        {"q": "cryptocurrency hacker stolen millions vanished offshore", "emoji": "💻", "category": "Cyber Mystery"},
        {"q": "underground bunker secret tunnels discovered beneath city", "emoji": "🚪", "category": "Secret Tunnels"}
    ]

    @classmethod
    def clean_headline(cls, raw_title: str) -> str:
        """Strips annoying news outlet branding (e.g. - BBC News, | CNN, - The New York Times)."""
        cleaned = re.sub(r"\s*[-|–—:]\s*(BBC|CNN|The New York Times|Fox News|NDTV|India Today|Daily Mail|The Guardian|CBS News|NBC News|ABC News|Reuters|AP News|New York Post|Forbes|USA Today|Independent|Times of India|Hindustan Times).*$", "", raw_title, flags=re.IGNORECASE)
        cleaned = re.sub(r"^BREAKING:\s*", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip() or raw_title.strip()

    @classmethod
    def search_live_true_crime(cls, api_key: str) -> List[Dict[str, Any]]:
        """Queries Serper API with randomized dynamic query sampling for 100% fresh topics on every search."""
        if not api_key:
            return []

        headers = {
            "X-API-KEY": api_key.strip(),
            "Content-Type": "application/json"
        }

        # Pick 3 random distinct queries from the pool on every single click
        sampled_queries = random.sample(cls.TREND_QUERIES_POOL, k=min(4, len(cls.TREND_QUERIES_POOL)))
        time_filters = ["qdr:w", "qdr:m", "qdr:d", ""]
        chosen_tbs = random.choice(time_filters)

        results: List[Dict[str, Any]] = []

        for q_item in sampled_queries:
            query_str = q_item["q"]
            emoji = q_item["emoji"]
            category = q_item["category"]

            try:
                payload = {
                    "q": query_str,
                    "num": 8,
                    "gl": "us",
                    "hl": "en"
                }
                if chosen_tbs:
                    payload["tbs"] = chosen_tbs

                response = requests.post(
                    cls.SERPER_SEARCH_URL,
                    headers=headers,
                    json=payload,
                    timeout=8
                )

                if response.status_code == 200:
                    data = response.json()
                    news_items = data.get("news", [])
                    random.shuffle(news_items)

                    for item in news_items:
                        raw_title = item.get("title", "").strip()
                        if not raw_title:
                            continue

                        title = cls.clean_headline(raw_title)
                        source = item.get("source", "Live Global Wire")
                        link = item.get("link", "#")
                        date = item.get("date", "Recent")
                        snippet = item.get("snippet", "")

                        # Avoid duplicates
                        if not any(r["title"].lower() == title.lower() for r in results):
                            views_random = f"{random.randint(12, 38)}.{random.randint(1, 9)}M Views"
                            results.append({
                                "title": title,
                                "source": source,
                                "link": link,
                                "date": date,
                                "snippet": snippet,
                                "category": category,
                                "views_potential": views_random,
                                "emoji": emoji
                            })

                if len(results) >= 8:
                    break
            except Exception as e:
                print(f"Serper search error for '{query_str}': {e}")
                continue

        # Fallback to general search if news returned too few
        if len(results) < 4:
            fallback_terms = [
                "mysterious real life unsolved true crime stories headlines",
                "chilling unsolved cold cases and ocean anomalies news",
                "bizarre unexplained ancient discoveries news"
            ]
            chosen_term = random.choice(fallback_terms)
            try:
                payload = {
                    "q": chosen_term,
                    "num": 10,
                    "gl": "us"
                }
                response = requests.post(
                    cls.SERPER_GENERAL_URL,
                    headers=headers,
                    json=payload,
                    timeout=8
                )
                if response.status_code == 200:
                    data = response.json()
                    organic = data.get("organic", [])
                    random.shuffle(organic)
                    for item in organic:
                        raw_title = item.get("title", "").strip()
                        if not raw_title:
                            continue
                        title = cls.clean_headline(raw_title)
                        link = item.get("link", "#")
                        snippet = item.get("snippet", "")
                        source = link.split("//")[-1].split("/")[0].replace("www.", "")

                        if not any(r["title"].lower() == title.lower() for r in results):
                            results.append({
                                "title": title,
                                "source": source,
                                "link": link,
                                "date": "Live Web",
                                "snippet": snippet,
                                "category": "Trending Mystery",
                                "views_potential": f"{random.randint(14, 29)}.{random.randint(1, 9)}M Views",
                                "emoji": "🔥"
                            })
            except Exception as e:
                print(f"Serper general search error: {e}")

        random.shuffle(results)
        return results[:8]
