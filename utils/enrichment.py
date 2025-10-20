import re
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, Any, Iterable, Tuple, List, Optional
import requests

from utils.file_parser import *


def sanitize_bib_file(bib_file: BibFile):
    for entry in bib_file.content:
        lookup = None
        if type(entry) is Reference:
            fields = entry.get_fields()
            if fields['entry_type'] != 'set':
                # if 'doi' in fields:
                #     lookup = lookup_bibtex_fields_by_title(fields['doi'], '')
                #     print('doi:')
                #     print(lookup)
                if 'author' in fields:
                    authors = _split_authors(fields['author'])
                    iterable = iter(authors)
                    first_author = next(iterable)
                    lookup = lookup_bibtex_fields_by_title(fields['title'], first_author)
                elif 'editor' in fields:
                    authors = _split_authors(fields['editor'])
                    iterable = iter(authors)
                    first_author = next(iterable)
                    lookup = lookup_bibtex_fields_by_title(fields['title'], first_author)
            if lookup:
                for k, v in lookup.items():
                    if not k in fields:
                        fields[k] = v
    return bib_file


def lookup_bibtex_fields_by_title(title: str, author: str, timeout: float = 10.0) -> Dict[str, Any] | None:
    # Make session for api friendliness
    session = requests.session()
    session.headers.update({'User-Agent': 'BibSTEAK/0.1'})

    responses: List[Dict[str, Any]] = []
    query = title + " " + author
    # Execute API queries
    try:
        cr = _search_crossref(session, query, timeout)
        if cr and is_same_paper(title, author, cr):
            responses.append(cr)
    except Exception as e:
        print(e)

    try:
        db = _search_dblp(session, query, timeout)
        if db and is_same_paper(title, author, db):
            responses.append(db)
    except Exception as e:
        print(e)

    try:
        dc = _search_datacite()
        if dc and is_same_paper(title, author, dc):
            responses.append(dc)
    except Exception:
        pass

    # try:
    #     oa = _search_openalex()
    #     if oa:
    #         responses.append(oa)
    # except Exception:
    #     pass
    final_dict: Dict[str, Any] = {}
    for response in responses:
        final_dict = _merge_responses(final_dict, response)

    return final_dict


def _search_crossref(session: requests.Session, query: str, timeout: float) -> Dict[str, Any] | None:
    url = "https://api.crossref.org/works"
    params = {
        'query.bibliographic': query,
        'rows': 1,
        'select': ",".join([
            "title", "author", "issued", "type", "publisher", "volume",
            "issue", "page", "DOI", "URL", "ISBN", "ISSN", "published-print", "published-online",
            "abstract", "reference", "subject"
        ]),
        'sort': 'score',
        'order': 'desc'
    }

    response = session.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    json = response.json()
    items = json.get("message", {}).get("items", [])
    if not items:
        return None
    return _map_crossref_to_bib_dict(items[0])


def _map_crossref_to_bib_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    # Get title
    title = (data.get("title") or None)[0]
    if title:
        result["title"] = title

    # Get authors
    authors = data.get("author") or []
    names = []
    for a in authors:
        if "literal" in a:
            names.append(a["literal"])
        else:
            given = a.get("given", "").strip()
            family = a.get("family", "").strip()
            full = " ".join(x for x in [given, family] if x).strip()
            if full:
                names.append(full)
    if names:
        result["author"] = " and ".join(names)

    # Volume
    if data.get("volume"): result["volume"] = data["volume"]
    # Issue
    if data.get("issue"): result["issue"] = data["issue"]
    # Pages
    if data.get("page"): result["pages"] = data["page"]
    # Publisher
    if data.get("publisher"): result["publisher"] = data["publisher"]
    # Identifiers
    if data.get("DOI"): result["doi"] = data["DOI"]
    if data.get("URL"): result["url"] = data["URL"]

    return result


def _search_dblp(session: requests.Session, query: str, timeout: float) -> Dict[str, Any] | None:
    url = "https://dblp.org/search/publ/api"
    params = {'q': query, 'h': 1, 'format': 'json'}
    response = session.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json().get("result", {}).get("hits", {}).get("hit", []) or []
    if isinstance(data, dict):
        data = [data]
    if not data:
        return None
    data_info = data[0].get("info", {})
    return _map_dblp_to_bib_dict(data_info)


def _map_dblp_to_bib_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    # Title
    if data.get("title"): result["title"] = data["title"]

    # Authors
    # TODO: Implement
    result["authors"] = "placeholder"

    # Venue (aka journal/book-title)
    if data.get("venue"): result["venue"] = data["venue"]
    # Year
    if data.get("year"): result["year"] = data["year"]
    # Volume
    if data.get("volume"): result["volume"] = data["volume"]
    # Number
    if data.get("number"): result["number"] = data["number"]
    # Pages
    if data.get("pages"): result["pages"] = data["pages"]
    # Identifiers
    if data.get("doi"): result["doi"] = data["doi"]
    if data.get("ee"): result["ee"] = data["ee"]
    if result["doi"]:
        result["url"] = f"https://doi.org/{result["doi"]}"
    else:
        if data.get("ee"): result["ee"] = data["ee"]

    return result


def _search_datacite(session: requests.Session, query: str, *, timeout: float) -> Optional[Dict[str, Any]]:
    url = "https://api.datacite.org/dois"
    params = {
        "query": f'title:"{query}"',
        "page[size]": 1,
        "sort": "relevance"
    }
    r = session.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    items = data.get("data", [])
    if not items:
        return None
    it = items[0].get("attributes", {})
    return _map_datacite_to_bibtex(it)

def _map_datacite_to_bibtex(data: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    # Title
    titles = data.get("titles") or []
    if titles:
        result["title"] = (titles[0].get("title") or "").strip()

    # Authors
    creators = data.get("creators") or []
    names = []
    for c in creators:
        name = c.get("name") or " ".join(filter(None, [c.get("givenName"), c.get("familyName")]))
        if name:
            names.append(name)
    if names:
        result["author"] = " and ".join(names)

    # Year/Month
    if data.get("publicationYear"):
        result["year"] = data.get("publicationYear")

    # Container / publisher
    if data.get("container"):
        # Some DataCite records include a container title
        title = data["container"].get("title")
        if title:
            result["_container"] = title
    if data.get("publisher"):
        result["publisher"] = data["publisher"]

    # Type hint
    rtg = (data.get("types") or {}).get("resourceTypeGeneral")
    if rtg:
        result["_type_hint"] = str(rtg).lower()

    # Volume/Issue/Pages (occasionally in 'container' or 'relatedIdentifiers'—often missing)
    biblio = data.get("biblio", {})  # not standard; keep as placeholder if present
    if biblio.get("volume"): result["volume"] = biblio["volume"]
    if biblio.get("issue"): result["number"] = biblio["issue"]

    # DOI/URL/ISSN/ISBN
    if data.get("doi"): result["doi"] = data["doi"]
    if data.get("url"): result["url"] = data["url"]
    # Identifiers can include ISBN/ISSN
    for ident in data.get("identifiers") or []:
        if ident.get("identifierType", "").upper() == "ISBN":
            result["isbn"] = ident.get("identifier")
        if ident.get("identifierType", "").upper() == "ISSN":
            result["issn"] = ident.get("identifier")

    # Subjects -> keywords
    subs = data.get("subjects") or []
    if subs:
        result["keywords"] = ", ".join([s.get("subject") for s in subs if s.get("subject")])

    # Descriptions -> abstract
    desc = data.get("descriptions") or []
    for d in desc:
        if d.get("description"):
            result["abstract"] = d["description"]
            break

    return result


def _search_openalex():
    return None


def _merge_responses(response_a: Dict[str, Any], response_b: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(response_a)
    for k, v in response_b.items():
        if k not in result or not result[k]:
            result[k] = v
    return result


def _normalize_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)  # remove punctuation
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _seq_ratio(a: str, b: str) -> float:
    a_n = _normalize_text(a)
    b_n = _normalize_text(b)
    if not a_n or not b_n:
        return 0.0
    return SequenceMatcher(None, a_n, b_n).ratio()


def _split_authors(authors_str: str) -> Iterable[str]:
    if not authors_str:
        return []
    # replace ' and ' with comma to combine, then split
    s = re.sub(r"\band\b", ",", authors_str, flags=re.IGNORECASE)
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return parts


def _last_name(name: str) -> str:
    n = _normalize_text(name)
    toks = n.split()
    return toks[-1] if toks else ""


def _extract_candidate_authors(cand: Dict[str, Any]) -> Iterable[str]:
    if cand.get("author"):
        return _split_authors(str(cand["author"]))
    if cand.get("authors"):
        return _split_authors(str(cand["authors"]))
    return []


def _author_overlap_ratio(query_authors: str, cand_authors: Iterable[str]) -> float:
    """
    Compute a surname Jaccard-like overlap between query authors and candidate authors.
    Returns value in [0,1]. Empty on either side -> 0.
    """
    q_names = set(filter(None, (_last_name(a) for a in _split_authors(query_authors))))
    c_names = set(filter(None, (_last_name(a) for a in cand_authors)))
    if not q_names or not c_names:
        return 0.0
    inter = len(q_names & c_names)
    union = len(q_names | c_names)
    return inter / union if union else 0.0


def match_score(
        query_title: str,
        query_authors: str,
        candidate: Dict[str, Any],
        title_weight: float = 0.8,
) -> Tuple[float, float, float]:
    """
    Compute a combined score in [0,1] plus the sub-scores (title, authors).
    - title_weight (0..1) is applied to title similarity; the rest goes to authors.
    Returns: (combined, title_score, author_score)
    """
    cand_title = str(candidate.get("title", "") or "")
    title_score = _seq_ratio(query_title, cand_title)

    cand_authors = list(_extract_candidate_authors(candidate))
    author_score = _author_overlap_ratio(query_authors, cand_authors)

    title_weight = max(0.0, min(1.0, title_weight))
    combined = title_weight * title_score + (1.0 - title_weight) * author_score
    return combined, title_score, author_score


def is_same_paper(
        query_title: str,
        query_authors: str,
        candidate: Dict[str, Any],
        threshold: float = 0.80,
        title_weight: float = 0.80,
) -> bool:
    combined, title_score, author_score = match_score(query_title, query_authors, candidate, title_weight)
    return combined >= threshold

print(lookup_bibtex_fields_by_title('10.2307/1919439', ''))