# -*- coding: utf-8 -*-
"""Canonical lecture topics L1-L42."""

LECTURES = [
    ("L1-2",   "Diseases of microcirculation and edema"),
    ("L3-4",   "Acute inflammation, including cells and mediators"),
    ("L5",     "Outcomes of acute inflammation"),
    ("L6-7",   "Chronic inflammation and reparative process"),
    ("L8",     "Pathology of infection"),
    ("L9",     "Neoplastic development"),
    ("L10-11", "Neoplasia"),
    ("L12",    "Principle of specimen collections"),
    ("L13",    "Basic diagnostic radiology"),
    ("L14",    "Radiobiology and basic radiotherapy"),
    ("L15",    "Radiopharmaceutical and basic nuclear medicine"),
    ("L16-17", "Radiation physics"),
    ("L18",    "Drug discovery and development"),
    ("L19",    "Pharmacokinetics I (Absorption)"),
    ("L20",    "Pharmacokinetics II (Distribution)"),
    ("L21",    "Pharmacokinetics III (Metabolism, Excretion)"),
    ("L22",    "Pharmacokinetics IV (Pharmacokinetic parameters)"),
    ("L23",    "Pharmacodynamics"),
    ("L24",    "Introduction to ANS Pharmacology"),
    ("L25-26", "Sympathomimetic and Sympatholytic drugs I-II"),
    ("L28-29", "Parasympathomimetic and parasympatholytic drugs"),
    ("L30",    "Introduction to CMT and concept of rational drug use"),
    ("L31",    "Cell Wall Inhibitors"),
    ("L32",    "Inhibitors of metabolism and inhibitors of nucleic acid"),
    ("L33-34", "Protein synthesis inhibitors and miscellaneous"),
    ("L35-36", "Cancer chemotherapy"),
    ("L37",    "Immunomodulating agents"),
    ("L38",    "Antiseptic and disinfectant"),
    ("L39",    "Adverse drug effects"),
    ("L40",    "Pharmacogenetics"),
    ("L41",    "Antifungal agents"),
    ("L42",    "Anti-non retroviral agents"),
    ("PARA",   "Antiparasitic drugs (added)"),
]

UNCLASSIFIED = ("UNCLASSIFIED", "Unclassified / needs manual review")

LECTURE_KEYS = [k for k, _ in LECTURES] + [UNCLASSIFIED[0]]
LECTURE_TITLE = dict(LECTURES + [UNCLASSIFIED])
LECTURE_ORDER = {k: i for i, (k, _) in enumerate(LECTURES)}
LECTURE_ORDER[UNCLASSIFIED[0]] = len(LECTURES)
