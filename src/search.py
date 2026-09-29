import math
import re
from collections import Counter


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "do",
    "for", "from", "how", "i", "if", "in", "is", "it", "me", "my", "of",
    "on", "or", "the", "this", "to", "was", "what", "when", "where", "will",
    "with", "you", "your",
}

NORMALIZE = {
    "log-in": "signin",
    "login": "signin",
    "sign-in": "signin",
    "renewing": "renewal",
    "cancelled": "cancel",
    "cancelling": "cancel",
    "refunded": "refund",
    "processing": "pending",
}


def tokenize(text):
    raw = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", text.lower())
    tokens = []
    for token in raw:
        token = NORMALIZE.get(token, token)
        if token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("ing") and len(token) > 5:
            token = token[:-3]
        elif token.endswith("ed") and len(token) > 4:
            token = token[:-2]
        elif token.endswith("s") and len(token) > 4:
            token = token[:-1]
        if token not in STOPWORDS and len(token) > 1:
            tokens.append(token)
    return tokens


def _idf(documents):
    count = len(documents)
    frequency = Counter()
    for document in documents:
        frequency.update(set(tokenize(document)))
    return {token: math.log((count + 1) / (seen + 1)) + 1 for token, seen in frequency.items()}


def _score(query, text, idf, heading="", title=""):
    query_tokens = tokenize(query)
    body = Counter(tokenize(text))
    heading_tokens = set(tokenize(heading))
    title_tokens = set(tokenize(title))
    score = 0.0
    for token in set(query_tokens):
        weight = idf.get(token, 1.0)
        score += min(body[token], 3) * weight
        score += 1.25 * weight if token in heading_tokens else 0
        score += 0.5 * weight if token in title_tokens else 0
    pairs = set(zip(query_tokens, query_tokens[1:]))
    text_tokens = tokenize(f"{heading} {text}")
    score += 1.5 * len(pairs & set(zip(text_tokens, text_tokens[1:])))
    return round(score, 6)


def section_rows(corpus):
    return [
        {
            "article_id": article["article_id"],
            "article_title": article["title"],
            "locale": article["locale"],
            "source_url": article.get("source_url"),
            **section,
        }
        for article in corpus
        for section in article["sections"]
    ]


def section_search(query, corpus, limit=3):
    rows = section_rows(corpus)
    documents = [f'{row["article_title"]} {row["heading"]} {row["text"]}' for row in rows]
    idf = _idf(documents)
    ranked = [
        {
            **row,
            "score": _score(query, row["text"], idf, heading=row["heading"], title=row["article_title"]),
        }
        for row in rows
    ]
    ranked.sort(key=lambda row: (-row["score"], row["section_id"]))
    return ranked[:limit]


def whole_article_search(query, corpus, limit=3):
    documents = [
        (article, " ".join([article["title"]] + [f'{s["heading"]} {s["text"]}' for s in article["sections"]]))
        for article in corpus
    ]
    idf = _idf([text for _, text in documents])
    ranked_articles = [(_score(query, text, idf, title=article["title"]), article) for article, text in documents]
    ranked_articles.sort(key=lambda item: (-item[0], item[1]["article_id"]))
    results = []
    for article_score, article in ranked_articles[:limit]:
        section_documents = [f'{section["heading"]} {section["text"]}' for section in article["sections"]]
        section_idf = _idf(section_documents)
        sections = [
            (_score(query, section["text"], section_idf, heading=section["heading"], title=article["title"]), section)
            for section in article["sections"]
        ]
        sections.sort(key=lambda item: (-item[0], item[1]["section_id"]))
        section_score, section = sections[0]
        results.append({
            "article_id": article["article_id"],
            "article_title": article["title"],
            "locale": article["locale"],
            "source_url": article.get("source_url"),
            **section,
            "score": article_score,
            "section_score": section_score,
        })
    return results


def matching_gate(query, gates):
    text = re.sub(r"\s+", " ", query.lower().replace("’", "'")).strip()
    return next(
        (gate for gate in gates if all(any(phrase in text for phrase in group) for group in gate["match_groups"])),
        None,
    )


def gated_section_search(query, corpus, gates, limit=3):
    rows = section_search(query, corpus, limit=sum(len(article["sections"]) for article in corpus))
    gate = matching_gate(query, gates)
    if not gate:
        return rows[:limit]
    required = next((row for row in rows if row["section_id"] == gate["required_section_id"]), None)
    if required is None:
        raise LookupError(f'Required safety section is missing: {gate["required_section_id"]}')
    excluded = set(gate.get("excluded_section_ids", []))
    remaining = [row for row in rows if row["section_id"] != required["section_id"] and row["section_id"] not in excluded]
    return [{**required, "gate": gate["name"]}, *remaining][:limit]
