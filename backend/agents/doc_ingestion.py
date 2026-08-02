# agents/doc_ingestion.py

import httpx
from bs4 import BeautifulSoup
import fitz                        # ye pymupdf hai — naam alag kyun?
                                   # PyMuPDF originally MuPDF ka wrapper
                                   # tha, import naam "fitz" reh gaya
import json
from dataclasses import dataclass, field
from typing import Dict            # Type hints ke liye
                                   # Python 3.9+ mein dict directly
                                   # use kar sakte ho but 3.8 support
                                   # ke liye typing import karo

# ─────────────────────────────────────────
# DATA CONTAINER
# Ye object poore project mein travel karega
# Har agent isko input lega ya output dega
# ─────────────────────────────────────────

@dataclass
class IngestedDoc:
    source_url: str
    format_type: str       # "openapi" / "html" / "pdf" / "text"
    raw_text: str          # poora content ek jagah
    sections: Dict         # {"authentication": "...", "endpoints": "..."}
    metadata: Dict = field(default_factory=dict)
    # default_factory=dict kyun?
    # @dataclass mein mutable defaults
    # directly nahi de sakte:
    # metadata: Dict = {}  ← YE WRONG HAI
    # Kyun? Sab instances ek hi dict share karte
    # field(default_factory=dict) har instance ke
    # liye naya dict banata hai


# ─────────────────────────────────────────
# AGENT CLASS
# ─────────────────────────────────────────

class DocIngestionAgent:
    """
    Koi bhi source lo → ek format mein do.

    Supported:
    - OpenAPI/Swagger JSON (.json, .yaml)
    - HTML documentation pages
    - PDF documents
    - Plain text / direct paste
    """

    # ─────────────────────────────────────
    # ROUTER METHOD
    # ─────────────────────────────────────

    def ingest(self, source: str) -> IngestedDoc:
        # Return type hint: -> IngestedDoc
        # Ye batata hai ki ye function
        # hamesha IngestedDoc return karega
        # IDE autocomplete isme help karta hai

        print(f"\n📥 Ingesting: {source[:60]}...")

        if source.endswith(".json") or source.endswith(".yaml"):
            print("   Format detected: OpenAPI/Swagger")
            return self._ingest_openapi(source)

        elif source.endswith(".pdf"):
            print("   Format detected: PDF")
            return self._ingest_pdf(source)

        elif source.startswith("http"):
            print("   Format detected: HTML")
            return self._ingest_html(source)

        else:
            print("   Format detected: Plain text")
            return self._ingest_text(source)

    # ─────────────────────────────────────
    # HANDLER 1: OpenAPI JSON
    # Best case — sab structured hota hai
    # ─────────────────────────────────────

    def _ingest_openapi(self, url: str) -> IngestedDoc:
        # Method naam underscore se shuru kyun?
        # Convention: _method = "private" method
        # Matlab: bahar se directly call mat karo
        # Sirf ingest() ke through aao

        resp = httpx.get(url, timeout=30)
        # timeout=30 kyun?
        # Bina timeout ke agar server respond na kare
        # program forever hang karega
        # 30 seconds reasonable limit hai

        resp.raise_for_status()
        # Ye line important hai
        # Agar 404/500 aaya → exception throw karo
        # Bina iske silently wrong data process hota

        spec = resp.json()
        # resp.text → raw string milti
        # resp.json() → directly Python dict milta
        # JSON API response ke liye hamesha .json() use karo

        # Sections alag kyun nikaal rahe hain?
        # RAG mein section-aware chunking hogi
        # "authentication" section se authentication
        # sawaal ka answer milega — mix nahi hoga
        sections = {
            "info": json.dumps(
                spec.get("info", {}), indent=2
            ),
            # spec.get("info", {}) kyun?
            # Agar "info" key exist na kare →
            # spec["info"] crash karega
            # spec.get("info", {}) → empty dict dega
            # Ye safe access pattern hai — hamesha use karo

            "servers": json.dumps(
                spec.get("servers", []), indent=2
            ),
            "authentication": json.dumps(
                spec.get("securitySchemes",
                spec.get("security", {})), indent=2
                # Nested .get() kyun?
                # OpenAPI 3.0 → "securitySchemes"
                # Swagger 2.0 → "security"
                # Dono handle karne ke liye
            ),
            "endpoints": json.dumps(
                spec.get("paths", {}), indent=2
            ),
            "schemas": json.dumps(
                spec.get("components", {})
                    .get("schemas", {}), indent=2
            )
        }

        # Empty sections hatao
        sections = {
            k: v for k, v in sections.items()
            if v and v not in ["{}", "[]", "null"]
            # Dictionary comprehension — filter karo
            # {} matlab empty dict as string
        }

        print(f"   ✅ Sections: {list(sections.keys())}")
        print(f"   ✅ Endpoints: {len(spec.get('paths', {}))}")

        return IngestedDoc(
            source_url=url,
            format_type="openapi",
            raw_text=json.dumps(spec, indent=2),
            sections=sections,
            metadata={
                "version": spec.get("openapi",
                           spec.get("swagger", "unknown")),
                "title": spec.get("info", {}).get("title", ""),
                "endpoint_count": len(spec.get("paths", {}))
            }
        )

    # ─────────────────────────────────────
    # HANDLER 2: HTML Pages
    # ─────────────────────────────────────

    def _ingest_html(self, url: str) -> IngestedDoc:

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; HermesBot/1.0)"
            # User-Agent kyun?
            # Kuch websites bots ko block karti hain
            # Browser jaisa User-Agent deke block avoid karo
        }

        resp = httpx.get(
            url,
            headers=headers,
            follow_redirects=True,
            # follow_redirects=True kyun?
            # Kuch URLs redirect karte hain (301/302)
            # Ye automatically follow karta hai
            timeout=30
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        # resp.text kyun? resp.json() nahi?
        # HTML text format mein hota hai, JSON nahi
        # BeautifulSoup text leta hai, dict nahi

        # Noise remove karo
        noise_tags = [
            "nav", "footer", "header",
            "script", "style", "aside"
        ]
        for tag in soup(noise_tags):
            tag.decompose()
            # decompose() → element ko DOM se hata do
            # vs remove() → element return karta hai
            # decompose() cleaner hai garbage collect ke liye

        # Sections detect karo
        sections = {}
        current_section = "general"
        current_content = []

        for element in soup.find_all(
            ["h1", "h2", "h3", "p", "code", "pre", "li"]
        ):
            # find_all() → matching sab elements list mein
            # Sequential order maintain hoti hai
            # Isliye section detection work karta hai

            if element.name in ["h1", "h2", "h3"]:

                if current_content:
                    content = " ".join(current_content).strip()
                    if len(content) > 50:
                        sections[current_section] = content

                current_section = (
                    element.get_text()
                           .strip()
                           .lower()
                           .replace(" ", "_")[:50]
                    # [:50] kyun?
                    # Dict key bahut lamba nahi hona chahiye
                    # 50 chars enough hai section identify ke liye
                )
                current_content = []

            else:
                text = element.get_text().strip()
                if text:
                    current_content.append(text)

        if current_content:
            sections[current_section] = " ".join(current_content)

        if not sections:
            sections["general"] = soup.get_text(
                separator=" ", strip=True
            )

        print(f"   ✅ Sections: {list(sections.keys())[:5]}")

        return IngestedDoc(
            source_url=url,
            format_type="html",
            raw_text=soup.get_text(separator=" ", strip=True),
            sections=sections,
            metadata={
                "title": soup.title.string if soup.title else "",
                "section_count": len(sections)
            }
        )

    # ─────────────────────────────────────
    # HANDLER 3: PDF
    # ─────────────────────────────────────

    def _ingest_pdf(self, url: str) -> IngestedDoc:
        import urllib.request
        # urllib.request kyun? httpx nahi?
        # PDF binary file hai
        # httpx.get() text/json ke liye best hai
        # urllib.request.urlretrieve() directly
        # file disk pe save karta hai — PDF ke liye better

        pdf_path = "/tmp/hermes_api_doc.pdf"
        # /tmp kyun?
        # Temporary files ke liye OS ka scratch space
        # Windows pe: C:/Users/user/AppData/Local/Temp/
        # Mac/Linux pe: /tmp/
        urllib.request.urlretrieve(url, pdf_path)

        doc = fitz.open(pdf_path)

        sections = {}
        full_text = ""

        for page_num, page in enumerate(doc): # type: ignore

            
            # enumerate() → (index, value) pairs deta hai
            # page_num 0 se shuru hota hai
            page_text = page.get_text()
            full_text += page_text
            sections[f"page_{page_num + 1}"] = page_text
            # +1 kyun? 0-indexed ko 1-indexed banana
            # User ke liye "page_1" zyada readable hai

        print(f"   ✅ Pages: {len(doc)}")

        return IngestedDoc(
            source_url=url,
            format_type="pdf",
            raw_text=full_text,
            sections=sections,
            metadata={"pages": len(doc)}
        )

    # ─────────────────────────────────────
    # HANDLER 4: Plain Text
    # ─────────────────────────────────────

    def _ingest_text(self, text: str) -> IngestedDoc:

        return IngestedDoc(
            source_url="direct_paste",
            format_type="text",
            raw_text=text,
            sections={"general": text},
            metadata={"char_count": len(text)}
        )