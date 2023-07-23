from enum import Enum

from Generic.Enums import Language, UIModule
from Generic.Essentials import essentials

class HelpEmbedStrings(Enum):
    def __call__(self, lang: Language):
        strings = essentials.get_language_dict(lang, UIModule.Help)
        
        self.value["title"] = strings[f"Help.{self.name}.Title"]
        for cmd in self.value["texts"].keys():
            self.value["texts"][cmd] = strings[f"Help.{self.name}.{cmd}.text"]

        return self.value

    Basic = {
        "title": "",
        "texts": {
              "/help": "",
              "/join": "",
              "/leave": ""
        }
    }

    Playback_1 = {
        "title": "",
        "texts": {
            "/playwith": "",
            "/play": "",
            "/np": "",
            "/pause": "",
            "/resume": "",
            "/skip": ""
        }
    }

    Playback_2 = {
        "title": "",
        "texts": {
            "/stop": "",
            "/seek": "",
            "/restart": "",
            "/loop": "",
            "/wholeloop": ""
        }
    }

    Queue = {
        "title": "",
        "texts": {
            "/queue": "",
            "/shuffle": "",
            "/remove": "",
            "/swap": "",
            "/move": ""
        }
    }