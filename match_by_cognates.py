# encoding=utf8
import requests
from bs4 import BeautifulSoup
from time import sleep

import os
import pickle
import argparse

from isv_nlp_utils.slovnik import get_slovnik
import pandas as pd
import rapidfuzz

# def infer_pos(details_string):



slovnik = get_slovnik()

from collections import defaultdict

major_langs = ['Bulgarian', 'Czech', 'Polish', "Russian", "Serbian"]
set_cols = dict(zip(major_langs, ["bg_set", "cs_set", "pl_set", "ru_set", "sr_set"]))

resulting_forms = []



i = 0
for k, v in words_data.items():
    i += 1
    
    scores = defaultdict(list)
    cognates_keys = [d_lang for d_lang in v.keys() if d_lang not in {"Related_NonSlavic", "Related_Slavic", "Etymology", "*"}]

    for lang in major_langs:
        set_col = set_cols[lang]

        for word in v.get(lang, []):
            found = slovnik[slovnik[set_col].apply(lambda x: word in x)]
            if len(found):
                for k_id, isv_form in found.isv.items():
                    flavorized_rec = v["*"]
                    sim = measure_isv_sim(isv_form, flavorized_rec)
                    if sim > 50:
                        # print(k_id, isv_form, v["*"], flavorized_rec, sim)
                        scores[k_id].append([lang, word, sim])
                        # print(lang, word, len(found))
                        # print(found[set_col].values)
    if len(scores) >= 1:
        #print(v["*"])
        # print(scores)
        max_sim = defaultdict(float)
        for k_id in list(scores):
            total_match = sum(s[-1] for s in scores[k_id])
            isv_form = slovnik.loc[k_id].isv
            max_sim[isv_form] = max(max_sim[isv_form], total_match)
        winner_isv = max(max_sim.items(), key=lambda x: x[1])[0]
        for k_id in list(scores):
            isv_form = slovnik.loc[k_id].isv
            N = len(scores[k_id])
            total_match = sum(s[-1] for s in scores[k_id]) / N
            etm_info = BeautifulSoup("".join(v["Etymology"])).text
            cognates = {kl: v[kl] for kl in cognates_keys}
            if isv_form == winner_isv:
                # print(v["*"], k_id, isv_form, total_match)
                resulting_forms.append((v["*"], k_id, isv_form, total_match, N, True, etm_info, cognates))
            else:
                resulting_forms.append((v["*"], k_id, isv_form, total_match, N, False, etm_info, cognates))

    #if len(scores) == 1:
    #    k_id = list(scores)[0]
    #    print(v["*"], k_id, slovnik.loc[k_id].isv)

praforms_df = pd.DataFrame(resulting_forms, columns="reconstructed isv_id isv_form match_score N is_best etm_info cognates".split())

praforms_df.sort_values(by="match_score")
