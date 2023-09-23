
from isv_nlp_utils import constants
from isv_nlp_utils.slovnik import get_slovnik
# from isv_translate import translate_sentence, postprocess_translation_details, prepare_parsing

from ast import literal_eval
import os
import glob

from isv_nlp_utils.flavorization.tokenizer import extract_stem_prefix_suffix


AO = 'ꜵ'
YI = "⒥"
NASAL = "⒩"
BACKTICK = "’"

def write_base_verb(indices, base_verb):
    partial_verb_prefixes.loc[
        indices,
        'base_verb'
    ] = base_verb

possible_prefixes = {
    "ne", "bez", "naj",
    "do", "iz", "na", "nad", "ne", "o", "ob", "obez", "od", "po", "pod", 
    "prě", "prěd", "pri", "pro", 
    "raz", "råz",
    "de", 
    "s", "sȯ",
    "so", "su", "vo", "voz", 
    "sų", "u", "v", 
    "vȯz", "vȯ",
    "vy", "za"
}
possible_prefixes = sorted(list(possible_prefixes), key=len, reverse=True)
possible_suffixes = [" sę", "iti", "ěti", 'nųti', 'ov', 'yvati', 'ati', 'j', 'ivati']
possible_suffixes = sorted(list(possible_suffixes), key=len, reverse=True)



def bite_all_suffixes_off(word, verb_nest):

    can_continue = True
    suffixes = []

    while can_continue:
        can_continue = False
        for pref in possible_suffixes:
            if word.endswith(pref):
                new_word = word[:-len(pref)]
                if new_word.startswith(verb_nest):
                    word = new_word
                    suffixes.append(pref)
                    can_continue = True
                    break
    return word, "+".join(reversed(suffixes)) + "+"

bite_all_suffixes_off('privęzyvati', 'privęz')
('privęz', 'yvati+')


"’"
word = 'nedoråzuměti'

def bite_all_prefixes_off(word, verb_nest):

    can_continue = True
    prefixes = []

    while can_continue:
        can_continue = False
        for pref in possible_prefixes:
            if word.startswith(pref):
                # print(pref, word, word[len(pref):])
                new_word = word[len(pref):]
                if new_word.endswith(verb_nest):
                    word = new_word
                    prefixes.append(pref)
                    can_continue = True
                    break
    return word, "’".join(prefixes) + "’"

bite_all_prefixes_off('nedoråzuměti', 'uměti')
('uměti', 'ne’do’råz’')


def add_derived_nouns(ending, replacement=''):
    tmp_df = slovnik[slovnik.partOfSpeech.apply(infer_pos) == 'noun'].copy()
    tmp_df['repl'] = tmp_df.isv.str.replace(ending + "$", replacement)
    tmp_df = tmp_df.query(
        "isv not in @BEG and repl in @BEG"
    ).copy()
    for i, row in tmp_df.iterrows():
        repl = row.repl
        matches = partial_verb_prefixes.query("left_stem_cand == @repl")

        partial_verb_prefixes.loc[matches.index, "derived_nouns"] = partial_verb_prefixes.loc[matches.index, "derived_nouns"] + "|" + row.isv

    return tmp_df.isv.values.tolist()

def split_carefully(x, true_stem):
    if " " in x:
        x = x.split(" ")[0]
    x = x.replace('å', 'a')
    true_stem = true_stem.replace('å', 'a')

    if AO in true_stem:
        if true_stem.replace(AO, "a") in x:
            return list(x.partition(true_stem.replace(AO, "a")))
    return x.partition(true_stem.replace(AO, "o"))

from itertools import zip_longest, takewhile

def all_equal(items: (tuple, list, str)) -> bool:
    '''
    A helper function to test if 
    all items in the given iterable 
    are identical. 

    Arguments:
    item -> the given iterable to be used

    eg.
    >>> all_same([1, 1, 1])
    True
    >>> all_same([1, 1, 2])
    False
    >>> all_same((1, 1, 1))
    True
    >> all_same((1, 1, 2))
    False
    >>> all_same("111")
    True
    >>> all_same("112")
    False
    '''
    return all(item == items[0] for item in items)


def common_suffix(strings: (list, tuple), _min: int=0, _max: int=100) -> str:
    '''
    Given a list or tuple of strings, find the common suffix
    among them. If a common suffix is not found, an empty string
    will be returned.

    Arguments:
    strings -> the string list or tuple to
    be used.

    _min, _max - > If a common suffix is  found, 
    Its length will be tested against the range _min 
    and _max. If its length is not in the range, and
    empty string will be returned, otherwise the suffix
    is returned 

    eg.
    >>> common_suffix([rhyme', 'time', 'mime'])
    'me'
    >>> common_suffix(('boo', 'foo', 'goo'))
    'oo'
    >>> common_suffix(['boo', 'foo', 'goz'])
    ''
    '''
    suffix = ""
    strings = [string[::-1] for string in strings]
    for tup in zip_longest(*strings):
        if all_equal(tup):
            suffix += tup[0]
        else:
            if _min <= len(suffix) <= _max:
                return suffix[::-1]
            else:
                return ''
    return suffix[::-1]


def split_carefully(x, true_stem):
    if " " in x:
        x = x.split(" ")[0]
    if any(weird in true_stem for weird in "[]()?"):
        splitted = re.split(true_stem, x)
        found_stem = x[len(splitted[0]): -len(splitted[1])]
        assert len(splitted) == 2
        return splitted[0], found_stem, splitted[1]
    x = x.replace('å', 'a')
    true_stem = true_stem.replace('å', 'a')

    if AO in true_stem:
        if true_stem.replace(AO, "a") in x:
            return list(x.partition(true_stem.replace(AO, "a")))
    return x.partition(true_stem.replace(AO, "o"))

def insert_YI(word, signature):

    if " " in word:
        word = word.split(" ")[0]

    if word[-3:] == "ęti":
        word = word[:-3] + "in" + NASAL + "ti"
    if "trim" not in word and "klimat" not in word:
        word = word.replace("idti", "jdti").replace("imati", "jmati")
    if signature == {'s', 't'}:
        if word[-3:] == "sti":
            # rasti -> rastti
            word = word[:-3] + "stti"
        
    base, end = word[:-5], word[-5:]
    
    # jehati
    if signature == {'đ', 'h'}:
        end = end.replace("žđati", "h" + YI + "ati")
    
    if signature == {'ć', 's'}:
        end = end.replace("šćati", "st" + YI + "ati")
    if signature == {'ć', 't'}:
        end = end.replace("šćati", "st" + YI + "ati")
        end = end.replace("ćati", "t" + YI + "ati")
    if signature == {'ć', 'č'}:
        end = end.replace("čiti", "ćiti")
        end = end.replace("čati", "ćati")

    if signature == {'đ', 'd'}:
        end = end.replace("žđati", "zd" + YI + "ati")
        end = end.replace("đati", "d" + YI + "ati")

    # puskati?
    if signature == {'ć', 'k'}:
        end = end.replace("šćati", "sk" + YI + "ati")
    if signature == {"c", "č"}:
        end = end.replace("čati", "c" + YI + "ati")
        end = end.replace("čiti", "c" + YI + "iti")

    if signature == {'k', 'č'}:
        base, end = word[:-6], word[-6:]
        end = end.replace("ščiti", "sk" + YI + "iti")
        end = end.replace("čiti", "k" + YI + "iti").replace("čivati", "k" + YI + "ivati")


    # pisati
    if signature == {'š', 's'}:  
        end = end.replace("šati", "s" + YI + "ati")
        end = end.replace("šiti", "s" + YI + "iti")
        
    if signature == {'š', 'h'}:
        end = end.replace("šiti", "h" + YI + "iti")
        end = end.replace("šati", "h" + YI + "ati")
    if signature == {'š'}:
        base, end = word[:-6], word[-6:]
        end = end.replace("šiti", "h" + YI + "iti")
        end = end.replace("šati", "h" + YI + "ati")
        end = end.replace("šivati", "h" + YI + "ivati")
        

    if signature == {'č', 'k'}:
        end = end.replace("čati", "k" + YI + "ati")
        
    if signature == {'ž', 'z'}:
        end = end.replace("žati", "z" + YI + "ati")
    if signature == {'ž', 'g'}:
        base, end = word[:-6], word[-6:]

        end = end.replace("žati", "g" + YI + "ati")
        end = end.replace("žiti", "g" + YI + "iti")
        end = end.replace("živati", "g" + YI + "ivati")

    return base + end

def manual_insert(base_verb, true_stem, last_cons=set(), dry_run=True, from_base_verb=True):
    if from_base_verb:
        g = morphemes.query("base_verb == @base_verb")
    else:
        g = morphemes.query("isv == @base_verb")
    manual_insert_g(g, true_stem, last_cons, dry_run)

def manual_insert_g(g, true_stem, last_cons=set(), dry_run=True):

    for i, row in g.isv.apply(lambda x: split_carefully(insert_YI(x, last_cons), true_stem)).items():
        if any(weird in true_stem for weird in "[]()?"):
            found_stem = row[1]
        else: 
            found_stem = true_stem

        if not dry_run:
            morphemes.loc[i, ['_prefix', '_stem', '_suffix']] = row[0], found_stem, row[2]
        raw_isv = g.loc[i, 'isv']
        #if also_insert_noun:
        #    morphemes.loc[[i], 'base_noun'] = true_stem
        #    print(raw_isv, " <- ", true_stem)

        print(raw_isv, "=", row[0], found_stem, row[2])
        


def check_if_orphan(BASE):

    g = morphemes.query(" base_verb == @BASE")

    base_variants = set((g['_stem'] + g['_suffix']).unique())
    variants = set(base_variants)
    for (src, dst) in [
        ("t" + YI, "ć"), ("sk" + YI, 'šć'), ("st" + YI, 'šć'),
        ("d" + YI, "đ"), ("zd" + YI, "žđ"),
        ("k" + YI, "č"), ("c" + YI, "č"), ("sk" + YI, "šč"),
        ("g" + YI, "ž"), ("z" + YI, "ž"), 
        ("s" + YI, "š"), ("h" + YI, "š"), 
        (AO, "a"), (AO, "o"), (AO, "å"), 
        ("in" + NASAL, "ę"),
        ("tt", "t"),
        ("bv", "v"),
        ("jdti", "idti"), ("jmati", "imati")
        # žđ  "h" + YI ?
    ]:
        variants |= {v.replace(src, dst) for v in base_variants}
    return BASE not in variants

