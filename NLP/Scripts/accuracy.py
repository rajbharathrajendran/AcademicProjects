import sys


def get_info_to_analyze(lines):
    to_analyze = []
    for line in lines:
        cols = line.split("\t")
        if len(cols) == 1:
            continue
        # Word, POS, Actual, Output
        to_analyze.append([cols[0], cols[1], cols[-2], cols[-1]])
    return to_analyze


def analyze(to_analyze):
    report = {"Z": {"correct": 0, "total": 0}, "NZ": {"correct": 0, "total": 0}, "total": 0}
    for token in to_analyze:
        word = token[0]
        pos = token[1]
        actual = token[2]
        output = token[3]

        report["total"] += 1

        if actual == "0":
            report["Z"]["total"] += 1
            if actual == output:
                report["Z"]["correct"] += 1
        else:
            report["NZ"]["total"] += 1

            if actual not in report:
                report[actual] = {"correct": 0, "total": 0, "incorrect": {}}

            report[actual]["total"] += 1

            if actual == output:
                report["NZ"]["correct"] += 1
                report[actual]["correct"] += 1
            else:
                if output not in report[actual]["incorrect"]:
                    report[actual]["incorrect"][output] = 0
                report[actual]["incorrect"][output] += 1
    return report


def display_table(report):
    print "Total Words: ", report["total"]

    print "\tCorrect\tTotal\tPercentage"
    cls = "NZ"
    print "Named Entity", "\t", report[cls]["correct"],"\t", report[cls]["total"],"\t", (report[cls]["correct"] * 1.0)/report[cls]["total"]
    cls = "Z"
    print "Non Named", "\t", report[cls]["correct"],"\t", report[cls]["total"],"\t", (report[cls]["correct"] * 1.0)/report[cls]["total"]
    print "\n"
    report.pop("total")
    report.pop("Z")
    report.pop("NZ")
    for cls in report:
        print cls, "\t", report[cls]["correct"],"\t", report[cls]["total"],"\t", (report[cls]["correct"] * 1.0)/report[cls]["total"]


def main():
    name = sys.argv[1]
    with open(name) as f:
        lines = f.read().splitlines()

    to_analyze = get_info_to_analyze(lines)
    report = analyze(to_analyze)
    display_table(report)


main()