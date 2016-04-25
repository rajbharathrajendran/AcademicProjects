import argparse
import json
import codecs
import simplejson
import re
import io
import os
import fnmatch
import sys

def get_args():
    parser = argparse.ArgumentParser(description='Combine Named Entity, POS Information and create input file for CRF')
    # parser.add_argument('-p', '--pos', type=str, dest='pos', help='The file containing POS and root word information', required=True)
    parser.add_argument('-ne', '--ner', type=str, dest='ner', help='The file containing Named Entity tagging', required=True)
    parser.add_argument('-r', '--raw', type=str, dest='raw', help='The raw input file', required=True)
    parser.add_argument('-o', '--out', type=str, dest='out', help='The name of the output file', required=True)
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
            parsed_entity.push(token.replace(",", ""))
        # For handling 2.5
        elif decimal_pattern.match(token):
            parsed_entity.push(token.replace(".", "##"))
        else:
            parsed_entity.push(token)
    entity = " ".join(entity)
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
                    if i == 0:
                        sentence.append([unit, tagging_info["cls"] + u"-B"])
                    else:
                        sentence.append([unit, tagging_info["cls"] + u"-I"])
                    if unit.endswith("."):
                        output.append(sentence)
                        sentence = []
            else:
                start_idx = idx
                token = tokens[idx]
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


def get_pos_sentence_extractor(pos_info):
    lines = pos_info.splitlines()
    sentence = []
    for line in lines:
        if line.strip() == '':
            yield sentence
            sentence = []
        else:
            sentence.append(line.split(" "))


#def combine_ner_and_pos(ner_sentence, pos_sentence):
#    for ner, pos in zip(ner_input, pos_info):


def test_crf_output(pos_info, ner_input):
    f = codecs.open("test_crf_out.txt", "w", "utf-8")
    for i in range(len(ner_input)):
        ner_data = ner_input[i]
        j = 0
        for j in range(len(pos_info)):
            if len(ner_data) == len(pos_info[j]) and ner_data[0].split(" ")[0] == pos_info[j][0].split(" ")[0]:
                f.write(str(len(ner_data))+" "+str(len(pos_info[j])))
                f.write(ner_data[1].split(" ")[0]+" "+ pos_info[j][1].split(" ")[0])
                sys.exit()
                for ner in ner_data:
                    f.write(ner+"\n")
                f.write("\n")
                for pos in pos_info[j]:
                    f.write(pos+"\n")
                f.write("\n")
    f.close()



def prepare_crf_output(pos_info, ner_input, out_file):
    i=0
    for i in range(len(ner_input)):
        print ner_input[i]
        ner_data = ner_input[i]
        j = 0
        for j in range(len(pos_info)):
            pos_data = pos_info[j]
            if len(ner_data) >0 and pos_data > 0 and len(ner_data) == len(pos_data) and ner_data[0].split(" ")[0] == pos_data[0].split(" ")[0]:
                m = 0
                flag = True
                zero_flag = False
                for m in range(len(ner_data)):
                    if ner_data[m].split(" ")[0] != pos_data[m].split(" ")[0]:
                        flag = False
                        break
                    if ner_data[m].split(" ")[1] != "" and ner_data[m].split(" ")[1] != "0":
                        print ner_data[m].split(" ")[1]
                        zero_flag = True
                #if flag and zero_flag:
                if flag:
                    for ner_data, pos_data in zip(ner_input[i], pos_info[j]):
                        pos_final_data = pos_data.split(" ")
                        ner_final_data = ner_data.split(" ")
                        if pos_final_data[0] == ner_final_data[0]:
                            word = pos_final_data[0]
                            pos = pos_final_data[1] 
                            if len(pos_final_data) > 2:
                                root = pos_final_data[2]
                            else:
                                root = "0"
                            if len(pos_final_data) > 3:
                                suffix = pos_final_data[3]
                            else:
                                suffix = "0"  
                            ner = ner_final_data[1].strip()
                            if len(ner) == 0:
                                ner = "0"
                        out_file.write(word+" "+pos+" "+root+" "+suffix+" "+ner+"\n")            
                    out_file.write("\n")




        # for pos_data in pos_info[i]:
        #     if(ner_data[0][i] == pos_data[0] and len(ner_data) == len(pos_)):


def data_from_file(file_path, data_list):
    f = codecs.open(file_path, "r", "utf-8")
    temp = []
    for entry in f:
        if entry == "\n":
            data_list.append(temp)
            temp = []
        else:
            temp.append(entry.strip())
    print entry
    f.close()

def pos_ner_data(pos_folder, ner_folder):
    f = codecs.open("final_crf_out.txt", "w", "utf-8")
    if pos_folder == "" or pos_folder == None or ner_folder == "" or ner_folder == None:
        sys.exit("Invalid Folder")
    for root, subdirs, files in os.walk(pos_folder):
        for filename in fnmatch.filter(files, '*.txt'):
            pos_info = []
            ner_input = []
            data_from_file(os.path.join(pos_folder, filename), pos_info)
            data_from_file(os.path.join(ner_folder, filename), ner_input)
            prepare_crf_output(pos_info, ner_input, f)


def main():

    #This code is the combiner
    NER_FOLDER = "/home/maxsteal/nlp/ner-merge/ner-data"
    POS_DATA = "/home/maxsteal/nlp/ner-merge/pos_data"
    pos_ner_data(POS_DATA, NER_FOLDER)
    

    #combiner ends here

    '''
    args = get_args()
    raw_file = read_raw_file(args.raw)

    # Split into paras
    paras = raw_file.splitlines()

    ner_info = read_ner_info(args.ner)
    (fp_paras, fp_ner_info) = disambiguate_tagging_and_reconstruct(paras, ner_info)


    fp_paras = [u' '.join(para) for para in fp_paras]

    f = codecs.open("sample.txt", "w", "utf-8")
    f.write(u'\n'.join(fp_paras))

    with io.open('sample.json', 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(fp_ner_info, ensure_ascii=False)))

    
    f = codecs.open("sample.txt", encoding="utf-8")
    fp_paras = f.read()

    fp_paras = fp_paras.splitlines()

    f = codecs.open("sample.json", encoding="utf-8")
    fp_ner_info = json.load(f)
    '''

    # ner_crf_input = convert_ner_to_crf_format(fp_paras, fp_ner_info)

    # f = codecs.open("ner_crf_input.txt", "w", "utf-8")
    # for sentence in ner_crf_input:
    #     for token in sentence:
    #         f.write(token[0] + u" " + token[1] + u"\n")
    #     f.write(u"\n")

    # pos_info = read_pos_info(args.pos)


if __name__ == '__main__':
    main()
