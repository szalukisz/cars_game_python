import numpy as np

from Fuzzy_System.mf import mf
from Fuzzy_System.fis_var import fis_var
from Fuzzy_System.rule import rule


class FuzzySystem:
    def __init__(self, name='fis', def_method='centroid'):
        self.Name = name
        self.def_method = def_method

        self.Inputs = []
        self.Outputs = []
        self.Rules = []

    def addInput(self, _range, Name):
        new_var = fis_var(Name, _range)
        self.Inputs.append(new_var)

    def addOutput(self, _range, Name):
        new_var = fis_var(Name, _range)
        self.Outputs.append(new_var)

    def addRule(self, rules):
        for rule_def in rules:
            new_rule = rule(rule_def, len(self.Inputs))
            self.Rules.append(new_rule)

    def addMF(self, var_name, mf_type, param, Name):
        names = [inp.Name for inp in self.Inputs+self.Outputs]
        index = names.index(var_name)

        new_mf = mf(mf_type, param, Name)
        if index < len(self.Inputs):
            self.Inputs[index].MFs.append(new_mf)
        else:
            self.Outputs[index-len(self.Inputs)].MFs.append(new_mf)
