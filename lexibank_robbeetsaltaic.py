from collections import defaultdict

from pathlib import Path
from pylexibank.dataset import Dataset as BaseDataset 
from pylexibank import Language, FormSpec, Cognate
from pylexibank import progressbar

from clldutils.misc import slug
import attr


@attr.s
class CustomLanguage(Language):
    Latitude = attr.ib(default=None)
    Longitude = attr.ib(default=None)
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
    id = "robbeetsaltaic"
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

        self.raw_dir.xls2csv("16_Eurasia3angle_synthesis_SI 1_BV 254.xls")

    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.
        """
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
        for language in self.languages:
            if language["NameInSheet"].strip():
                args.writer.add_language(
                        ID=language["ID"],
                        Name=language["Name"],
                        Family=language["Family"],
                        Latitude=language["Latitude"],
                        Longitude=language["Longitude"],
                        Glottocode=language["Glottocode"],
                        ISO639P3code=language["ISO639P3code"]
                        )
                languages[language["NameInSheet"]] = language["ID"]
        args.writer.add_sources()
        for i, row in enumerate(self.raw_dir.read_csv("16_Eurasia3angle_synthesis_SI 1_BV 254.1.csv",
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
                            Cognacy=str(i+1)
                            ):
                        args.writer.add_cognate(
                                lexeme=lex,
                                Cognateset_ID=str(i+1),
                                Root=proto)

