from urllib.parse import urljoin

def org_schema(base):
    return {"@context":"https://schema.org","@type":"Organization","name":"ReneEnergy","url":base}

def website_schema(base):
    return {"@context":"https://schema.org","@type":"WebSite","name":"ReneEnergy","url":base}

def article_schema(base, path, title, desc):
    return {
        "@context":"https://schema.org","@type":"Article",
        "headline": title[:110], "description": desc[:300],
        "mainEntityOfPage": urljoin(base, path)
    }

def faq_schema(base, path, faqs):
    return {
        "@context":"https://schema.org","@type":"FAQPage","url":urljoin(base, path),
        "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]
    }
