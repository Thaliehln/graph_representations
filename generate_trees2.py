import os
from pygraphviz import *
from copy import deepcopy
from libs import read_epoct_json2
from definitions import JSON_PATH, OUTPUT_DIR, CLINICAL_KEYS_PATH
from utils import loadCategoryCoding, loadDiagnosisSeverity2, loadTests
from libs import algoreader, epoct

lightgray = "#D3D3D3"
gray = "#808080"
white = "#FFFFFF"
cqs = "#40e0d0"
cqsa = "#c9fffa"
cfd = "#FF5733"
cmd = "#FFC300"

def wrap_text(s, max_len):

    def wrap(s, max_len):
        idx = s[:max_len].rfind('/')
        if idx==-1:
            idx = s[:max_len].rfind(' ')
            s = s[:idx]+"\n"+ s[idx:]
        else:
            s = s[:idx+1]+"\n"+ s[idx+1:]
        return s

    if len(s) > max_len:
        s = wrap(s, max_len)
    return s

def wrap2_text(s, max_len):

    def wrap(s, max_len):
        idx = s[:max_len].rfind('/')
        if idx==-1:
            idx = s[:max_len].rfind(' ')
            s = s[:idx]+"<br />"+ s[idx:]
        else:
            s = s[:idx+1]+"<br />"+ s[idx+1:]
        return s

    if len(s) > max_len:
        s = wrap(s, max_len)
    return s

conv = dict()
conv["<"] = "&#60;"
conv[">"] = "&#62;"
conv["°"] = "&#176;"
conv["="] = "&#61;"
conv["/"] = "&#47;"

def format_reflbl(n):
    max_len = 20
    lbl = n.getLabel()
    for k, s in zip(conv.keys(), conv.values()):
        lbl = lbl.replace(k, s)
    idx = lbl.find('(')
    if idx>-1:
        lbl = lbl[:idx]
    lbl = "{}. {}".format(n.getReference(), lbl)
        
    lbl = wrap_text(lbl, max_len)
    return lbl

def format_albl(n):
    max_len = 20
    lbl = n.getLabel()
    for k, s in zip(conv.keys(), conv.values()):
        lbl = lbl.replace(k, s)
    idx = lbl.find('(')
    if idx>-1:
        lbl = lbl[:idx]
        
    lbl = wrap_text(lbl, max_len)
    return lbl

def html_format(qlbl, qbgc, albls, indices, bgcolors):

    nb_answers = len(albls)
    rlbl = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4"><TR><TD ROWSPAN="{}" PORT="e" BGCOLOR="{}">{}</TD><TD COLSPAN="1" PORT="f{}" BGCOLOR="{}">{}</TD></TR>'.format(nb_answers, qbgc, qlbl, indices[0], bgcolors[0], albls[0])
    for k, i, bgc in zip(albls[1:], indices[1:], bgcolors[1:]):
        rlbl += '<TR><TD PORT="f{}" BGCOLOR="{}">{}</TD></TR>'.format(i, bgc, k)
    rlbl += "</TABLE>>"
    return rlbl

def html_format_vert(qlbl, qbgc, albls, indices, bgcolors):

    nb_answers = len(albls)
    rlbl = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4"><TR><TD COLSPAN="{}" PORT="n" BGCOLOR="{}">{}</TD></TR><TR><TD PORT="f{}" BGCOLOR="{}">{}</TD>'.format(nb_answers, qbgc, qlbl, indices[0], bgcolors[0], albls[0])
    for k, i, bgc in zip(albls[1:], indices[1:], bgcolors[1:]):
        rlbl += '<TD PORT="f{}" BGCOLOR="{}">{}</TD>'.format(i, bgc, k)
    rlbl += "</TR></TABLE>>"
    return rlbl

###################
# ClinicalAlgo class
###################

class ClinicalAlgo():

    def __init__(self, horizontal=True):
        self._graph = AGraph(strict=False)
        self._horizontal = horizontal
        if self._horizontal:
            self._graph.graph_attr['rankdir'] = 'LR'
        self._graph.graph_attr['splines'] = 'spline'
        self._root    = {}
        self._nodes   = []
        self._edges   = []
        self._answers = []
    
    def setRoot(self, r):
        self._root['node'] = r
        self._root['id'] = r.getID()
        self._root['label'] = format_reflbl(r)
        self._root['shape'] = 'doubleoctagon'
        if type(r) is epoct.FinalDiagnosis:
            if r.getSeverity() == "mild":
                self._root['color'] = '#ccffcc'
            elif r.getSeverity() == "moderate":
                self._root['color'] = '#ffff99'
            elif r.getSeverity() == "severe":
                self._root['color'] = '#ff8080'
            else:
                self._root['color'] = lightgray
        elif type(r) is epoct.DiagnosisSequence:
            self._root['color'] = cmd
        elif type(r) is epoct.QuestionSequence:
            self._root['color'] = cqs
        else:
            self._root['color'] = lightgray

    def getRoot(self):
        return self._root

    def getNodes(self):
        return self._nodes

    def addNode(self, n):
        for n in self._nodes:
            self._nodes.append(n)

    def getEdges(self):
        return self._edges

    def addEdge(self, e):
        if e not in self._edges:
            self._edges.append(e)

    def addAnswer(self, a):
        self._answers.append(a)

    def getAnswers(self):
        return self._answers

    def draw(self):
        if type(self._root['node']) is not epoct.DiagnosisSequence:
            self._graph.add_node(self._root['id'], label=self._root['label'], shape=self._root['shape'], fillcolor=self._root['color'], style="filled")
        for n in self._nodes:
            if type(n['node']) is epoct.Question or type(n['node']) is epoct.QuestionSequence:
                self._graph.add_node(n['id'], label=n['html_label'], shape=n['shape'])
            else:
                self._graph.add_node(n['id'], label=n['label'], shape=n['shape'], fillcolor=n['color'], style="filled")
        for e in self._edges:
            if 'headport' in e.keys():
                if 'tailport' in e.keys():
                    self._graph.add_edge(e['id1'], e['id2'], tailport=e['tailport'], headport=e['headport'], key=e['key'], color=e['color'], label=e['label'], style=e["style"])
                else:
                    self._graph.add_edge(e['id1'], e['id2'], headport=e['headport'], key=e['key'], color=e['color'], label=e['label'], style=e["style"])
            else:
                if 'tailport' in e.keys():
                    self._graph.add_edge(e['id1'], e['id2'], tailport=e['tailport'], key=e['key'], color=e['color'], label=e['label'], style=e["style"])
                else:
                    self._graph.add_edge(e['id1'], e['id2'], key=e['key'], color=e['color'], label=e['label'], style=e["style"])
        
    def export2png(self, pngfile):
        self._graph.layout(prog='dot')
        self._graph.draw(pngfile, prog='dot')

    def addSimpleNode(self, n):
        cnode = {}
        cnode['node']  = n
        cnode['id']  = n.getID()
        cnode['label'] = format_reflbl(n)
        if type(n) is epoct.FinalDiagnosis:
            cnode['shape'] = 'doubleoctagon'
            if n.getSeverity() == "mild":
                cnode['color'] = '#ccffcc'
            elif n.getSeverity() == "moderate":
                cnode['color'] = '#ffff99'
            elif n.getSeverity() == "severe":
                cnode['color'] = '#ff8080'
            else:
                cnode['color'] = lightgray
        elif type(n) is epoct.Question2:
            cnode['shape'] = 'box'
            cnode['color'] = '#bcbd22'
        elif type(n) is epoct.DiagnosisSequence:
            cnode['shape'] = 'octagon'
            cnode['color'] = 'orange'
        elif type(n) is epoct.QuestionSequence:
            cnode['shape'] = 'octagon'
            cnode['color'] = cqs
        else:
            cnode['color'] = lightgray
        self._nodes.append(cnode)

    def addHTMLQANode(self, q, a):
        cnode = {}
        cnode['node']  = q
        cnode['id']  = "struct{}".format(q.getID())
        qlbl = format_reflbl(q)
        max_len = max(10, int(round(len(qlbl)/1.8, 0)))
        if type(q) is epoct.Question:
            cnode['label'] = "<B>" + wrap2_text(qlbl, max_len) + "</B>"
            if q.getCategory() == "background_calculation":
                cnode['bgcolor'] = gray 
            else:
                cnode['bgcolor'] = '#bcbd22'
        elif type(q) is epoct.QuestionSequence:
            qlbl = "<B>" + qlbl + "</B><br />" + q.displaySequenceText()
            cnode['label'] = wrap2_text(qlbl, max_len)
            cnode['bgcolor'] = cqs
        cnode['answers'] = []
        cnode['answer_labels'] = []
        cnode['answer_indices'] = []
        cnode['answer_bgcolors'] = []
        for child in q.getChildren():
            clbl = format_albl(child)
            cnode['answers'].append(child)
            cnode['answer_labels'].append(clbl)
            cnode['answer_indices'].append(child.getID())
            cnode['answer_bgcolors'].append(white)
        if self._horizontal:
            cnode['html_label'] = html_format(cnode['label'], cnode['bgcolor'], cnode['answer_labels'], cnode['answer_indices'], cnode['answer_bgcolors'])
        else:
            cnode['html_label'] = html_format_vert(cnode['label'], cnode['bgcolor'], cnode['answer_labels'], cnode['answer_indices'], cnode['answer_bgcolors'])
        cnode['shape'] = 'plain'
        self.addAnswer(a)
        self._nodes.append(cnode)

    def addParentQuestions(self, n):
        for q, a in zip(n.getGrandParents(), n.getParents()):
            # Exclude management and treatment questions at this stage
            if q.getCategory() not in ["management", "treatment_question"]:
                self.addHTMLQANode(q, a)
                self.addEdge(n, q, a)

    def highlightAnswers(self):
        for n in self.getNodes():
            if type(n['node']) is epoct.Question:
                if n['node'].getCategory() == "background_calculation":
                    asw_color = lightgray
                else:
                    asw_color = '#dbdb8d'
                for a2 in self.getAnswers():
                    if a2.getID() in n['answer_indices']:
                        idx = n['answer_indices'].index(a2.getID())
                        n['answer_bgcolors'][idx] = asw_color
                if self._horizontal: 
                    n['html_label'] = html_format(n['label'], n['bgcolor'], n['answer_labels'], n['answer_indices'], n['answer_bgcolors'])
                else:
                    n['html_label'] = html_format_vert(n['label'], n['bgcolor'], n['answer_labels'], n['answer_indices'], n['answer_bgcolors'])
            elif type(n['node']) is epoct.QuestionSequence:
                for a2 in self.getAnswers():
                    if a2.getID() in n['answer_indices']:
                        idx = n['answer_indices'].index(a2.getID())
                        n['answer_bgcolors'][idx] = cqsa
                if self._horizontal:
                    n['html_label'] = html_format(n['label'], n['bgcolor'], n['answer_labels'], n['answer_indices'], n['answer_bgcolors'])
                else:
                    n['html_label'] = html_format_vert(n['label'], n['bgcolor'], n['answer_labels'], n['answer_indices'], n['answer_bgcolors'])

    def addShortSequence(self, question_seqs):
        self.addParentQuestions(self._root['node'])
        for s in self._root['node'].getSeq():
            if type(s) is epoct.Question:
                self.addParentQuestions(s)
            if type(s) is epoct.QuestionSequence:
                grand_parents, _ = analyse_seq(s, question_seqs)
                for q, a in zip(s.getGrandParents(), s.getParents()):
                    if q.getID() not in grand_parents:
                        self.addHTMLQANode(q, a)
                        self.addEdge(s, q, a)
        self.highlightAnswers()

    def addShortDiagnosis(self):
        for s in self._root['node'].getSeq():
            if type(s) is epoct.Question:
                # Exclude treatment / management branches
                if s.getCategory() not in ["management", "treatment_question"]:
                    self.addParentQuestions(s)
                    for q in self._root['node'].getSeq():
                        if q.getCategory() not in ["management", "treatment_question"]:
                            self.addParentQuestions(s)
                            '''
                            fpp = s.getFormulaParent()
                            if fpp is not None:
                                self.addSimpleNode(fpp)
                                self.addEdge3(fpp, s)
                            '''
            elif type(s) is epoct.QuestionSequence:
                self.addParentQuestions(s)
        self.highlightAnswers()

    def addShortFinalDiagnosis(self):
        self.addParentQuestions(self._root['node'])
        self.highlightAnswers()

    # Draw diagnosis sequence
    def addDiagnosisSequence(self, final_diagnoses):
        self.addShortDiagnosis()
        for fd in final_diagnoses:
            if fd.getMainDiagnosis().getID() == self._root['id']:
                self.addSimpleNode(fd)
                self.addParentQuestions(fd)
                # Add link to excluded diagnosis
                for efd in fd.getExcludedFinalDiagnoses():
                    self.addSimpleNode(efd)
                    self.addEdge4(fd, efd)
            self.highlightAnswers()

    def addDiagnosesPerChiefComplaint(self, cc, main_diagnoses, final_diagnoses):
        for md in main_diagnoses:
            if md.getChiefComplaint().getID() == cc:
                self.setRoot(md)
                self.addDiagnosisSequence(final_diagnoses)

    def addFullSequence(self, question_seqs):
        # Nodes linked with root node
        for q, a in zip(self._root['node'].getGrandParents(), self._root['node'].getParents()):
            self.addHTMLQANode(q, a)
            self.addEdge(self._root['node'], q, a)
        # Loop on the sequence of nodes
        parents = {}
        start_nodes = {}
        for s in self._root['node'].getSeq():
            parents[s.getID()] = []
            start_nodes[s.getID()] = []
            for q, a in zip(s.getGrandParents(), s.getParents()):
                self.addHTMLQANode(q, a)
                if type(s) is epoct.Question:
                    self.addEdge(s, q, a) 
                elif type(s) is epoct.QuestionSequence:
                    pqs, start_nodes[s.getID()] = analyse_seq(s, question_seqs)
                    if q.getID() not in pqs:
                        parents[s.getID()].append((q, a))
        
        for n in self.getNodes():
            if type(n['node']) is epoct.QuestionSequence:
                for n2 in question_seqs:
                    if n2.getID() == n['node'].getID():
                        for q, a in zip(n2.getGrandParents(), n2.getParents()):
                            self.addHTMLQANode(q, a)
                            for a2 in self.getAnswers():
                                if a2.getID() in n['answer_indices']:
                                    self.addEdge2(n2, a2, q, a)
                        for s in n2.getSeq():
                            if s.getID() not in parents:
                                parents[s.getID()] = []
                            for q, a in zip(s.getGrandParents(), s.getParents()):
                                self.addHTMLQANode(q, a)
                                if type(s) is epoct.Question:
                                    self.addEdge(s, q, a)
                                elif type(s) is epoct.QuestionSequence:
                                    pqs, start_nodes[s.getID()] = analyse_seq(s, question_seqs)
                                    if q.getID() not in pqs:
                                        parents[s.getID()].append((q, a))
                if n['node'].getID() in parents:
                    for sn in start_nodes[n['node'].getID()]:
                        for q2, a2 in parents[n['node'].getID()]:
                            self.addEdge(sn, q2, a2)

        self.highlightAnswers()

    def addFullDiagnosis(self, question_seqs):
        for q, a in zip(self._root['node'].getGrandParents(), self._root['node'].getParents()):
            self.addHTMLQANode(q, a)
            self.addEdge(self._root['node'], q, a)
        parents = {}
        start_nodes = {}
        for n in self.getNodes():
            if type(n['node']) is epoct.QuestionSequence:
                for n2 in question_seqs:
                    if n2.getID() == n['node'].getID():
                        for q, a in zip(n2.getGrandParents(), n2.getParents()):
                            self.addHTMLQANode(q, a)
                            for a2 in self.getAnswers():
                                if a2.getID() in n['answer_indices']:
                                    self.addEdge2(n2, a2, q, a)
                        for s in n2.getSeq():
                            if s.getID() not in parents:
                                parents[s.getID()] = []
                            for q, a in zip(s.getGrandParents(), s.getParents()):
                                self.addHTMLQANode(q, a)
                                if type(s) is epoct.Question:
                                    self.addEdge(s, q, a)
                                elif type(s) is epoct.QuestionSequence:
                                    pqs, start_nodes[s.getID()] = analyse_seq(s, question_seqs)
                                    if q.getID() not in pqs:
                                        parents[s.getID()].append((q, a))
                       
                if n['node'].getID() in start_nodes:
                    for sn in start_nodes[n['node'].getID()]:
                        for q2, a2 in parents[n['node'].getID()]:
                            self.addEdge(sn, q2, a2)

        self.highlightAnswers()

    def addEdge(self, n, q, a):
        e = {}
        e["style"] = 'solid'
        e['color'] = 'black'
        e['label'] = q.getScore()
        if type(q) is epoct.Question or type(q) is epoct.QuestionSequence:
            e['id1'] = "struct{}".format(q.getID())
            e['tailport'] = "f{}".format(a.getID())
            e['key'] ="{}.{}".format(e['id1'], e['tailport'])
        else:
            e['id1'] = q.getID()
            e['key'] = "{}".format(e['id1'])
        if n.getID() == self._root['id']:
            e['id2'] = "{}".format(self._root['id'])
        else:
            if type(n) is epoct.Question or type(n) is epoct.QuestionSequence:
                e['id2'] = "struct{}".format(n.getID())
                if self._horizontal:
                    e['headport'] = "e"
                else:
                    e['headport'] = "n"
            else:
                e['id2'] = n.getID()
        e['key'] = e['key']+"-{}".format(e['id2'])
        self._edges.append(e)

    def addEdge2(self, q1, a1, q2, a2):
        e = {}
        e["style"] = 'solid'
        e['color'] = cqs
        e['label'] = q2.getScore()
        e['id1'] = "struct{}".format(q2.getID())
        e['tailport'] = "f{}".format(a2.getID())
        e['key'] ="{}.{}".format(e['id1'], e['tailport'])
        e['id2'] = "struct{}".format(q1.getID())
        e['headport'] = "f{}".format(a1.getID())
        e['key'] = e['key']+"-{}".format(e['id2'], e['headport'])
        self._edges.append(e)

    def addEdge3(self, n, q):
        e = {}
        e["style"] = 'solid'
        e['color'] = 'black'
        e['label'] = ""
        e['id1'] = n.getID()
        e['tailport'] = ""
        e['key'] ="{}.{}".format(e['id1'], e['tailport'])
        e['id2'] = "struct{}".format(q.getID())
        e['headport'] = ""
        e['key'] = e['key']+"-{}".format(e['id2'], e['headport'])
        self._edges.append(e)

    def addEdge4(self, fd, excluded_fd):
        e = {}
        e["style"] = 'dashed'
        e['color'] = 'black'
        e['label'] = "excludes"
        e['id1'] = fd.getID()
        e['tailport'] = ""
        e['key'] ="{}.{}".format(e['id1'], e['tailport'])
        e['id2'] = excluded_fd.getID()
        e['headport'] = ""
        e['key'] = e['key']+"-{}".format(e['id2'], e['headport'])
        self._edges.append(e)

    def addEdges(self, n):
        for q, a in zip(n.getGrandParents(), n.getParents()):
            self.addEdge(n, q, a)

    def createTree(self, n, question_seqs, main_diagnoses, final_diagnoses, outdir, mode):
        self.setRoot(n)
        if mode == "short":
            pngfile = os.path.join(outdir, "{}-short.png".format(n.getReference()))
            if type(n) is epoct.QuestionSequence:
                self.addShortSequence(question_seqs)
            elif type(n) is epoct.DiagnosisSequence:
                self.addShortDiagnosis()
            elif type(n) is epoct.FinalDiagnosis:
                self.addShortFinalDiagnosis()
        elif mode == "full":
            pngfile = os.path.join(outdir, "{}-full.png".format(n.getReference()))
            if type(n) is epoct.QuestionSequence:
                self.addFullSequence(question_seqs)
            elif type(n) is epoct.DiagnosisSequence or type(n) is epoct.FinalDiagnosis:
                self.addFullDiagnosis(question_seqs)
        elif mode == "mdfocus":
            lbl = n.getLabel().replace("/", " - ").replace(":", " - ")
            idx = lbl.find('(')
            if idx>-1:
                lbl = lbl[:idx]
            if type(n) is epoct.DiagnosisSequence:
                pngfile = os.path.join(outdir, "{} {}.png".format(n.getReference(), lbl))
                self.addDiagnosisSequence(final_diagnoses)
            else:
                pngfile = os.path.join(outdir, "{}.png".format(n.getReference()))
                self.addDiagnosesPerChiefComplaint(n.getID(), main_diagnoses, final_diagnoses)
        self.addEdges(n)
        self.draw()
        
        self.export2png(pngfile)

def analyse_seq(s, question_seqs):
    for qs in question_seqs:
        if qs.getID() == s.getID():
            parent_nodes = [gp.getID() for gp in qs.getGrandParents()]
            start_nodes = []
            for n in qs.getSeq():
                if type(n) is epoct.Question:
                    if not n.getGrandParents():
                        start_nodes.append(n)
                elif type(n) is epoct.QuestionSequence:
                    _, sns = analyse_seq(n, question_seqs)
                    for n2 in sns:
                        start_nodes.append(n2)
            return parent_nodes, start_nodes

def plot_nodes(nodes, question_seqs, main_diagnoses, final_diagnoses, outdir, mode="short"):
    
    for n in nodes:
        print("{} - {}".format(n.getID(), n.getReference()))
        g = ClinicalAlgo(horizontal=False)
        g.createTree(n, question_seqs, main_diagnoses, final_diagnoses, outdir, mode)
        del g

def mergeDiagnoses(final_diagnoses_to_test, test_id, question_seqs, main_diagnoses, final_diagnoses, outdir):
    pngfile = os.path.join(outdir, "Test{}.png".format(test_id))
    g = ClinicalAlgo(horizontal=False)
    for n in final_diagnoses_to_test:
        g.setRoot(n)
        g.addDiagnosisSequence(final_diagnoses, question_seqs)
        g.addEdges(n)
    g.draw()
    g.export2png(pngfile)

if __name__ == '__main__':

    # Load category coding
    ctg_code = loadCategoryCoding(CLINICAL_KEYS_PATH, 'category codes')

    # Load diagnosis severity
    severity_df = loadDiagnosisSeverity2(CLINICAL_KEYS_PATH, 'DYNAMIC diagnoses')
    
    # Import data from MedAL-C json file
    algo2 = algoreader.Algo2NodeReader(JSON_PATH, severity_df)

    # Plot question sequences
    mode = "short"
    #plot_nodes(algo2.getQuestionSequenceNodes(), algo2.getQuestionSequenceNodes(), algo2.getDiagnosisSequenceNodes(), algo2.getFinalDiagnosisNodes(), os.path.join(OUTPUT_DIR, "question_sequences2"), mode)
    #mode = "full"
    #plot_nodes(question_seq_nodes, question_seq_nodes, main_diagnosis_nodes, final_diagnosis_nodes, os.path.join(OUTPUT_DIR, "question_sequences"), mode)
    mode = "mdfocus"
    #plot_nodes(main_diagnosis_nodes, question_seq_nodes, main_diagnosis_nodes, final_diagnosis_nodes, os.path.join(OUTPUT_DIR, "diagnoses"), mode)
    plot_nodes(algo2.getDiagnosisSequenceNodes(), algo2.getQuestionSequenceNodes(), algo2.getDiagnosisSequenceNodes(), algo2.getFinalDiagnosisNodes(), os.path.join(OUTPUT_DIR, "diagnoses2"), mode)
    #mode = "short"
    #plot_nodes(final_diagnosis_nodes, question_seq_nodes, main_diagnosis_nodes, final_diagnosis_nodes, os.path.join(OUTPUT_DIR, "final_diagnoses"), mode)