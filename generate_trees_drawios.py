from graphviz2drawio import graphviz2drawio

import os
from pygraphviz import *
from copy import deepcopy
from read_epoct_json2 import extract_nodes
from epoct import Diagnosis, FinalDiagnosis, Question, QuestionSequence, Answer

lightgray = "#D3D3D3"
gray = "#808080"
white = "#FFFFFF"
cqs = "#40e0d0"
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

def format_label(n):
    max_len = 20
    if type(n) is QuestionSequence:
        lbl = "{}. {}".format(n.getID(), n.getCategory().replace("_"," "))
    else:
        conv = dict()
        conv["/"] = "-"
        lbl = n.getLabel()
        for k, s in zip(conv.keys(), conv.values()):
            lbl = lbl.replace(k, s)
        idx = lbl.find('(')
        if idx>-1:
            lbl = lbl[:idx]
        lbl = "{}. {}".format(n.getID(), lbl)
        
    lbl = wrap_text(lbl, max_len)
    return lbl

def format_4_filename(n):
    max_len = 25
    if type(n) is QuestionSequence:
        lbl = "{}. {}".format(n.getID(), n.getCategory())
    else:
        conv = dict()
        conv["/"] = "_"
        conv[" "] = "_"
        lbl = n.getLabel()
        for k, s in zip(conv.keys(), conv.values()):
            lbl = lbl.replace(k, s)
        idx = lbl.find('(')
        if idx>-1:
            lbl = lbl[:idx]
        if len(lbl)>max_len:
            lbl = lbl[:max_len]
    
    return lbl

###################
# ClinicalAlgo class
###################

class ClinicalAlgo():

    def __init__(self):
        self._graph = AGraph(strict=True)
        self._graph.graph_attr['rankdir'] = 'LR'
        self._graph.graph_attr['splines'] = 'spline'
        self._root    = {}
        self._nodes   = []
        self._edges   = []
        self._answers = []
    
    def setRoot(self, r):
        self._root['node'] = r
        self._root['id'] = r.getID()
        self._root['label'] = format_label(r)
        self._root['shape'] = 'doubleoctagon'
        if type(r) is FinalDiagnosis:
            if "severe" in r.getLabel().lower() or "major" in r.getLabel().lower(): 
                self._root['color'] = cfd
            else:
                if "minor" in r.getLabel().lower() or "uncomplicated" in r.getLabel().lower() or "mild" in r.getLabel().lower(): 
                    self._root['color'] = "green"
                else: 
                    self._root['color'] = "yellow"
        elif type(r) is Diagnosis:
            self._root['color'] = cmd
        elif type(r) is QuestionSequence:
            self._root['color'] = cqs
        else:
            self._root['color'] = lightgray
        self._graph.add_node(self._root['id'], label=self._root['label'], shape=self._root['shape'], fillcolor=self._root['color'], style="filled")

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

    def draw_edges(self):
        for e in self._edges:
            if 'style' in e.keys():
                self._graph.add_edge(e['id1'], e['id2'], style=e['style'])
            else:
                self._graph.add_edge(e['id1'], e['id2'])
    
    def export2png(self, pngfile):
        self._graph.layout(prog='dot')
        self._graph.draw(pngfile, prog='dot')

    def addSimpleNode(self, n):
        cnode = {}
        cnode['node']  = n
        cnode['id']  = n.getID()
        cnode['label'] = format_label(n)
        cnode['shape'] = 'octagon'
        if type(n) is FinalDiagnosis:
            if "severe" in n.getLabel().lower() or "major" in n.getLabel().lower(): 
                cnode['color'] = cfd
            else:
                if "minor" in n.getLabel().lower() or "uncomplicated" in n.getLabel().lower() or "mild" in n.getLabel().lower(): 
                    cnode['color'] = "green"
                else: 
                    cnode['color'] = "yellow"
        elif type(n) is Diagnosis:
            cnode['color'] = 'orange'
        elif type(n) is QuestionSequence:
            cnode['color'] = cqs
        else:
            cnode['color'] = lightgray
        self._nodes.append(cnode)
        self._graph.add_node(cnode['id'], label=cnode['label'], shape=cnode['shape'], fillcolor=cnode['color'], style="filled")

    def addQANodes(self, q, a):
        cnode = {}
        cnode['node']  = q
        cnode['id']  = "{}".format(q.getID())
        qlbl = format_label(q)
        max_len = max(10, int(round(len(qlbl)/1.8, 0)))
        cnode['label'] = wrap_text(qlbl, max_len)
        cnode['color'] = gray
        cnode['shape'] = "box"
        self._nodes.append(cnode)
        self._graph.add_node(cnode['id'], label=cnode['label'], shape=cnode['shape'], fillcolor=cnode['color'], style="filled")
        for child in q.getChildren():
            cnode = {}
            cnode['node'] = child
            cnode['id']  = "a{}".format(child.getID())
            clbl = format_label(child)
            cnode['label'] = clbl
            cnode['color'] = white
            cnode['shape'] = "ellipse"
            self._nodes.append(cnode)
            self._graph.add_node(cnode['id'], label=cnode['label'], shape=cnode['shape'], fillcolor=cnode['color'], style="filled")
            self.addEdge(q, child)
        self.addAnswer(a)

    def highlightAnswers(self):
        for n in self.getNodes():
            if type(n['node']) is Answer:
                for a2 in self.getAnswers():
                    if a2.getID() == n['node'].getID():
                        n['color'] = lightgray
                        self._graph.add_node(n['id'], label=n['label'], shape=n['shape'], fillcolor=n['color'], style="filled")       
                
    def addShortSequence(self, question_seqs):
        for q, a in zip(self._root['node'].getGrandParents(), self._root['node'].getParents()):
            if type(q) is Question:
                self.addQANodes(q, a)
                self.addEdge(a, self._root['node'])
            elif type(q) is QuestionSequence:
                self.addSimpleNode(q)
                self.addEdge(q, self._root['node'])
        for s in self._root['node'].getSeq():
            if type(s) is Question:
                for q, a in zip(s.getGrandParents(), s.getParents()):
                    if type(q) is Question:
                        self.addQANodes(q, a)
                        self.addEdge(a, s)
                    elif type(q) is QuestionSequence:
                        self.addSimpleNode(q)
                        self.addEdge(q, s)
            if type(s) is QuestionSequence:
                grand_parents, _ = analyse_seq(s, question_seqs)
                for q, a in zip(s.getGrandParents(), s.getParents()):
                    if q.getID() not in grand_parents:
                        if type(q) is Question:
                            self.addQANodes(q, a)
                            self.addEdge(a, s)
                        elif type(q) is QuestionSequence:
                            self.addSimpleNode(q)
                            self.addEdge(q, s)
        self.highlightAnswers()

    def addShortDiagnosis(self):
        for q, a in zip(self._root['node'].getGrandParents(), self._root['node'].getParents()):
            if type(q) is Question:
                self.addQANodes(q, a)
                self.addEdge(a, self._root['node'])
            else:
                self.addSimpleNode(q)
                self.addEdge(q, self._root['node'])

        self.highlightAnswers()

    # Draw diagnosis
    def addFinalDiagnosesPerMainDiagnosis(self, final_diagnoses):
        self.addShortDiagnosis()
        for fd in final_diagnoses:
            if fd.getMainDiagnosis().getID() == self._root['id']:
                self.addSimpleNode(fd)
                for q, a in zip(fd.getGrandParents(), fd.getParents()):
                    if type(q) is Question:
                        self.addQANodes(q, a)
                        self.addEdge(a, fd)
                    else:
                        self.addSimpleNode(q)
                        self.addEdge(q, fd)
                    self.addEdge(self._root['node'], q)
        
        self.highlightAnswers()

    def addDiagnosesPerChiefComplaint(self, main_diagnoses):
        for md in main_diagnoses:
            if md.getChiefComplaint().getID() == self._root['id']:
                self.addSimpleNode(md)
                for q, a in zip(md.getGrandParents(), md.getParents()):
                    if type(q) is Question:
                        self.addQANodes(q, a)
                        self.addEdge(q, md)
                    else:
                        self.addSimpleNode(q)
                        self.addEdge(a, md)
                self.highlightAnswers()

    def addFullSequence(self, question_seqs):
        # Nodes linked with root node
        for q, a in zip(self._root['node'].getGrandParents(), self._root['node'].getParents()):
            if type(q) is Question:
                self.addQANodes(q, a)
                self.addEdge(a, self._root['node'])
            elif type(q) is QuestionSequence:
                self.addSimpleNode(q)
                self.addEdge(q, self._root['node'])
        # Loop on the sequence of nodes
        parents = {}
        start_nodes = {}
        for s in self._root['node'].getSeq():
            parents[s.getID()] = []
            start_nodes[s.getID()] = []
            for q, a in zip(s.getGrandParents(), s.getParents()):
                if type(q) is Question:
                    self.addQANodes(q, a)
                elif type(q) is QuestionSequence:
                    self.addSimpleNode(q)
                if type(s) is Question:
                    self.addEdge(s, a) 
                elif type(s) is QuestionSequence:
                    pqs, start_nodes[s.getID()] = analyse_seq(s, question_seqs)
                    if q.getID() not in pqs:
                        parents[s.getID()].append((q, a))
        
        for n in self.getNodes():
            if type(n['node']) is QuestionSequence:
                for n2 in question_seqs:
                    if n2.getID() == n['node'].getID():
                        for q, a in zip(n2.getGrandParents(), n2.getParents()):
                            if type(q) is Question:
                                self.addQANodes(q, a)
                            elif type(q) is QuestionSequence:
                                self.addSimpleNode(q)
                            self.addEdge(n2, a)
                        for s in n2.getSeq():
                            if s.getID() not in parents:
                                parents[s.getID()] = []
                            for q, a in zip(s.getGrandParents(), s.getParents()):
                                if type(q) is Question:
                                    self.addQANodes(q, a)
                                elif type(q) is QuestionSequence:
                                    self.addSimpleNode(q)
                                if type(s) is Question:
                                    self.addEdge(s, a)
                                elif type(s) is QuestionSequence:
                                    pqs, start_nodes[s.getID()] = analyse_seq(s, question_seqs)
                                    if q.getID() not in pqs:
                                        parents[s.getID()].append((q, a))
                if n['id'] in parents:
                    for sn in start_nodes[n['id']]:
                        for q2, a2 in parents[n['id']]:
                            self.addEdge(sn, a2)

        self.highlightAnswers()

    def addFullDiagnosis(self, question_seqs):
        for q, a in zip(self._root['node'].getGrandParents(), self._root['node'].getParents()):
            if type(q) is Question:
                self.addQANodes(q, a)
            else:
                self.addSimpleNode(q)
            self.addEdge(self._root['node'], a)
        parents = {}
        start_nodes = {}
        for n in self.getNodes():
            if type(n['node']) is QuestionSequence:
                for n2 in question_seqs:
                    if n2.getID() == n['node'].getID():
                        for q, a in zip(n2.getGrandParents(), n2.getParents()):
                            if type(q) is Question:
                                self.addQANodes(q, a)
                            elif type(q) is QuestionSequence:
                                self.addSimpleNode(q)
                            self.addEdge(n2, a)
                        for s in n2.getSeq():
                            if s.getID() not in parents:
                                parents[s.getID()] = []
                            for q, a in zip(s.getGrandParents(), s.getParents()):
                                if type(q) is Question:
                                    self.addQANodes(q, a)
                                elif type(q) is QuestionSequence:
                                    self.addSimpleNode(q)
                                if type(s) is Question:
                                    self.addEdge(s, a)
                                elif type(s) is QuestionSequence:
                                    pqs, start_nodes[s.getID()] = analyse_seq(s, question_seqs)
                                    if q.getID() not in pqs:
                                        parents[s.getID()].append((q, a))
                       
                if n['id'] in start_nodes:
                    for sn in start_nodes[n['id']]:
                        for q2, a2 in parents[n['id']]:
                            self.addEdge(sn, a2)

        self.highlightAnswers()

    def addEdge(self, n1, n2):
        e = {}
        if type(n1) is Answer:
            e['id1'] = "a{}".format(n1.getID())
        else:
            e['id1'] = n1.getID()
        if type(n2) is Answer:
            e['id2'] = "a{}".format(n2.getID())
        else:
            e['id2'] = n2.getID()
        self._edges.append(e)

    def addEdges(self, n):
        for q, a in zip(n.getGrandParents(), n.getParents()):
            self.addEdge(n, a)

    def createTree(self, n, question_seqs, main_diagnoses, final_diagnoses, outdir, mode):
        self.setRoot(n)
        if mode == "short":
            pngfile = os.path.join(outdir, "node{0:03d}-short2.png".format(n.getID()))
            if type(n) is QuestionSequence:
                self.addShortSequence(question_seqs)
            elif type(n) is Diagnosis:
                self.addShortDiagnosis()
            elif type(n) is FinalDiagnosis:
                self.addShortDiagnosis()
        elif mode == "full":
            pngfile = os.path.join(outdir, "node{0:03d}-full2.png".format(n.getID()))
            if type(n) is QuestionSequence:
                self.addFullSequence(question_seqs)
            elif type(n) is Diagnosis or type(n) is FinalDiagnosis:
                self.addFullDiagnosis(question_seqs)
        elif mode == "mdfocus":
            if type(n) is Diagnosis:
                pngfile = os.path.join(outdir, "node{0:03d}-{1}-mdfocus2.png".format(n.getID(), format_4_filename(n)))
                self.addFinalDiagnosesPerMainDiagnosis(final_diagnoses)
            else:
                pngfile = os.path.join(outdir, "node{0:03d}-{1}-ccfocus2.png".format(n.getID(), format_4_filename(n)))
                self.addDiagnosesPerChiefComplaint(main_diagnoses)
        self.draw_edges()
        self.export2png(pngfile)
        self.convert2drawio(pngfile.replace('png', 'xml'))

    def convert2drawio(self, outfile):

        xml = graphviz2drawio.convert(self._graph)
        with open(outfile, 'w', encoding="utf8") as f:
            f.write(xml)

def analyse_seq(s, question_seqs):
    for qs in question_seqs:
        if qs.getID() == s.getID():
            parent_nodes = [gp.getID() for gp in qs.getGrandParents()]
            start_nodes = []
            for n in qs.getSeq():
                if type(n) is Question:
                    if not n.getGrandParents():
                        start_nodes.append(n)
                elif type(n) is QuestionSequence:
                    _, sns = analyse_seq(n, question_seqs)
                    for n2 in sns:
                        start_nodes.append(n2)
            return parent_nodes, start_nodes

def plot_nodes(nodes, question_seqs, main_diagnoses, final_diagnoses, outdir, mode="short"):
    
    for n in nodes:
        print("{}".format(n.getID()))
        g = ClinicalAlgo()
        g.createTree(n, question_seqs, main_diagnoses, final_diagnoses, outdir, mode)
        del g

if __name__ == '__main__':

    import json
    import os

    json_path = r'C:\Users\langhe\switchdrive\Private\Unisanté\epoct_variables.json'
    outdir = r'C:\Users\langhe\switchdrive\Private\Unisanté\epoct_variables'
    
    # Load data from json file
    with open(json_path, encoding='utf8') as f:
        data = json.load(f)

    # Extract node structure
    main_diagnosis_nodes, final_diagnosis_nodes, cc_nodes, question_seq_nodes = extract_nodes(data)

    # Plot question sequences
    mode = "mdfocus"
    #plot_nodes(question_seq_nodes, question_seq_nodes, main_diagnosis_nodes, final_diagnosis_nodes, os.path.join(outdir, "question_sequences"), mode)
    plot_nodes(main_diagnosis_nodes, question_seq_nodes, main_diagnosis_nodes, final_diagnosis_nodes, os.path.join(outdir, "main_diagnoses"), mode)
    #plot_nodes(final_diagnosis_nodes, question_seq_nodes, main_diagnosis_nodes, final_diagnosis_nodes, os.path.join(outdir, "final_diagnoses"), mode)
    #plot_nodes(cc_nodes, question_seq_nodes, main_diagnosis_nodes, final_diagnosis_nodes, os.path.join(outdir, "cc"), mode)