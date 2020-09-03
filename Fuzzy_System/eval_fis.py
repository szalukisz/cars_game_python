import numpy as np

from Fuzzy_System.FuzzySystem import FuzzySystem
from Fuzzy_System.defuzz import defuzz
from Fuzzy_System.trap_mf import trap_mf
from Fuzzy_System.tri_mf import tri_mf


def eval_mf(mf, x):
    if mf.MF_type == 'trimf':
        return tri_mf(x, mf.Param)
    if mf.MF_type == 'trapmf':
        return trap_mf(x, mf.Param)


def eval_fis(fis, user_input, rules_dis=False):
    # _ step 1 : Fuzzify input
    rule_input = fuzzify_input(fis, user_input)

    # _ step 2 : Inference
    inference_output = eval_inference(fis, rule_input)

    # _ step 3 : implication
    num_samples = 21
    implication_output = eval_implication(fis,inference_output,num_samples)

    # _ step 4 : aggregation
    aggregation_output = aggregate(fis, implication_output, num_samples)

    # _ step 5 : defuzzy
    if rules_dis:
        return defuzzy_out(fis, aggregation_output, num_samples), inference_output
    else:
        return defuzzy_out(fis, aggregation_output, num_samples)



def fuzzify_input(fis, user_input):
    num_rules = len(fis.Rules)
    num_inputs = len(fis.Inputs)
    rule_input = np.zeros((num_rules, num_inputs))

    for i in range(num_rules):
        antecedent = fis.Rules[i].Antecedent
        for j in range(num_inputs):
            crisp_x = user_input[j]

            mf_index = antecedent[j]
            mf = fis.Inputs[j].MFs[mf_index]
            mu = eval_mf(mf, crisp_x)

            rule_input[i, j] = mu

    return rule_input


def eval_inference(fis, rule_input):
    num_rules = len(fis.Rules)
    num_inputs = len(fis.Inputs)
    inference_output = np.zeros(num_rules)
    for i in range(num_rules):
        rule = fis.Rules[i]
        antecedent_mus = []
        for j in range(num_inputs):
            if rule.Antecedent[j] >= 0:
                mu = rule_input[i, j]
                antecedent_mus.append(mu)

        if rule.Connection == 1:  # 1 == AND
            inference_output[i] = min(antecedent_mus)
        else:                     # 0 == OR
            inference_output[i] = max(antecedent_mus)
    return inference_output


def eval_implication(fis, inference_output, num_samples):
    num_output = len(fis.Outputs)
    num_rules = len(fis.Rules)

    implication_output = np.zeros((num_samples, num_rules*num_output))

    for i in range(num_output):
        begin = fis.Outputs[i].Range[0]
        end = fis.Outputs[i].Range[1]
        for j in range(num_rules):
            for s in range(num_samples):
                crisp_x = begin + (end-begin)/num_samples*s

                rule = fis.Rules[j]

                mf_index = rule.Consequent[i]

                height = inference_output[j]

                mf = fis.Outputs[i].MFs[mf_index]

                mu = eval_mf(mf, crisp_x)

                implication_output[s][i*num_rules+j] = min(height, mu)

    return implication_output


def aggregate(fis, implication_output, num_samples):
    num_output = len(fis.Outputs)
    num_rules = len(fis.Rules)

    aggregate_output = np.zeros((num_samples,num_output))
    for j in range(num_output):

        for i in range(num_samples):
            base = j*num_rules
            tab = np.zeros(num_rules)
            for r in range(num_rules):
                tab[r] = implication_output[i][base+r]

            aggregate_output[i][j] = max(tab)
    return aggregate_output


def defuzzy_out(fis, aggregate_output, num_samples):
    num_outputs = len(fis.Outputs)
    output = np.zeros(num_outputs)

    for i in range(num_outputs):
        begin = fis.Outputs[i].Range[0]
        end = fis.Outputs[i].Range[1]
        x = np.linspace(begin, end, num_samples)
        y = aggregate_output[:, i]
        output[i] = defuzz(x, y, fis.def_method)
    return output
