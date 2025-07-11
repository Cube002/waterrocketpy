import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import torch

def test_packages():
    print("Numpy version:", np.__version__)
    print("Pandas version:", pd.__version__)
    
    # Simple linear regression test
    X = np.array([[1], [2], [3], [4], [5]])
    y = np.array([2, 4, 5, 4, 5])
    model = LinearRegression().fit(X, y)
    print("LinearRegression score:", model.score(X, y))
    
    # Plot a simple graph
    plt.plot(X.flatten(), y)
    plt.title("Test Plot")
    plt.show()
    
    # Torch tensor test
    x = torch.tensor([1.0, 2.0, 3.0])
    print("Torch tensor:", x)

if __name__ == "__main__":
    test_packages()
