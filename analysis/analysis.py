import numpy as np
import argparse
import seaborn as sns
import matplotlib.pyplot as plt

def main(path):
    a = np.loadtxt(path+"/result.csv", delimiter=",")

    sns.scatterplot(data=a)
    png_name = path+"/result.png"
    plt.savefig(png_name)
            
    
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Load list of random 2D vectors and print it')
    parser.add_argument('--source', dest='path',
                        default="./",
                        help='Location of the result file')

    args = parser.parse_args()
    print(args.path)
    
    main(args.path)
                
