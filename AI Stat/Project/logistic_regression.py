from automation import Tester
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def LogReg(x_train, x_test, y_train, y_test, func_var):

    y_test = np.argmax(y_test, axis=1)
    y_train = np.argmax(y_train, axis=1)

    logistic_regression_model = LogisticRegression(C=1/func_var, max_iter=5000)
    logistic_regression_model.fit(x_train, y_train)
    y_test_est = logistic_regression_model.predict(x_test).T

    acc = accuracy_score(y_test, y_test_est)
    return acc
  

if __name__ == "__main__":
    path_to_data = "/Users/lucasvilsen/Desktop/DTU/MachineLearning&DataMining/Project2/StandardizedDataFrameWithNansFilled.csv"
    lambda_to_test = [0.1, 1, 10, 100]
    # h_to_test = 8
    print(lambda_to_test)
    tester = Tester(function_to_test = LogReg, final_test = False, k = 14, vars_to_test=lambda_to_test)