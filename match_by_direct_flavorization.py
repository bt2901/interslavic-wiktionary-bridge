# encoding=utf8
import requests
from bs4 import BeautifulSoup
from time import sleep

import os
import pickle
import argparse

from isv_nlp_utils.flavorization.replacer import VOWELS
from isv_nlp_utils.flavorization.parsing import parse_multireplacer_rules
from isv_nlp_utils.flavorization.tokenizer import compute_annotated_tokens, pretty_stringify
from isv_nlp_utils.flavorization.replacer import process_multireplacing, morphological_flavorise

from isv_nlp_utils import constants
from isv_nlp_utils.slovnik import get_slovnik
# from isv_translate import translate_sentence, postprocess_translation_details, prepare_parsing

from ast import literal_eval
import os
import glob


# from isv_nlp_utils.flavorization.selector import produce_string, filter_good_spellings, filter_lingua, init_detector, init_hunspell

from isv_nlp_utils.flavorization.tokenizer import tokens_to_exhaustive_string_list
from razdel import sentenize


JAN_EXAMPLES = """byti, dobry, svět, rěka, język, svęty, pųt́, rųka, 
vųtroba, pavųk, otėc, pės, sȯn, pěsȯk, gråd, kråva, glåva, mlådy, 
brěg, prěd, mlěko, trg, krčma, dŕžati, smŕt́, dȯlg, kȯlbasa, tȯlsty, vȯlk, kupjų, zemja, 
ljubiti, hvaljeńje, dėnj, hrånjeńje, caŕ, tvorjeńje, 
kost́, dȯžd́, loś, knęź, prošų, tęžeńje, svěća, noć, među, ščetka, moliti, grlo, glåva, jego, 
usiĺje, dělańje, primoŕje, žit́je, orųd́je, podlěśje
""".replace("\n", "").replace("t́", "ť").replace("d́", "ď").split(', ')


with open("wiktionary_extended_new.json", "r", encoding="utf8") as f:
    words_data = json.load(f)

all_reconstructions = set()
reconstructed_articles = {}

for k, v in words_data.items():
    if v['Related_Slavic']:
        all_reconstructions |= set([x[1][1:] for x in v['Related_Slavic']])
    all_reconstructions.add(v['*'])
    reconstructed_articles[v['*']] = v

len(all_reconstructions), len(reconstructed_articles)
# (13323, 3692)



rules_struct, declared_constants = parse_multireplacer_rules(
        r"C:\dev\razumlivost\src\flavorizers\slow\protoslavic.ts"
    )

def f(word, rules_struct, declared_constants, pos_tag):
    cap = False
    space_after = ""
    
    slovnik_pos = ""
    isv_lemma = None
    variants = [ParseVariant(
                    [word],
                    pos_tag, slovnik_pos, isv_lemma,
                    None, "", 
                    False
                )]

    ann_token = AnnotatedToken(
        variants,
        cap, space_after,
    )
    
    tokens_base = [ann_token]
    # tokens = morphological_flavorise(tokens_base, morph, flavor_rules[LANG])
    tokens = process_multireplacing(tokens_base, rules_struct, declared_constants)
    return tokens

word = 'těnь'
word = 'bolь'
word = "zemja"
pretty_stringify(
    f(word, rules_struct, declared_constants, {""})
)
# [zemja|zemlja]


for word, data in reconstructed_articles.items():
    if "ťi" in word:
        print(word)
        tokens = f(word, rules_struct, declared_constants, "")

        for var in tokens[0].variants[0].text_variants:
            if any(
                    morph.word_is_known(var1.replace("đ", "dʒ")) for var1 in 
                    [var, 
                     var.replace("ȯ", "o"), var.replace("ė", "e"), 
                     var.replace("nj", "n"), var.replace("lj", "l"),
                     var.replace("ď", "d"), var.replace("ť", "t"), var.replace("å", "a"), var.replace("ų", "u"),
                     var.replace("ś", "s"), var.replace("ź", "z"), var.replace("ŕ", "r")
                    ]
            ):
                print("OK!", var)



slovnik_matches = {}
unknown = set()

for word, data in reconstructed_articles.items():
    pos_tag = "Adjective" if "Adjective" in data["POS"] else ""
    tokens = f(word, rules_struct, declared_constants, pos_tag)

    for var in tokens[0].variants[0].text_variants:
        if any(
                morph.word_is_known(var1.replace("đ", "dʒ")) for var1 in 
                [var, 
                 var.replace("ȯ", "o"), var.replace("ė", "e"), 
                 var.replace("ě", "e"), var.replace("ę", "e"), var.replace("ė", "e"),
                 var.replace("nj", "n"), var.replace("lj", "l"),
                 var.replace("ď", "d"), var.replace("ť", "t"), var.replace("å", "a"), var.replace("ų", "u"),
                 var.replace("ś", "s"), var.replace("ź", "z"), var.replace("ŕ", "r")
                ]
        ):
            slovnik_matches[var] = word
            break
    else:
        if len(data) > 25:
            print(word, var, len(data))
        if len(data) > 10:
            unknown.add(word)

