import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


DESCRIPTION = """A tool to manage a database for AWS EC2 instance type offerings.
input source file must be a TSV file with a header line.
"""


def main():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '-i', '--input-file',
        dest='input_file',
        required=True,
        help='input file (tsv with header line)',
    )
    parser.add_argument(
        '-o', '--output-file',
        dest='output_file',
        required=True,
        help='output file (png)',
    )

    args = parser.parse_args()

    df = pd.read_csv(args.input_file, delimiter='\t')

    # Instance family. e.g. m5, c5, etc.
    # Because of too many variations of instance types to plot
    df['InstanceTypeFamily'] = df['InstanceType'].str.split('.').str[0]

    pivot_table = df.pivot_table(
        index="InstanceTypeFamily",
        columns="Location",
        values="ExistsInLocation",
        aggfunc="sum",
    )
    # Normalize by the maximum value in each row
    # This means that each cell will be the ratio of the supported instance types in each row InstanceTypeFamily (=row)
    normalized_pivot_table = pivot_table.apply(lambda x: x / x.max(), axis=1)

    # pivot_table.to_csv('pivot_table.csv')
    # normalized_pivot_table.to_csv('normalized_pivot_table.csv')

    # headmap
    plt.figure(figsize=(12, 20))
    sns.heatmap(normalized_pivot_table, annot=False, cmap="YlGnBu")
    plt.title("Instance Type offerings by InstanceFamily, Location")
    plt.xlabel("Location")
    plt.ylabel("Instance Type Family")
    plt.tight_layout()
    plt.savefig(args.output_file)
    # plt.show()


if __name__ == '__main__':
    main()
