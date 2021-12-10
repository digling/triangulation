from lingpy import *
from lexibase.lexibase import LexiBase


cols = ['concept_id', 'concept_name', 'language_id', 'language_name', 'value',
        'form', 'segments', 'glottocode', "cognacy", "language_family",
        #'comment'
        ]


lex = LexStat.from_cldf("../cldf/cldf-metadata.json", columns=cols)
lex.cluster(method='sca', threshold=0.45, ref="autocogid")
alms = Alignments(lex, ref="autocogid")
alms.align()
alms.add_entries("subgroup", "language_family", lambda x: x)
alms.add_entries("cogid", "cognacy", lambda x: int(x))


D = {0: ["doculect", "subgroup", "concept", "value", "form",
    "tokens", "cogid", "autocogid", "alignment"]}
for idx in alms:
    D[idx] = [alms[idx, h] for h in D[0]]
lex = LexiBase(D, dbase="robbeetsaltaic.sqlite3")
lex.create("robbeetsaltaic")
