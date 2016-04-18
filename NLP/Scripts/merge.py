'''
Script to generate Named Entity Tagged Corpus by combining the raw text with the annotation information
* Resolves tokenization ambiguities
* Generates NE Tagged Corpus in format compatible with POS and CRF input
'''

import argparse
import json
import codecs
import simplejson
import re
from string import maketrans
import io

def get_args():
    parser = argparse.ArgumentParser(description='Combine Named Entity, POS Information and create input file for CRF')
    '''
    parser.add_argument('-p', '--pos', type=str, dest='pos', help='The file containing POS and root word information', required=True)
    parser.add_argument('-ne', '--ner', type=unicode, dest='ner', help='The file containing Named Entity tagging', required=True)
    parser.add_argument('-r', '--raw', type=unicode, dest='raw', help='The raw input file', required=True)
    parser.add_argument('-o', '--out', type=str, dest='out', help='The name of the output file', required=True)
    '''
    parser.add_argument('-n', '--name', type=str, dest='name', help='Name for the {txt|json|pos} files and crf output', required=True)
    args = parser.parse_args()
    return args


def read_raw_file(filename):
    f = codecs.open(filename, encoding='utf-8')
    contents = f.read()
    return contents


def read_ner_info(filename):
    f = codecs.open(filename, encoding='utf-8')
    ner_info = json.loads(json.loads(f.read()))
    print type(ner_info)
    return ner_info


def read_pos_info(filename):
    f = codecs.open(filename, encoding='utf-8')
    return f.read()

date_pattern = re.compile("^[0-9]+\.$")
number_pattern = re.compile("^[0-9,]+[0-9]+$")
plain_number_pattern = re.compile("^[0-9]+$")
decimal_pattern = re.compile("^[0-9.]+[0-9]+$")


def get_atomic_units(entity):
    parsed_entity = []
    for token in entity:
        # Handle 84,000
        if number_pattern.match(token):
            parsed_entity.append(token.replace(",", ""))
        # For handling 2.5
        elif decimal_pattern.match(token):
            parsed_entity.append(token.replace(".", "##"))
        else:
            parsed_entity.append(token)
    entity = " ".join(parsed_entity)
    return [token for token in entity.replace(",", ", ").replace(".", ". ").replace("##", ".").replace(";", "; ").split(" ") if token != ""]


def get_tagging_info_for_token(token_no, ner_info):
    for annotation in ner_info:
        if annotation["start"] == token_no:
            return annotation


def get_disambiguation_input(atomic_units, tagging_info):
    while True:
        try:
            print "\n ****** \n"
            print "Existing Named Entity: ", tagging_info["token"]
            s = u''
            for idx, unit in enumerate(atomic_units):
                s += str(idx) + u': ' + unit + u'\t'
            print "New split tokens: ", s
            start = int(raw_input("Enter start token no: "))
            end = int(raw_input("Enter end token no: "))

            print "YOUR INPUT: ", " ".join(atomic_units[start: end+1])
            return start, end+1
        except Exception, e:
            print e
            print "Couldn't understand your input. Please retry"


def disambiguate_tagging_and_reconstruct(paras, ner_info):
    new_paras = []
    new_ner_info = []
    global_token_no = 0
    augmented = 0
    for para in paras:
        new_para = []
        tokens = para.split(" ")
        idx = 0
        while idx != len(tokens):
            tagging_info = get_tagging_info_for_token(global_token_no, ner_info)

            entity_len = tagging_info["length"] if tagging_info is not None else 1
            entity = tokens[idx : idx + entity_len]

            # Set index and token number appropriately
            idx += entity_len

            atomic_units = get_atomic_units(entity)
            new_tokens_count = len(atomic_units) - len(entity) if len(atomic_units) > 0 else 0

            if new_tokens_count > 0 and tagging_info is not None:
                # Now if it has tagging information, disambiguate
                (start, end) = get_disambiguation_input(atomic_units, tagging_info)
                new_ner_info.append({
                  "token": (" ").join(atomic_units[start:end]),
                  "start": global_token_no + augmented + start,
                  "length": end-start,
                  "cls": tagging_info["cls"]
                })
            elif tagging_info is not None:
                new_ner_info.append({
                  "token": " ".join(atomic_units),
                  "start": global_token_no + augmented,
                  "length": entity_len,
                  "cls": tagging_info["cls"]
                })

            '''
            if new_tokens_count > 0:
                s = u''
                for word in entity:
                    s += word + u' '
                print s, new_tokens_count
            '''

            global_token_no += entity_len
            augmented += new_tokens_count
            new_para.extend(atomic_units)

        new_paras.append(new_para)
    return (new_paras, new_ner_info)


def is_not_atomic(token):
    if token.endswith(".") and len(token) <= 3 and not date_pattern.match(token):
        return True
    return False


def get_combined_units(entity):
    idx = 0
    result = []
    while idx < len(entity):
        token = entity[idx]

        # Handle E. Ve. Ra
        if is_not_atomic(token):
            new_token = ''
            ended = False
            while is_not_atomic(token):
                new_token += token[:-1]
                idx += 1
                if idx == len(entity):
                    ended = True
                    break
                token = entity[idx]
            if not ended:
                # Handle ki.mu. 3
                if not plain_number_pattern.match(token):
                    new_token += token
                else:
                    idx -= 1
            result.append(new_token)
        # Handle 18.
        elif token.endswith(".") and date_pattern.match(token):
            result.append(token[:-1])
        else:
            result.append(token)
        idx += 1
    return result


def convert_ner_to_crf_format(paras, ner_info):
    output = []
    global_token_no = 0
    for para in paras:
        idx = 0
        tokens = para.split(" ")
        sentence = []
        while idx < len(tokens):
            tagging_info = get_tagging_info_for_token(global_token_no, ner_info)

            if tagging_info is not None:
                entity_len = tagging_info["length"] if tagging_info is not None else 1
                entity = tokens[idx : idx + entity_len]

                # Set index and token number appropriately
                idx += entity_len
                global_token_no += entity_len

                combined_units = get_combined_units(entity)
                for i, unit in enumerate(combined_units):
                    if unit.endswith("."):
                        sentence.append([unit[:-1], tagging_info["cls"] + (u"-B" if i == 0 else u"-I")])
                        output.append(sentence)
                        sentence = []
                    else:
                        sentence.append([unit, tagging_info["cls"] + (u"-B" if i == 0 else u"-I")])
            else:
                start_idx = idx
                token = tokens[idx]
                # Handle E. Ve. Ra
                if token.strip() == ".":
                    output.append(sentence)
                    sentence = []
                elif is_not_atomic(token):
                    new_token = ''
                    ended = False
                    while is_not_atomic(token):
                        new_token += token[:-1]
                        idx += 1
                        if idx == len(entity):
                            ended = True
                            break
                        token = tokens[idx]
                    if not ended:
                        # Handle ki.mu. 3
                        if not plain_number_pattern.match(token):
                            new_token += token
                        else:
                            idx -= 1
                    sentence.append([new_token, u" 0"])
                # Handle 18.
                elif token.endswith(".") and number_pattern.match(token[:-1]):
                    sentence.append([token[:-1], u" 0"])
                # Handle actual end of sentence
                elif token.endswith("."):
                    # TODO: Check if . is to be removed in end of sentence
                    sentence.append([token[:-1], u" 0"])
                    output.append(sentence)
                    sentence = []
                else:
                    sentence.append([token, u" 0"])
                idx += 1
                global_token_no += idx - start_idx
    return output


'''
def get_ner_enriched_sentence_generator(paras, ner_info):
    global_token_no = 0
    changed = 0
    for para in paras:
        word_generator = get_word_generator(para, ner_info)
        sentence = []
        for (word, ne_type) in word_generator:
            if word.endswith("."):
                yield sentence
                sentence = []
            else:
                sentence.append([word, ne_type])
'''


def get_ner_sentence_generator(ner_input):
    for sentence in ner_input:
        yield sentence


def translate_punctuations(to_translate):
    punctuations = u'"*+<=>^`\'{|}~'
    translate_table = dict((ord(char), None) for char in punctuations)
    return to_translate.translate(translate_table)


def process_ner_crf_input(ner_input):
    output = []
    for sentence in ner_input:
        new_sentence = []
        for idx, token in enumerate(sentence):
            word = token[0]
            stripped_word = translate_punctuations(word)
            if stripped_word != "":
                if stripped_word.endswith(",") or stripped_word.endswith("?"):
                    new_sentence.append([stripped_word[:-1], token[1]])
                    next_token = sentence[idx+1] if idx < len(sentence) - 1 else None
                    if next_token is not None and next_token[1].endswith("-I") and (token[1].endswith("-I") or token[1].endswith("-B")):
                        new_sentence.append([stripped_word[-1:], next_token[1]])
                    else:
                        new_sentence.append([stripped_word[-1:], "0"])
                else:
                    new_sentence.append([stripped_word, token[1]])
        output.append(new_sentence)
    return output


def get_pos_sentence_extractor(pos_info):
    lines = pos_info.splitlines()
    sentence = []
    for line in lines:
        if line.strip() == '':
            yield sentence
            sentence = []
        else:
            sentence.append(line.split(" "))


def compare_ner_and_pos(ner_sentence, pos_sentence):
    for idx in range(len(ner_sentence)):
        cur_ner_token = ner_sentence[idx]
        if idx < len(pos_sentence):
            cur_pos_token = pos_sentence[idx]
            if cur_pos_token[0].strip() == cur_ner_token[0].strip() or (cur_ner_token[0].endswith(".") and cur_ner_token[0][:-1] == cur_pos_token[0]):
                # So far so good, continue
                continue
            else:
                # No match
                return 0
        elif idx != 0:
            # Partial match
            return 2
        else:
            # No match
            return 0
    # Full match
    return 1


def combine_ner_and_pos(ner_sentence, pos_sentence):
    sentence = []
    for idx in range(len(ner_sentence)):
        crf_tokens = []
        pos_tokens = pos_sentence[idx]
        ner_tokens = ner_sentence[idx]
        crf_tokens.extend(pos_tokens)
        to_add = 4-len(pos_tokens)
        for i in range(to_add):
            crf_tokens.append("0")
        crf_tokens.append(ner_tokens[1])
        sentence.append(crf_tokens)
    return sentence


def prepare_combined_crf_input(pos_info, ner_input):
    pos_sentence_extractor = get_pos_sentence_extractor(pos_info)
    ner_sentence_extractor = get_ner_sentence_generator(ner_input)
    output = []

    for pos_sentence in pos_sentence_extractor:
        if len(pos_sentence) == 0:
            continue
        match_found = 0
        while match_found == 0:
            try:
                ner_sentence = ner_sentence_extractor.next()
            except Exception, e:
                print e
                return output
            match_found = compare_ner_and_pos(ner_sentence, pos_sentence)
        if match_found == 1:
            crf_sentence = combine_ner_and_pos(ner_sentence, pos_sentence)
            output.append(crf_sentence)
    return output


def write_in_crf_file_format(name, input):
    f = codecs.open(name, "w", "utf-8")
    for sentence in input:
        for token in sentence:
            f.write(token[0] + u" " + token[1] + u"\n")
        f.write(u"\n")


def full_pipeline():
    args = get_args()
    name = args.name
    raw_file = read_raw_file("Raw/" + name + ".txt")

    # Split into paras
    paras = raw_file.splitlines()

    ner_file = "Ann/" + name + ".json"
    ner_info = read_ner_info(ner_file)
    (fp_paras, fp_ner_info) = disambiguate_tagging_and_reconstruct(paras, ner_info)

    fp_paras = [u' '.join(para) for para in fp_paras]

    f = codecs.open("CleanedRaw/" + name + "-cleaned.txt", "w", "utf-8")
    f.write(u'\n'.join(fp_paras))

    with io.open("CleanedAnn/" + name + "-cleaned.json", 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(fp_ner_info, ensure_ascii=False)))

    ner_crf_input = convert_ner_to_crf_format(fp_paras, fp_ner_info)
    ner_crf_input = process_ner_crf_input(ner_crf_input)

    write_in_crf_file_format("NER/" + name + ".ner", ner_crf_input)

    '''
    pos_file = name + ".pos"
    pos_info = read_pos_info(pos_file)

    crf_input = prepare_combined_crf_input(pos_info, ner_crf_input)

    write_in_crf_file_format(name + ".crf", crf_input)
    '''


def partial_pipeline():
    args = get_args()
    name = args.name
    f = codecs.open(name + "-cleaned.txt", encoding="utf-8")
    fp_paras = f.read()

    fp_paras = fp_paras.splitlines()

    f = codecs.open(name + "-cleaned.json", encoding="utf-8")
    fp_ner_info = json.load(f)

    ner_crf_input = convert_ner_to_crf_format(fp_paras, fp_ner_info)
    ner_crf_input = process_ner_crf_input(ner_crf_input)

    write_in_crf_file_format(name + ".ner", ner_crf_input)

    '''
    pos_file = name + ".pos"
    pos_info = read_pos_info(pos_file)

    crf_input = prepare_combined_crf_input(pos_info, ner_crf_input)

    write_in_crf_file_format(name + ".crf", crf_input)
    '''

if __name__ == '__main__':
    full_pipeline()