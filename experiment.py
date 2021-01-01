import json

import numpy as np
import argparse
import sys

def main(path, N):
    a = np.random.rand(N,2)
    np.savetxt(path+"/result.csv", a, delimiter=",")

if __name__ == "__main__":

    #parser = argparse.ArgumentParser(description='Save list of random 2D vectors in specified location ')
    #parser.add_argument('N', metavar='N', type=int,
    #                                        help='Number of numbers')
    
    #parser.add_argument("hparameters", type=str, help="Experiment hyper-parameters")
    #parser.add_argument('--dest', dest='path',
    #                    default="./",
    #                    help='Destination of the result file')

    #args = parser.parse_args()
    #print("The value of N is:", args.N)
    #print(args.path)
    
    obj = json.loads(" ".join(sys.argv[1:]))
    print("Value of N is", obj["N"])

    main(args.path, obj["N"])
                
