
"""
Your function should have the following attributes for regression:
- Input should be: x_train, x_test, y_train, y_test, func_var
- Output 1 element, which is the MSE. 
    If multiple, return as tuple. First element should be MSE. The other elements can be found using tester.results

Your function should have the following attributes for classification:
- Input should be: x_train, x_test, y_train, y_test, func_var
- Output 1 element, which is f1 score for your predictions using the sklearn.metrics.f1_score
"""

"""
To do:
- [x] Be able to do single level cross validation
- [x] Be able to take in parameter input as list
- [x] Be able to do 2 level cross validation
- [x] When doing 2 level cross validation produce a table with outputs
- [ ] Make it work for classification problem 1
- [ ] Make it work for classification problem 2
"""

# Automatically split data, reserve for validation, run the function on all the folds, return minimum accuracy
# generalization error and best model object

import pandas as pd
from sklearn.model_selection import train_test_split
import torch
from tqdm import tqdm
from prettytable import PrettyTable
import numpy as np
import random

def frust_class(x):
    if int(x) <= 3:
        return 0
    else:
        return 1

def normalize_column(df, columns):
    for column in columns:
        data = df[column]
        min_val = data.min()
        max_val = data.max()
        normalized_column = (data - min_val) / (max_val - min_val)
        df[column] = normalized_column
    return df

def rand_col(df):
    df["rand"] = [random.choice(list(range(1, 15))) for _ in range(len(df))]
    return df

def hr_dev_cols(df):
    labels = {
        "HR_Mean_rel": [],
        "HR_Median_rel": [],
        "HR_std_rel": [],
        "HR_Min_rel": [],
        "HR_Max_rel": [],
        "HR_AUC_rel": []
    }
    for individual in df["Individual"].unique():
        for key, column in zip(labels.keys(), ["HR_Mean", "HR_Median", "HR_std", "HR_Min", "HR_Max", "HR_AUC"]):
            phase1 = df[(df["Individual"] == individual) & (df["Phase"] == "phase1")][column].mean()
            all_values = [(x - phase1) / phase1 for x in df[df["Individual"] == individual][column].values]
            labels[key].extend(all_values)
    for key, value in labels.items(): 
        df[key] = value
    print(df.head(30))
    return df


class Tester():

    def __init__(
        self, 
        function_to_test = None, 
        final_test : bool = False, 
        k : int = 10, 
        vars_to_test = None,
        cross_validation_level : 1 or 2 = 1,
        display_info : bool = True, 
        # Do not use parameters below:
        _predetermined_data : bool = False,
        _data_x = None, 
        _data_y = None,
        _all_data = None,
        _active_tqdm : bool = True,
        _run_tests : bool = True
        ):
        if cross_validation_level == 2 and type(function_to_test) is not list: raise ValueError("You are doing two level cross validation. You should test multiple functions against each other. Please put them in a list.")
        self.func_to_test, self.final_test, self.k, self.cv_lvl = function_to_test, final_test, k, cross_validation_level
        self.display_info, self._predetermined_data, self.data_x, self.data_y, self._active_tqdm, self._all_data, self._run_tests = display_info, _predetermined_data, _data_x, _data_y, _active_tqdm, _all_data, _run_tests
        self.func_vars = [vars_to_test] if type(vars_to_test) is not list else vars_to_test
        self.results = []
        self._set_classification()

    def get_data(self): return self.data_x, self.data_y
    def get_data_folds(self): return self.fold_combs # List of (train_indexes, test_indexes) or (train_indexes, val_indexes, test_indexes), then use data_x[train_indexes], so on
    def get_data_columns(self): return self.x_cols, self.y_col
    def _load_data(self): self.data = pd.read_csv(self.path_to_data); self.columns = list(self.data.columns); self._fix_data(); self._categorize_y_column(); self._add_rel_cols(); self._normalize_x_columns(); self._add_rand_col(); #self._add_data();
    def _add_rel_cols(self): self.data = hr_dev_cols(self.data)
    def _add_rand_col(self): self.data = rand_col(self.data)
    def _normalize_x_columns(self): self.data = normalize_column(self.data, ["HR_Mean", "HR_Median", "HR_std", "HR_Min", "HR_Max", "HR_AUC"])#, "All_6", "All_4"])
    def _categorize_y_column(self): self.data["HighlyFrustrated"] = self.data["Frustrated"].apply(frust_class)
    def _add_data(self): self._all_6(); self._all_4()
    def _all_6(self): self.data["All_6"] = self.data["HR_Mean"] * self.data["HR_Median"] * self.data["HR_std"] * self.data["HR_Min"] * self.data["HR_Max"] * self.data["HR_AUC"] 
    def _all_4(self): self.data["All_4"] = self.data["HR_Mean"] * self.data["HR_std"] * self.data["HR_Max"] * self.data["HR_AUC"] 
    def _reset_index(self): self.data = self.data.reset_index(drop=True)
    def _fix_data(self): self.data = self.data.astype({"Frustrated": str}); self.data = pd.concat([self.data, pd.get_dummies(self.data["Individual"])], axis=1, join="inner") #self.data = self.data[self.data["Cohort"] == "D1_1"]; self._reset_index()
    def _set_data_x(self, x_columns): self.data_x = torch.tensor(self.data[x_columns].values.astype(np.float32()))
    def _set_data_y(self, y_column): self.data_y = torch.tensor(self.data[y_column].values.astype(np.float32))
    def _set_data_props(self): self._set_data_x(self.x_cols); self._set_data_y(self.y_col)
    def _unnest_lst(self, lst): return [item for sublist in lst for item in sublist]
    def _get_fold_combs_without_val(self): self.fold_combs = [(self._unnest_lst(self.data_folds[:i] + self.data_folds[i+1:]), self.data_folds[i]) for i in range(self.k)] # (train, test)
    def _get_fold_combs_with_val(self): self.fold_combs = [(self._unnest_lst(self.data_folds[:i] + self.data_folds[i+2:]), self.data_folds[i+1 if i+1 < self.k else 0], self.data_folds[i]) for i in range(self.k)] # (train, val, test)
    def _set_folds(self): self._set_init_data_folds(); self._get_fold_combs_without_val() if self.final_test else self._get_fold_combs_with_val()
    def _set_best_performer(self): self.best_performer = (self.best_param_func(self.error.keys(), key=lambda x: self.error[x]), self.best_param_func(self.error.values()))
    def _print_best_performer(self): print("".join(["-"]*40), f"\nBest performer is: {self.best_performer[0]}\n", sep="\n")
    def _print_generalization_table(self): print("Func var: |   Generalization error", "".join(["-"]*40), *[f"{k}   \t|    {v}" for k, v in self.error.items()], sep="\n"); self._print_best_performer()
    def _display(self): self._print_generalization_table() if len(self.error) > 1 else print("Generalization error is: ", list(self.error.values())[0])
    def _get_generalization_error(self): self.error = {k: sum(v) / len(v) for k, v in self.accuracies.items()}
    def _fix_results(self): self.accuracies = {k: self._check_results(v) for k, v in self.results.items()}
    def _check_results(self, results): return [float(r[0]) if type(r) in [list, tuple] and len(r) > 1 else r for r in results]
    def _test_folds_and_save_error(self): self._test_all_folds(); self._fix_results(); self._get_generalization_error(); self._set_best_performer(); self._display() if self.display_info else None
    def _test_all_folds(self): 
        self.results = {}
        progress_bar = tqdm(self.func_vars, desc=f"Training and testing all function variables for {self.k} folds...") if self._active_tqdm else self.func_vars
        for func_var in progress_bar:
            self.results[func_var] = [self.func_to_test(self.data_x[fold[0]], self.data_x[fold[1]], self.data_y[fold[0]], self.data_y[fold[1]], func_var) for fold in self.fold_combs]
        return self.results

    def _set_init_data_folds(self): 
        self.data = self._all_data if self._all_data is not None else self.data
        self._reset_index()
        # column_to_split_from = "Individual"
        column_to_split_from = "rand"
        unique_individuals = self.data[column_to_split_from].unique()
        if self.k is None: print(f"You set k to {self.k}, but changing to {len(unique_individuals)} as this is the number of individuals in the dataset, and the cross validation should be base on this")
        self.k = len(unique_individuals)
        self.data_folds = [self.data[self.data[column_to_split_from] == individual].index for individual in unique_individuals]

    def _print_table(self, columns, data):
        table = PrettyTable()
        table.field_names = ["Fold"] + columns
        for i in range(self.k): row_data = [f"{i+1}"] + data[i]; table.add_row(row_data)
        print(table)

    def _get_best_param(self, func, vars_to_test, fold_train_x, fold_train_y, fold_train_indexes):
        return Tester(function_to_test=func,
                final_test=True, vars_to_test=vars_to_test, display_info = False, _predetermined_data = True, _data_x = fold_train_x, 
                _data_y = fold_train_y, _all_data = self.data.loc[fold_train_indexes], _active_tqdm = False, k = self.k).best_performer

    def _two_level_cross_validation(self):
        self.all_results = []
        columns = [v for lst in [[func.__name__, f"Best Param {i}", f"Test Error {i}", f"Val Gen Error {i}"] for i, func in enumerate(self.func_to_test)] for v in lst]
        for fold_train_indexes, fold_test_indexes in tqdm(self.fold_combs, desc="Testing all functions with all parameters on each fold. Please wait..."):
            results_this_fold = []
            fold_train_x, fold_train_y, fold_test_x, fold_test_y = self.data_x[fold_train_indexes], self.data_y[fold_train_indexes], self.data_x[fold_test_indexes], self.data_y[fold_test_indexes]
            for func, vars_to_test in zip(self.func_to_test, self.func_vars):
                best_parameter, best_gen_val_loss = self._get_best_param(func, vars_to_test, fold_train_x, fold_train_y, fold_train_indexes)
                test_error = func(fold_train_x, fold_test_x, fold_train_y, fold_test_y, best_parameter)
                results_this_fold.extend([" ", best_parameter, round(test_error, 6), round(best_gen_val_loss, 6)])
            self.all_results.append(results_this_fold)
        self._print_table(columns, self.all_results)

    def _one_hot_y_col(self): self.data_y = torch.nn.functional.one_hot(self.data_y.long(), num_classes=11).squeeze(1)

    def _set_classification(self):
        self.path_to_data = "Project/HR_data.csv"
        # self.path_to_data = "HR_data.csv"
        self.best_param_func = max
        if not self._predetermined_data:
            self._load_data()
            # self.x_cols = ["HR_Mean", "HR_Median", "HR_std", "HR_Min", "HR_Max", "HR_AUC"]
            self.x_cols = ['HR_Median', 'HR_Max', 'HR_Mean']
            # self.x_cols = ["HR_Mean", "HR_Median", "HR_std", "HR_Min", "HR_Max", "HR_AUC", "All_6", "All_4"]
            # self.x_cols = ["HR_Mean_rel", "HR_Median_rel", "HR_Max_rel"]
            # self.x_cols = ["HR_Min", "All_6", "All_4"]
            self.y_col = ["Puzzler"]
            # self.y_col = ["HighlyFrustrated"]
            # self.y_col = "Frustrated"
            self._set_data_props()
            print(self.data_x)
            self._one_hot_y_col() 
        if self.cv_lvl == 2: self.final_test = True
        self._set_folds()
        if not self._run_tests: return 
        if self._run_tests and self.func_to_test is None: raise ValueError("You have to specify a function to test with func_to_test = ____")
        if self.cv_lvl == 1: self._test_folds_and_save_error()
        if self.cv_lvl == 2: self._two_level_cross_validation()