from typing import Dict, Any, List

import requests


def lookup_bibtex_fields_by_title(query: str, timeout: float = 10.0) -> Dict[str, Any] | None:
    # Make session for api friendliness
    session = requests.session()
    session.headers.update({'User-Agent': 'BibSTEAK/0.1'})

    responses: List[Dict[str, Any]] = []

    # Execute API queries
    try:
        cr = _search_crossref(session, query, timeout)
        if cr:
            responses.append(cr)
    except Exception as e:
        print(e)

    try:
        db = _search_dblp(session, query, timeout)
        if db:
            responses.append(db)
    except Exception as e:
        print(e)

    # try:
    #     dc = _search_datacite()
    #     if dc:
    #         responses.append(dc)
    # except Exception:
    # pass

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
    result["authors"] = "placeholder"
    # TODO: Implement

    # Year(s)
    for k in ("issued", "published-print", "published-online"):
        date = data.get(k, {})
        date_parts = date.get("date-parts", [])
        if date_parts and date_parts[0]:
            result[k] = int(date_parts[0][0])
        else:
            result[k] = None

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
    data_info = data[0].get("info", [])
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
    if result["doi"]: result["url"] = f"https://doi.org/{result["doi"]}"
    else:
        if data.get("ee"): result["ee"] = data["ee"]

    return result


def _search_datacite():
    return None


def _search_openalex():
    return None


def _merge_responses(response_a: Dict[str, Any], response_b: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(response_a)
    for k, v in response_b.items():
        if k not in result or not result[k]:
            result[k] = v
    return result


print(lookup_bibtex_fields_by_title("New version of the Crimean Tatar resettlement"))
