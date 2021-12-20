from collections import defaultdict

from pathlib import Path
from pylexibank.dataset import Dataset as BaseDataset 
from pylexibank import Language, FormSpec, Cognate
from pylexibank import progressbar

from clldutils.misc import slug
import attr
import re


@attr.s
class CustomLanguage(Language):
    Latitude = attr.ib(default=None)
    Longitude = attr.ib(default=None)
    InAnalysis = attr.ib(default=None)
    #SubGroup = attr.ib(default=None)
    #Family = attr.ib(default='Sino-Tibetan')
    #Source_ID = attr.ib(default=None)
    #WiktionaryName = attr.ib(default=None)
    #Area = attr.ib(default=None)


@attr.s
class CustomCognate(Cognate):
    Root = attr.ib(default=None)


class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "triangulation"
    language_class = CustomLanguage
    cognate_class = CustomCognate
    form_spec = FormSpec(
            missing_data=("–", "-"),
            brackets={"(": ")", "[": "]", "{": "}"},
            first_form_only=True,
            separators = (";", "/", "~", ","),
            replacements=[
                (" inf. = soˁḳïš ?", ""),
                ("arla < avərla", "arla"),
                ("? (köterip) ", ""),
                ("olur-. olïr-", "olur"),
                ("?? ", ""),
                (" + 'motion verb'", ""),
                ("kele-", "kele"),
                ("'(walking) stick'", ""), (" + motion verb", ""), (" ", "_")] 
            )
    
    def cmd_download(self, args):
        
        self.raw_dir.download(
                "https://figshare.com/ndownloader/files/28217394?private_link=748bf751fe3ba7752046",
                "tea3geo.xml"
                )
        self.raw_dir.download_and_unpack("https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-04108-8/MediaObjects/41586_2021_4108_MOESM3_ESM.zip",
                "2021-02-02920E-s3/16_Eurasia3angle_synthesis_SI 1_BV 254_REV2021.09.22.xlsx")
        self.raw_dir.xlsx2csv("16_Eurasia3angle_synthesis_SI 1_BV 254_REV2021.09.22.xlsx")
        # change first line 
        with open(self.raw_dir / "16_Eurasia3angle_synthesis_SI 1_BV 254_REV2021.09.22.1.csv") as f:
            rows = [row for row in f]
            with open(self.raw_dir / "data-sheet.csv", "w") as f:
                for row in rows[1:]:
                    f.write(row)


    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.
        """
        with open(self.raw_dir / "tea3geo.xml") as f:
            data = [line.strip() for line in f]
            geo = {}
            for row in data[270:368]:
                lang, coords = row.split(" = ")
                lat, lon = coords.strip(",").split(" ")
                geo[lang] = [lat, lon]
        concepts = {}
        for concept in self.concepts:
            idx = concept["NUMBER"]+'_'+slug(concept['ENGLISH'])
            args.writer.add_concept(
                    ID=idx,
                    Name=concept["ENGLISH"]
                    )
            for gloss in concept["LEXIBANK_GLOSS"].split(" // "):
                concepts[gloss] = idx
        languages = {}
        INA = []
        for language in self.languages:
            if language["NameInSheet"].strip():
                in_analysis = 1 if language["IDInXML"] in geo else 0
                if in_analysis:
                    INA += [language["IDInXML"]]
                args.writer.add_language(
                        ID=language["ID"],
                        Name=language["Name"],
                        Family=language["Family"],
                        Latitude=language["Latitude"],
                        Longitude=language["Longitude"],
                        Glottocode=language["Glottocode"],
                        InAnalysis = in_analysis,
                        ISO639P3code=language["ISO639P3code"]
                        )
                languages[language["NameInSheet"]] = language["ID"]
        args.writer.add_sources()
        for i, row in enumerate(self.raw_dir.read_csv("data-sheet.csv",
                dicts=True, delimiter=",")):
            # headers are inconsistent, have to clean this
            concept = row["Meaning"].strip()
            proto = row["MRCA Root"]
            for language, lid in languages.items():
                entry = row.get(language, row.get(language+' ')).strip()
                if entry:
                    for lex in args.writer.add_forms_from_value(
                            Language_ID=lid,
                            Parameter_ID=concepts[concept],
                            Value=entry,
                            Cognacy=str(i+1),
                            Loan=True if entry.endswith(" bor") else False
                            ):
                        args.writer.add_cognate(
                                lexeme=lex,
                                Cognateset_ID=str(i+1),
                                Root=proto)

