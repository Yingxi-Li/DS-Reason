#!/usr/bin/env python3
import os
import random
import argparse
import ast
import json

from evaluation.eval import translate, predict, log
from evaluation.batch_eval import get_batch_results
from evaluation.utils import parse_arguments

from natural.graph.schema import GraphSchema, GraphSchemaAnsOnly

def main():
    args = parse_arguments()
    args.type = "graph"
    args.operation = "natural"

    # locate files relative to this script
    base_dir     = os.path.dirname(__file__)
    natural_path = os.path.join(base_dir, "natural.txt")
    desc_path    = os.path.join(base_dir, "template", "description.txt")
    node_path    = os.path.join(base_dir, "template", "node.txt")
    edge_path    = os.path.join(base_dir, "template", "edge.txt")

    # read and parse each graph‐instance block
    raw_blocks = open(natural_path).read().strip().split("\n\n")
    instances = []
    for block in raw_blocks:
        data = {}
        for line in block.splitlines():
            key, val = line.split(": ", 1)
            if key in ("nodes", "edges", "amenities", "required_amenities", "dfs_path"):
                data[key] = ast.literal_eval(val)
            elif key in ("source", "target"):
                data[key] = val
        instances.append(data)

    # load description + node/edge templates
    descriptions = [l.strip() for l in open(desc_path) if l.strip()]
    node_tmpls   = [l.strip() for l in open(node_path) if l.strip()]
    edge_tmpls   = [l.strip() for l in open(edge_path) if l.strip()]

    truths = []
    Q_list = []

    for inst in instances:
        nodes     = inst["nodes"]
        edges     = inst["edges"]
        amenities = inst["amenities"]
        req_ams   = inst["required_amenities"]
        source    = inst["source"]
        target    = inst["target"]

        # 1) high-level description
        desc = random.choice(descriptions)
        Q = desc + "\n\n"

        # 2) node descriptions
        all_ams = sorted({a for lst in amenities.values() for a in lst})
        for p in nodes:
            tmpl = random.choice(node_tmpls)
            text = tmpl.replace("{planet}", p)
            # amenity_list
            alist = amenities[p]
            text = text.replace("{amenity_list}", ", ".join(alist))
            # non_amenity_list
            non_list = [a for a in all_ams if a not in alist]
            text = text.replace("{non_amenity_list}", ", ".join(non_list))
            # other_planet
            other = random.choice([x for x in nodes if x != p])
            text = text.replace("{other_planet}", other)
            Q += text + "\n"
        Q += "\n"

        # 3) edge descriptions
        for u, v in edges:
            tmpl = random.choice(edge_tmpls)
            text = tmpl.replace("{planet1}", u).replace("{planet2}", v)
            other = random.choice([x for x in nodes if x not in (u, v)])
            text = text.replace("{other_planet}", other)
            Q += text + "\n"
        Q += "\n"

        # 4) final question using the provided target
        req_str = ", ".join(req_ams)
        Q += (
            f"Q: What is the DFS path (a list of planet names) that the Star Courier takes, "
            f"starting from {source} and ending at {target}, "
            f"such that for each amenity in {req_str}, the path includes at least one planet offering that amenity? \n" 
        )

        # translate/format prompt
        Q_list.append(translate(Q, desc, args))
        truths.append(inst["dfs_path"])


    # run prediction/evaluation
    schema = GraphSchemaAnsOnly if args.prompt == "AnsOnly" else GraphSchema
    if args.batch:
        answers = get_batch_results(Q_list, args, schema)
    else:
        if args.format == "schema":
            answers = predict(Q_list, args, schema)
        else:
            raise Exception("Invalid format type.")

    # compare against truths
    res = []
    for idx, ans_text in enumerate(answers):
        try:
            js  = json.loads(ans_text)
            ans = js["final_answer"]
        except Exception as e:
            print(f"Parse error at {idx}: {e}")
            res.append(0)
            continue

        # normalize both to lists
        if isinstance(ans, list):
            ans_list = ans
        else:
            ans_list = ast.literal_eval(ans)
        truth_list = truths[idx]

        if ans_list == truth_list:
            res.append(1)
        else:
            res.append(0)
            print(f"Answer[{idx}]: {ans_list}")
            print(f"Truth [{idx}]: {truth_list}")

    log(Q_list, res, answers, args)

if __name__ == "__main__":
    main()
