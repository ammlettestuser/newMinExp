import numpy as np
import argparse
import seaborn as sns
import matplotlib.pyplot as plt

def main(path):
    csv_path = "result.csv" if path == "./" else path + "/result.csv"
    a = np.loadtxt(csv_path, delimiter=",")

    sns.scatterplot(data=a)
    png_name = "result.png" if path == "./" else path + "/result.png"
    
    plt.savefig(png_name)
            
    
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Load list of random 2D vectors and print it')
    parser.add_argument('--source', dest='path',
                        default="./",
                        help='Location of the result file')

    args = parser.parse_args()
    print(args.path)
    
    main(args.path)
                
