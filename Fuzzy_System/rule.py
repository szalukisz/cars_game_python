class rule:
    def __init__(self, rule, numInputs):
        self.Antecedent = rule[:numInputs]
        self.Consequent = rule[numInputs:-1]
        # self.Weight = rule[-2]
        self.Connection = rule[-1]
