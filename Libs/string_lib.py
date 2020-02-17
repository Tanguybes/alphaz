import re

def is_number(txt):
    try:
        a = float(txt)
        return True
    except: 
        return False

def sort_words(words_dict):
    return {x[0]:x[1] for x in sorted(words_dict.items(), key=lambda item: item[1],reverse=True)}

def is_carac(test):
    string_check = re.compile('[@_!#$%^€&*()<>?/\|}{~:]')
 
    if(string_check.search(test) == None):
        return False
    else: 
        return True

def get_words(txt):
    pm = re.findall(r'\([^()]*\)', txt)
    for p in pm:
        txt = txt.replace(p,'')

    words = txt.split()

    words_out = []
    for x in words:
        x = x.lower()
        if is_carac(x): continue
        if '.' in x:    continue
        if '+' in x:    continue
        if '-' in x:    continue
        if "'" in x:    continue
        if "," in x:    continue
        if ';' in x:    continue
        if '<' in x:    continue
        if '>' in x:    continue
        if '·' in x:    continue
        if '[' in x:    continue
        if x == 'est':  continue 
        if x == 'le':   continue 
        if x == 'est':  continue 
        if x == 'des':  continue 
        if x == 'les':  continue 
        if len(x) == 1: continue
        if len(x) == 2: continue
        if is_number(x) : continue

        words_out.append(x)
    return words_out
