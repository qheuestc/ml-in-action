#!/usr/bin/env python3
# -*- utf-8 -*-

import numpy as np


def load_data(file_name):
    num_feat = len(open(file_name).readline().split('\t')) - 1
    data_mat = []
    label_mat = []
    with open(file_name) as fr:
        for line in fr.readlines():
            line_arr = []
            cur_line = line.strip().split('\t')
            for i in range(num_feat):
                line_arr.append(float(cur_line[i]))
            data_mat.append(line_arr)
            label_mat.append(float(cur_line[-1]))
    return data_mat, label_mat


def stand_regression(x_arr, y_arr):
    x_mat = np.mat(x_arr)
    y_mat = np.mat(y_arr).T
    xtx = x_mat.T * x_mat
    if np.linalg.det(xtx) == 0.0:
        print('this matrix is singular, cannot do inverse')
        return
    ws = xtx.I * (x_mat.T * y_mat)
    return ws


def plot_std_regression(ws, x, y):
    import matplotlib.pyplot as plt
    x_mat = np.mat(x)
    y_mat = np.mat(y)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(x_mat[:, 1].flatten().A[0], y_mat.T[:, 0].flatten().A[0])
    x_copy = x_mat.copy()
    x_copy.sort(0)
    y_hat = x_copy * ws
    ax.plot(x_copy[:, 1], y_hat)
    plt.show()


def lwlr(test_point, x_arr, y_arr, k=1.0):
    x_mat = np.mat(x_arr)
    y_mat = np.mat(y_arr).T
    m = np.shape(x_mat)[0]
    weights = np.mat(np.eye(m))
    for j in range(m):
        diff_mat = test_point - x_mat[j, :]
        weights[j, j] = np.exp(diff_mat * diff_mat.T / (-2.0 * k ** 2))
    xtx = x_mat.T * (weights * x_mat)
    if np.linalg.det(xtx) == 0.0:
        print('the matrix is singular, cannot do inverse')
        return
    ws = xtx.I * (x_mat.T * (weights * y_mat))
    return test_point * ws


def lwlr_test(test_arr, x_arr, y_arr, k=1.0):
    m = np.shape(x_arr)[0]
    y_hat = np.zeros(m)
    for i in range(m):
        y_hat[i] = lwlr(test_arr[i], x_arr, y_arr, k)
    return y_hat


def plot_lwlr(x_arr, y_arr, k):
    x_mat = np.mat(x_arr)
    y_hat = lwlr_test(x_arr, x_arr, y_arr, k)
    sort_idx = x_mat[:, 1].argsort(0)
    x_sort = x_mat[sort_idx][:, 0, :]
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x_sort[:, 1], y_hat[sort_idx])
    ax.scatter(x_mat[:, 1].flatten().A[0], np.mat(y_arr).T.flatten().A[0], s=2, c='red')
    plt.show()


def rss_error(y_arr, y_hat):
    return ((y_arr - y_hat) ** 2).sum()


def ridge_regression(x_mat, y_mat, lam=0.2):
    xtx = x_mat.T * x_mat
    denom = xtx + np.eye(np.shape(x_mat)[1]) * lam
    if np.linalg.det(denom) == 0.0:
        print('this matrix is singular, cannot do inverse')
        return
    ws = denom.T * (x_mat.T * y_mat)
    return ws


def ridge_test(x_arr, y_arr):
    x_mat = np.mat(x_arr)
    y_mat = np.mat(y_arr).T
    y_mean = np.mean(y_mat, 0)
    y_mat = y_mat - y_mean
    x_means = np.mean(x_mat, 0)
    x_var = np.var(x_mat, 0)
    x_mat = (x_mat - x_means) / x_var
    num_test_pts = 30
    w_mat = np.zeros((num_test_pts, np.shape(x_mat)[1]))
    for i in range(num_test_pts):
        ws = ridge_regression(x_mat, y_mat, np.exp(i - 10))
        w_mat[i, :] = ws.T
    return w_mat


def regularize(x_mat):
    in_mat = x_mat.copy()
    in_mat_mean = np.mean(in_mat, 0)
    in_mat_var = np.var(in_mat, 0)
    in_mat = (in_mat - in_mat_mean) / in_mat_var
    return in_mat


def stage_wise(x_arr, y_arr, eps=0.01, num_iter=100):
    x_mat = np.mat(x_arr)
    y_mat = np.mat(y_arr).T
    y_mean = np.mean(y_mat, 0)
    y_mat = y_mat - y_mean
    x_mat = regularize(x_mat)
    m, n = np.shape(x_mat)
    return_mat = np.zeros((num_iter, n))
    ws = np.zeros((n, 1))
    ws_test = ws.copy()
    ws_max = ws.copy()
    for i in range(num_iter):
        print(ws)
        lowest_err = np.inf
        for j in range(n):
            for sign in [-1, 1]:
                ws_test = ws.copy()
                ws_test[j] += eps * sign
                y_test = x_mat * ws_test
                rss_e = rss_error(y_mat.A, y_test.A)
                if rss_e < lowest_err:
                    lowest_err = rss_e
                    ws_max = ws_test
        ws = ws_max.copy()
        return_mat[i, :] = ws.T

    return return_mat


if __name__ == '__main__':
    pass
