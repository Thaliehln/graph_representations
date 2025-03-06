import os
from datetime import date, datetime
from read_epoct_json2 import extract_nodes
from epoct import Diagnosis, FinalDiagnosis, Question, QuestionSequence, Answer
from shutil import copyfile, rmtree

def generate_arborescence(main_diagnosis_nodes, final_diagnosis_nodes, cc_nodes, data, keys, outdir):

    def format_label(lbl):

        lbl = lbl.replace("/", "-").replace(",", "").replace(" ", "_")
        idx = lbl.rfind("(")
        if idx>-1:
            lbl = lbl[:idx]
        if lbl[-1] == "_":
            lbl = lbl[:-1]
        return lbl

    export_dir = os.path.join(outdir, "export_{}".format(datetime.strftime(date.today(),'%d%b%y')))
    os.makedirs(export_dir, exist_ok=True)

    for d in os.listdir(export_dir):
        rmtree(os.path.join(export_dir, d), ignore_errors=True)
    with open(os.path.join(export_dir, "info.txt"), "w") as f:
        for k in keys:
            text = "{}: {}\n".format(k, data[k])
            f.write(text)

    cc_names = {} 
    for cc in cc_nodes:

        #Create directory
        cc_names[cc.getID()] = "{0:03d}_{1}".format(cc.getID(), format_label(cc.getLabel()))
        current_dir = os.path.join(export_dir, cc_names[cc.getID()])
        print(current_dir)
        
        md_names = {}
        for md in main_diagnosis_nodes:
            if md.getChiefComplaint() == cc:

                print("\t {}".format(md.getLabel()))
                #Create directory
                md_names[md.getID()] = "{0:03d}_{1}".format(md.getID(), format_label(md.getLabel()))
                current_subdir = os.path.join(current_dir, md_names[md.getID()])
                os.makedirs(current_subdir, exist_ok=True)
                
                imgname = "D{0:03d}_{1}.png".format(md.getID(), format_label(md.getLabel()))
                imgfile = os.path.join(outdir, "main_diagnoses", "node{0:03d}-full.png".format(md.getID()))
                copyfile(imgfile, os.path.join(current_subdir, imgname))

                for fd in final_diagnosis_nodes:
                    if fd.getMainDiagnosis() == md:
                        
                        imgname = "FD{0:03d}_{1}.png".format(fd.getID(), format_label(fd.getLabel()))
                        imgfile = os.path.join(outdir, "final_diagnoses", "node{0:03d}-full.png".format(fd.getID()))
                        copyfile(imgfile, os.path.join(current_subdir, imgname))

if __name__ == '__main__':

    import json
    import os

    json_path = r'C:\Users\langhe\switchdrive\Private\Unisanté\medal_c_18.06.20.json'
    outdir = r'C:\Users\langhe\switchdrive\Private\Unisanté\epoct_variables'
    
    # Load data from json file
    with open(json_path, encoding='utf8') as f:
        data = json.load(f)

    # Print clinical algorithm generic information
    keys = ['id', 'algorithm_id', 'name', 'version', 'version_id', 'author', 'created_at', 'updated_at']
    for k in keys:
        print("{}: {}".format(k, data[k]))

    # Extract node structure
    main_diagnosis_nodes, final_diagnosis_nodes, cc_nodes, question_seq_nodes = extract_nodes(data)

    # Create Word export
    generate_arborescence(main_diagnosis_nodes, final_diagnosis_nodes, cc_nodes, data, keys, outdir)