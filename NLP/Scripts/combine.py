import argparse
import json
import codecs
import simplejson
import re
import io
import os
import fnmatch
import sys



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
    #NER_FOLDER = "/home/maxsteal/nlp/ner-merge/ner-data"
    #POS_DATA = "/home/maxsteal/nlp/ner-merge/pos_data"
    NER_FOLDER = sys.args[1]
    POS_DATA = sys.args[2]
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
