#!/usr/bin/env python3
"""
Sri Shodashi (Tripura Sundari) Ashtottara Shatanama Stotram - Data builder

Reads:
- ~/shodashi-research/stotram.txt (Devanagari stotra from sanskritdocuments.org)
- ~/shodashi-research/namavali.txt (Devanagari namāvalī - 108 names)
- ~/Downloads/shodashi-ashtottara-stotram-meanings.md (user's curated IAST + meanings)

Writes:
- data.js with all 108 names + 20 verses
"""

import json
import re
from pathlib import Path

RESEARCH = Path.home() / 'shodashi-research'
USER_MD = Path.home() / 'Downloads' / 'shodashi-ashtottara-stotram-meanings.md'
OUT = Path.home() / 'shodashi-ashtottara' / 'data.js'


# Devanagari → IAST mapping (vowels + consonants)
DEVA_VOWELS = {
    'अ': 'a', 'आ': 'ā', 'इ': 'i', 'ई': 'ī', 'उ': 'u', 'ऊ': 'ū',
    'ऋ': 'ṛ', 'ॠ': 'ṝ', 'ऌ': 'ḷ', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
}

DEVA_VOWEL_SIGNS = {
    'ा': 'ā', 'ि': 'i', 'ी': 'ī', 'ु': 'u', 'ू': 'ū',
    'ृ': 'ṛ', 'ॄ': 'ṝ', 'ॢ': 'ḷ', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
}

DEVA_CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ṅ',
    'च': 'c', 'छ': 'ch', 'ज': 'j', 'झ': 'jh', 'ञ': 'ñ',
    'ट': 'ṭ', 'ठ': 'ṭh', 'ड': 'ḍ', 'ढ': 'ḍh', 'ण': 'ṇ',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'ś', 'ष': 'ṣ', 'स': 's', 'ह': 'h',
    'ळ': 'ḷ',
}

VIRAMA = '्'
ANUSVARA = 'ं'
VISARGA = 'ः'
CANDRABINDU = 'ँ'


def deva_to_iast(text):
    """Convert Devanagari text to IAST. Handles vowels, consonants, virama, anusvara, visarga."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in DEVA_VOWELS:
            # Independent vowel
            out.append(DEVA_VOWELS[c])
            i += 1
        elif c in DEVA_CONSONANTS:
            # Consonant - has implicit 'a' unless followed by vowel sign or virama
            cons = DEVA_CONSONANTS[c]
            i += 1
            # Look ahead
            if i < n and text[i] == VIRAMA:
                # Halant: no vowel
                out.append(cons)
                i += 1
            elif i < n and text[i] in DEVA_VOWEL_SIGNS:
                # Has vowel sign
                out.append(cons + DEVA_VOWEL_SIGNS[text[i]])
                i += 1
            else:
                # Implicit 'a'
                out.append(cons + 'a')
            # Now check for anusvara/visarga following the syllable
            if i < n and text[i] == ANUSVARA:
                out.append('ṃ')
                i += 1
            elif i < n and text[i] == VISARGA:
                out.append('ḥ')
                i += 1
            elif i < n and text[i] == CANDRABINDU:
                out.append('m̐')
                i += 1
        elif c == ANUSVARA:
            out.append('ṃ')
            i += 1
        elif c == VISARGA:
            out.append('ḥ')
            i += 1
        elif c == VIRAMA:
            i += 1  # stray virama, skip
        elif c == 'ॐ':
            out.append('oṃ')
            i += 1
        elif c.isspace() or c in '।॥-':
            out.append(c)
            i += 1
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def parse_namavali(path):
    """Parse the namāvalī file. Returns list of 108 (full_line, bare_devanagari_name) tuples.

    Source format: "श्रीत्रिपुरायै नमः ।"
    The bare name (in dative case) is "त्रिपुरायै"; full line includes "श्री" prefix and "नमः".
    """
    with open(path) as f:
        text = f.read()
    # Find lines like "श्री<name> नमः ।"
    pattern = re.compile(r'श्री([^।\n]+?)\s*नमः\s*।')
    lines = []
    for m in pattern.finditer(text):
        full = m.group(0).strip()
        bare = m.group(1).strip()
        lines.append((full, bare))
    return lines


def parse_stotram(path):
    """Parse the stotra. Returns list of verses [{number, devanagari, role}].
    Roles: 'framing' (1-2), 'names' (3-17), 'phalashruti' (18-20).
    """
    with open(path) as f:
        text = f.read()
    # Find region between "॥ श्रीषोडशीशतनामस्तोत्रम् ॥" type marker (skip the title) and the colophon
    start = text.find("भृगुरुवाच")
    end = text.find("इति ब्रह्मयामले")
    if start < 0:
        raise RuntimeError("Could not find start marker")
    if end < 0:
        end = len(text)
    body = text[start:end]

    verses = []
    pattern = re.compile(r'(.+?)॥\s*(\d+)॥', re.DOTALL)
    for m in pattern.finditer(body):
        chunk = m.group(1).strip()
        num = int(m.group(2))
        chunk = re.sub(r'\s+', ' ', chunk).strip()
        # Strip speaker tags
        chunk = re.sub(r'^(भृगुरुवाच|ब्रह्मोवाच)\s*[-–—]*\s*', '', chunk).strip()
        # Strip viniyoga clause that appears between V2 and V3
        chunk = re.sub(r'अस्य.*?विनियोगः\s*॥', '', chunk, flags=re.DOTALL).strip()
        # Strip leading ॐ
        chunk = re.sub(r'^ॐ\s*', '', chunk).strip()
        if not chunk:
            continue
        if num <= 2:
            role = 'framing'
        elif num <= 17:
            role = 'names'
        else:
            role = 'phalashruti'
        verses.append({"number": num, "devanagari": chunk, "role": role})
    return verses


def parse_user_meanings(path):
    """Parse the user's markdown to extract IAST → meaning + collective verse meanings.

    Returns:
      name_meanings: dict mapping IAST (without diacritics, lowercase, simplified) → meaning
      verse_meanings: dict mapping verse_number (3-17, 18-20) → collective_meaning
      verse_iast: dict mapping verse_number → IAST verse text
      framing_translations: dict mapping 1, 2 → english translation
    """
    md = path.read_text()
    name_meanings = {}
    verse_meanings = {}
    verse_iast = {}
    framing = {}
    phalashruti_translations = {}

    # Extract verse blocks: "### Verse N - Title" through next "###" or "---"
    # First, find each verse section
    verse_blocks = re.split(r'\n### Verse (\d+)', md)
    # verse_blocks[0] is preamble, then alternating: number, content, number, content...
    for i in range(1, len(verse_blocks), 2):
        if i + 1 >= len(verse_blocks):
            break
        vnum = int(verse_blocks[i])
        content = verse_blocks[i + 1]

        # Find the IAST verse text (lines starting with > * after the title)
        iast_match = re.search(r'>\s*\*([^*]+)\*\s*\|\s*\n>\s*\*([^*]+)\*\s*\|\|\s*\d+\s*\|\|', content)
        if not iast_match:
            iast_match = re.search(r'>\s*\*([^*]+)\*', content, re.DOTALL)
        if iast_match:
            verse_iast[vnum] = re.sub(r'\s+', ' ', iast_match.group(0).replace('>', '').replace('*', '').strip())

        # For verses with name tables, extract names
        # Table format: | **Name** | Meaning |
        for tm in re.finditer(r'\|\s*\*\*([^*|]+)\*\*\s*\|\s*([^|\n]+?)\s*\|', content):
            iast_name = tm.group(1).strip()
            meaning = tm.group(2).strip()
            # Normalize key: lowercase, strip diacritics
            key = simplify_iast(iast_name)
            name_meanings[key] = (iast_name, meaning)

        # Collective meaning for the verse
        cm_match = re.search(r'\*\*Collective meaning:\*\*\s*([^\n]+(?:\n(?!\*\*|###|---)[^\n]+)*)', content)
        if cm_match:
            verse_meanings[vnum] = cm_match.group(1).strip().replace('\n', ' ')

        # Framing meaning (V1, V2) - "**Meaning:**"
        if vnum <= 2:
            mm = re.search(r'\*\*Meaning:\*\*\s*([^\n]+(?:\n(?!\*\*|###|---)[^\n]+)*)', content)
            if mm:
                framing[vnum] = mm.group(1).strip().replace('\n', ' ')

        # Phalashruti meanings (V18-20) - "**Meaning:**"
        if vnum >= 18:
            mm = re.search(r'\*\*Meaning:\*\*\s*([^\n]+(?:\n(?!\*\*|###|---)[^\n]+)*)', content)
            if mm:
                phalashruti_translations[vnum] = mm.group(1).strip().replace('\n', ' ')

    return name_meanings, verse_meanings, verse_iast, framing, phalashruti_translations


def simplify_iast(s):
    """Lowercase + strip diacritics for matching. Anusvara normalized to 'n' (not 'm')
    to match common spellings like sañjñā ↔ saṃjñā."""
    s = s.lower()
    table = str.maketrans({
        'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṛ': 'r', 'ṝ': 'r', 'ḷ': 'l',
        'ṅ': 'n', 'ñ': 'n', 'ṭ': 't', 'ḍ': 'd', 'ṇ': 'n',
        'ṃ': 'n', 'ḥ': 'h', 'ś': 's', 'ṣ': 's',
    })
    s = s.translate(table)
    s = re.sub(r"[^a-z]", '', s)
    return s


# Manual overrides for namāvalī source quirks (typos, splits from compound user entries)
NAMAVALI_MEANING_OVERRIDES = {
    # Source typo "श्म्भुवनिता" should be "शम्भुवनिता" → Śambhuvanitā
    20: ("Śambhuvanitā", "Consort of Shambhu (the source has a minor spelling variant)"),
    # Source typo "शीग्रसिद्धिदा" should be "शीघ्रसिद्धिदा" → Śīghrasiddhidā
    25: ("Śīghrasiddhidā", "Bestower of swift siddhi"),
    # Source variant "ऋतुरूपा"; the stotra body has क्रतुरूपा (Kraturūpā)
    38: ("Kraturūpā", "Of the form of yajña (the stotra reads Kraturūpā here)"),
    # Source has "संज्ञा" (with anusvāra) → equivalent to "सञ्ज्ञा" (Sañjñā) in user MD
    55: ("Sañjñā", "The Conscious One (Sūrya's primary consort)"),
    # Namāvalī splits user's compound "Somasūryāgninayanā" into 2 names
    103: ("Sūryāgninayanā", "Whose eyes are sun and fire"),
    # Source spelling "अर्द्धन्दु" → equivalent to user's "Ardhendudhāriṇī"
    105: ("Ardhendudhāriṇī", "Wearer of the half-moon (on her crown)"),
    # Namāvalī #100 combines user's V16 names "Śatacandrānanā" + "Devī" into one name
    100: ("Śatacandrānanā Devī", "The Goddess of face like a hundred moons"),
    # User MD has compound Bhaktibhāvaparāyaṇā; namāvalī splits into 71 + 72
    71: ("Bhaktiparāyaṇā", "Absorbed in devotion (bhakti)"),
    72: ("Bhāvaparāyaṇā", "Absorbed in devotional disposition (bhāva)"),
    # User MD has compound Somasūryāgninayanā; namāvalī splits into 102 (Soma-) + 103 (Sūryāgni-)
    102: ("Somanayanā", "Whose eye is the moon"),
}


# Hand-curated dative → nominative for each of 108 names from namavali.
# The namavali names are in dative case ("त्रिपुरायै") - we want nominative ("त्रिपुरा").
def deva_dative_to_nominative(d):
    """Strip Devanagari dative endings."""
    rules = [
        ('ायै', 'ा'),     # -āyai → -ā
        ('्यै', 'ी'),     # -yai (consonant + halant) → -ī
        ('वे',  'ू'),     # -ave → -ū
        ('त्रे', 'ता'),   # -tre → -tā (mātre → mātā)
        ('ये',  'ी'),     # -ye → -ī
    ]
    for src, tgt in rules:
        if d.endswith(src):
            return d[:-len(src)] + tgt
    return d


def main():
    namavali = parse_namavali(RESEARCH / 'namavali.txt')
    verses = parse_stotram(RESEARCH / 'stotram.txt')
    name_meanings, verse_meanings, verse_iast, framing, phala_translations = parse_user_meanings(USER_MD)

    print(f"Namāvalī entries: {len(namavali)}")
    print(f"Stotra verses: {len(verses)}")
    print(f"Name meanings parsed from MD: {len(name_meanings)}")
    print(f"Verse meanings: {len(verse_meanings)}")
    print(f"Framing translations: {len(framing)}")
    print(f"Phalashruti translations: {len(phala_translations)}")

    assert len(namavali) == 108, f"Expected 108 namāvalī entries, got {len(namavali)}"

    # Map each name to a verse number (3-17)
    # The 108 names span verses 3-17. Names per verse count is variable.
    # The stotra verses contain the names; we walk through them sequentially.
    # For the Shodashi stotra, we know verse boundaries from the source text.
    # Just compute name-to-verse mapping by counting tokens per verse.
    verse_name_counts = {}  # verse_num → count of names
    for v in verses:
        if v["role"] != "names":
            continue
        v_text = v["devanagari"]
        # Split on whitespace, filter danda/digits
        cleaned = re.sub(r'[।॥]', ' ', v_text)
        cleaned = re.sub(r'[०-९0-9]', '', cleaned)
        tokens = [t for t in cleaned.split() if t]
        # Each token is approximately one name (some compounds, but namāvalī uses splits)
        # We'll match the namāvalī count to verses by knowing the stotra structure
        verse_name_counts[v["number"]] = len(tokens)

    # The namāvalī gives us 108 names total. Distribute them to verses based on token counts,
    # knowing that the namāvalī sometimes splits compounds.
    # The token-counts give an approximation; we'll just sequentially assign.
    name_to_verse = {}
    name_idx = 0
    # Hand-curated counts based on the source stotra:
    # V3: 10, V4: 8, V5: 7, V6: 6, V7: 6, V8: 6, V9: 7, V10: 10, V11: 8,
    # V12: 6 (split: 7 in namavali due to bhakti-bhava split), V13: 6, V14: 10, V15: 8,
    # V16: 5 (split: 5 → 5 because Śatacandrānanā-Devyai = 1 but Soma+Sūryāgni = 2), V17: 4
    # Actual namavali distribution (verified by counting "नमः" between syllable transitions):
    # Looking at the namavali file marker comments: "१०" after V3, "२०" after V5,
    # "३०" after V6, "४०" after V8, "५०" after V9, "६०" after V10, "७०" after V12 first half,
    # ... let me count from the namavali text directly.

    # Actually, simplest: use the namavali markers (१०, २०, ..., १००, १०८) to know where each
    # block of 10 ends. Combined with verse text token counting, we can assign.

    # For now, simple approach: split 108 names into verses 3-17 with predefined counts.
    # Counts (from the user's markdown table sizes), adjusted for namāvalī's 108 split:
    counts = {
        3: 10, 4: 8, 5: 7, 6: 6, 7: 6, 8: 6, 9: 7, 10: 10,
        11: 8, 12: 7, 13: 6, 14: 10, 15: 8, 16: 5, 17: 4,
    }
    # Sum check
    total = sum(counts.values())
    print(f"Sum of per-verse name counts: {total}")
    if total != 108:
        # Adjust V12 since the namavali splits Bhaktibhāva into 2
        # Or adjust V16 since namavali combines Śatacandrānanā+Devī but splits Somasūryāgni
        pass

    # Assign names to verses by counts
    for vn in sorted(counts.keys()):
        cnt = counts[vn]
        for _ in range(cnt):
            if name_idx < 108:
                name_to_verse[name_idx + 1] = vn
                name_idx += 1
    # Any leftover go on V17
    while name_idx < 108:
        name_to_verse[name_idx + 1] = 17
        name_idx += 1

    def title_case_iast(s):
        """Capitalize first letter, preserving diacritics."""
        if not s:
            return s
        return s[0].upper() + s[1:]

    # Build names list
    names = []
    used_meaning_keys = set()
    for i in range(108):
        num = i + 1
        full_line, dative_dv = namavali[i]
        nom_dv = deva_dative_to_nominative(dative_dv)
        nom_iast_raw = deva_to_iast(nom_dv)
        nom_iast = title_case_iast(nom_iast_raw)
        dative_iast = deva_to_iast(dative_dv)
        full_iast = "śrī " + dative_iast + " namaḥ"

        # Manual overrides for namāvalī source quirks
        if num in NAMAVALI_MEANING_OVERRIDES:
            override_iast, override_meaning = NAMAVALI_MEANING_OVERRIDES[num]
            nom_iast = override_iast
            meaning = override_meaning
        else:
            # Look up meaning from user's markdown
            key = simplify_iast(nom_iast_raw)
            meaning_entry = name_meanings.get(key)
            if not meaning_entry:
                # Fuzzy match: longest prefix match
                best_match = None
                best_len = 0
                for mkey, mval in name_meanings.items():
                    m = 0
                    for j in range(min(len(mkey), len(key))):
                        if mkey[j] == key[j]:
                            m += 1
                        else:
                            break
                    if m >= 4 and m > best_len:
                        best_len = m
                        best_match = mval
                meaning_entry = best_match
            meaning = meaning_entry[1] if meaning_entry else ''

        names.append({
            "number": num,
            "devanagari": nom_dv,
            "iast": nom_iast,
            "meaning": meaning,
            "verse": name_to_verse.get(num, 17),
            "devanagariDative": dative_dv,
            "iastDative": dative_iast,
            "namavaliDevanagari": full_line,
            "namavaliIast": full_iast,
        })

    # Add per-verse name lists
    for v in verses:
        v["names"] = []
    verse_by_num = {v["number"]: v for v in verses}
    for n in names:
        v = verse_by_num.get(n["verse"])
        if v:
            v["names"].append(n["number"])
        # Also attach collective meaning if applicable
    for v in verses:
        if v["number"] in verse_meanings:
            v["collectiveMeaning"] = verse_meanings[v["number"]]
        if v["number"] in framing:
            v["meaning"] = framing[v["number"]]
        if v["number"] in phala_translations:
            v["meaning"] = phala_translations[v["number"]]
        # Speaker
        if v["number"] == 1:
            v["speaker"] = "Bhṛgu"
            v["speakerDeva"] = "भृगुरुवाच"
        elif v["number"] == 2:
            v["speaker"] = "Brahmā"
            v["speakerDeva"] = "ब्रह्मोवाच"

    # Final data
    data = {
        "meta": {
            "totalNames": 108,
            "totalVerses": len(verses),
            "namesVerseStart": 3,
            "namesVerseEnd": 17,
            "phalashrutiVerseStart": 18,
            "phalashrutiVerseEnd": 20,
            "source": "Brahmayāmala Tantra, Pūrvakhaṇḍa - dialogue between Brahmā and sage Bhṛgu",
            "devata": "Sri Shodashi (Tripura Sundari)",
            "rishi": "Shambhu (Shiva)",
            "chandas": "Anuṣṭup",
            "version": "1.0",
        },
        "names": names,
        "verses": verses,
        "openingNote": (
            "The Sri Shodashi Ashtottara Shatanama Stotra is a sacred 108-name hymn "
            "to Goddess Shodashi (Tripura Sundari) from the Pūrvakhaṇḍa of the Brahmayāmala Tantra. "
            "It is a dialogue in which Lord Brahmā reveals the 108 names to sage Bhṛgu, "
            "extracting them from the thousand names of Sundarī. The text describes itself as "
            "guhyād guhyataraṃ guhyaṃ - secret, more secret than the secret, the very heart of secrecy."
        ),
    }

    js = "/* Sri Shodashi Ashtottara Shatanama Stotram - generated by build_data.py - DO NOT edit by hand */\n"
    js += "const SHODASHI_DATA = "
    js += json.dumps(data, ensure_ascii=False, indent=2)
    js += ";\n"

    OUT.write_text(js)
    print(f"\nWrote {OUT} ({len(js)} bytes, {len(names)} names, {len(verses)} verses)")


if __name__ == '__main__':
    main()
