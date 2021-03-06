#!/usr/bin/env python3
# -*- utf-8 -*-

import numpy as np


def load_data(file_name):
    data_mat = []
    label_mat = []
    with open(file_name) as fr:
        for line in fr.readlines():
            line_arr = line.strip().split('\t')
            data_mat.append([float(line_arr[0]), float(line_arr[1])])
            label_mat.append(float(line_arr[-1]))
    return data_mat, label_mat


def select_j_rand(i, m):
    # 随机选取j
    j = i
    while j == i:  # 直到j和i不同
        j = int(np.random.uniform(0, m))
    return j


def clip_alpha(a_j, h, l):
    # 对于超出范围的aj进行截断
    if a_j > h:
        a_j = h
    if a_j < l:
        a_j = l
    return a_j


def smo_simple(data_mat, class_mat, c, toler, max_iter):
    data_matrix = np.mat(data_mat)
    label_mat = np.mat(class_mat).transpose()
    b = 0
    m, n = np.shape(data_matrix)
    alphas = np.zeros((m, 1))
    iteration = 0
    while iteration < max_iter:
        alpha_pairs_changed = 0
        for i in range(m):
            f_xi = float(np.multiply(alphas, label_mat).T * (data_matrix * data_matrix[i, :].T)) + b
            e_i = f_xi - float(label_mat[i])
            # 选择第一个需要优化的 α
            if (label_mat[i] * e_i < -toler and alphas[i] < c) or (label_mat[i] * e_i > toler and alphas[i] > 0):
                # 随机选择第二个需要优化的 α
                j = select_j_rand(i, m)
                f_xj = float(np.multiply(alphas, label_mat).T * (data_matrix * data_matrix[j, :].T)) + b
                e_j = f_xj - float(label_mat[j])
                alpha_i_old = alphas[i].copy()
                alpha_j_old = alphas[j].copy()
                if label_mat[i] != label_mat[j]:
                    low = max(0, alphas[j] - alphas[i])
                    high = min(c, c + alphas[j] - alphas[i])
                else:
                    low = max(0, alphas[j] + alphas[i] - c)
                    high = min(c, alphas[j] + alphas[i])
                if low == high:
                    print('low == high')
                    continue
                eta = 2.0 * data_matrix[i, :] * data_matrix[j, :].T - data_matrix[i, :] * data_matrix[i, :].T - \
                      data_matrix[j, :] * data_matrix[j, :].T
                if eta >= 0:
                    print('eta >= 0')
                    continue
                alphas[j] = alphas[j] - label_mat[j] * (e_i - e_j) / eta
                alphas[j] = clip_alpha(alphas[j], high, low)
                if abs(alphas[j] - alpha_j_old < 1e-5):
                    print('j not moving enough')
                    continue
                alphas[i] = alphas[i] + label_mat[j] * label_mat[i] * (alpha_j_old - alphas[j])
                b1 = b - e_i - label_mat[i] * (alphas[i] - alpha_i_old) * data_matrix[i, :] * data_matrix[i, :].T - \
                     label_mat[j] * (alphas[j] - alpha_j_old) * data_matrix[i, :] * data_matrix[j, :].T
                b2 = b - e_j - label_mat[i] * (alphas[i] - alpha_i_old) * data_matrix[i, :] * data_matrix[j, :].T - \
                     label_mat[j] * (alphas[j] - alpha_j_old) * data_matrix[j, :] * data_matrix[j, :].T
                if 0 < alphas[i] < c:
                    b = b1
                elif 0 < alphas[j] < c:
                    b = b2
                else:
                    b = (b1 + b2) / 2.0
                alpha_pairs_changed += 1
                print('iteration: %d i:%d, pairs changed %d' % (iteration, i, alpha_pairs_changed))
        if alpha_pairs_changed == 0:
            iteration += 1
        else:
            iteration = 0
        print('iteration number: %d' % iteration)
    return b, alphas


class OptStructure:
    def __init__(self, data_mat_in, class_labels, c, toler, k_tup):
        self.x = data_mat_in
        self.label_mat = class_labels
        self.c = c
        self.tol = toler
        self.m = np.shape(data_mat_in)[0]
        self.alphas = np.mat(np.zeros((self.m, 1)))
        self.b = 0
        self.e_cache = np.mat(np.zeros((self.m, 2)))
        self.k = np.mat(np.zeros((self.m, self.m)))
        for i in range(self.m):
            self.k[:, i] = kernel_trans(self.x, self.x[i, :], k_tup)


def calc_e_k(o_s, k):
    f_xk = float(np.multiply(o_s.alphas, o_s.label_mat).T * o_s.k[:, k]) + o_s.b
    e_k = f_xk - float(o_s.label_mat[k])
    return e_k


def select_j(i, o_s, e_i):
    # 选择第二个优化变量的启发式方法
    max_k = -1
    max_delta_e = 0
    e_j = 0
    o_s.e_cache[i] = [1, e_i]
    valid_e_cache_list = np.nonzero(o_s.e_cache[:, 0].A)[0]  # np.nonzero() 返回列表中非0值的下标
    if len(valid_e_cache_list) > 1:
        for k in valid_e_cache_list:
            if k == i:
                continue
            e_k = calc_e_k(o_s, k)
            delta_e = abs(e_i - e_k)
            if delta_e > max_delta_e:
                max_k = k
                max_delta_e = delta_e
                e_j = e_k
        return max_k, e_j
    else:
        j = select_j_rand(i, o_s.m)
        e_j = calc_e_k(o_s, j)
    return j, e_j


def update_ek(o_s, k):
    e_k = calc_e_k(o_s, k)
    o_s.e_cache[k] = [1, e_k]


def inner_loop(i, o_s):
    e_i = calc_e_k(o_s, i)
    if (o_s.label_mat[i] * e_i < -o_s.tol  and o_s.alphas[i] < o_s.c) or \
        (o_s.label_mat[i] * e_i > o_s.tol and o_s.alphas[i] > 0):
        j, e_j = select_j(i, o_s, e_i)
        alpha_i_old = o_s.alphas[i].copy()
        alpha_j_old = o_s.alphas[j].copy()
        if o_s.label_mat[i] != o_s.label_mat[j]:
            low = max(0, o_s.alphas[j] - o_s.alphas[i])
            high = min(o_s.c, o_s.c + o_s.alphas[j] - o_s.alphas[i])
        else:
            low = max(0, o_s.alphas[j] + o_s.alphas[i])
            high = min(o_s.c, o_s.alphas[j] + o_s.alphas[i])
        if low == high:
            # print('low == high')
            return 0
        eta = 2.0 * o_s.k[i, j] - o_s.k[i, i] - o_s.k[j, j]
        if eta >= 0:
            # print('eta >= 0')
            return 0
        o_s.alphas[j] = o_s.alphas[j] - o_s.label_mat[j] * (e_i - e_j) / eta
        o_s.alphas[j] = clip_alpha(o_s.alphas[j], high, low)
        update_ek(o_s, j)
        if abs(o_s.alphas[j] - alpha_j_old) < 1e-5:
            # print('j not moving enough')
            return 0
        o_s.alphas[i] = o_s.alphas[i] + o_s.label_mat[j] * o_s.label_mat[i] * (alpha_j_old - o_s.alphas[j])
        update_ek(o_s, i)
        b1 = o_s.b - e_i - o_s.label_mat[i] * (o_s.alphas[i] - alpha_i_old) * \
            o_s.k[i, i] - o_s.label_mat[j] * (o_s.alphas[j] - alpha_j_old) * o_s.k[i, j]
        b2 = o_s.b - e_j - o_s.label_mat[i] * (o_s.alphas[i] - alpha_i_old) * \
            o_s.k[i, j] - o_s.label_mat[j] * (o_s.alphas[j] - alpha_j_old) * o_s.k[j, j]
        if 0 < o_s.alphas[i] < o_s.c:
            o_s.b = b1
        elif 0 < o_s.alphas[j] < o_s.c:
            o_s.b = b2
        else:
            o_s.b = (b1 + b2) / 2
        return 1
    else:
        return 0


def smo_p(data_mat, class_labels, c, toler, max_iter, k_tup=('lin', 0)):
    o_s = OptStructure(np.mat(data_mat), np.mat(class_labels).transpose(), c, toler, k_tup)
    iteration = 0
    entire_set = True
    alpha_pairs_changed = 0
    while iteration < max_iter and (alpha_pairs_changed > 0 or entire_set):
        alpha_pairs_changed = 0
        if entire_set:
            for i in range(o_s.m):
                alpha_pairs_changed += inner_loop(i, o_s)
                # print('full set, iter: %d, i: %d pairs changed %d' % (iteration, i, alpha_pairs_changed))
            iteration += 1
        else:
            non_bound_is = np.nonzero((o_s.alphas.A > 0) * (o_s.alphas.A < c))[0]
            for i in non_bound_is:
                alpha_pairs_changed += inner_loop(i, o_s)
                # print('non-bound, iter: %d i: %d, pairs changed %d' % (iteration, i, alpha_pairs_changed))
            iteration += 1
        if entire_set:
            entire_set = False
        elif alpha_pairs_changed == 0:
            entire_set = True
        print('iteration number: %d' % iteration)
    return o_s.b, o_s.alphas


def calc_ws(alphas, data_arr, class_labels):
    x = np.mat(data_arr)
    label_mat = np.mat(class_labels).transpose()
    m, n = np.shape(x)
    w = np.zeros((n, 1))
    for i in range(m):
        w += np.multiply(alphas[i] * label_mat[i], x[i, :].T)
    return w


def kernel_trans(x, a, k_tup):
    m, n = np.shape(x)
    k = np.mat(np.zeros((m, 1)))
    if k_tup[0] == 'lin':
        k = x * a.T
    elif k_tup[0] == 'rbf':
        for j in range(m):
            delta_row = x[j, :] - a
            k[j] = delta_row * delta_row.T
        k = np.exp(k / (-1 * k_tup[1] ** 2))
    else:
        raise NameError('Houston We Have a Problem -- That Kernel is not recognized')
    return k


def test_rbf(k1=1.3):
    data_arr, label_arr = load_data('../../data/ch6/testSetRBF.txt')
    b, alphas = smo_p(data_arr, label_arr, 200, 1e-4, 10000, ('rbf', k1))
    data_mat = np.mat(data_arr)
    label_mat = np.mat(label_arr).transpose()
    sv_ind = np.nonzero(alphas.A > 0)[0]
    sv_s = data_mat[sv_ind]
    label_sv = label_mat[sv_ind]
    print('there are %d Support Vectors' % np.shape(sv_s)[0])
    m, n = np.shape(data_mat)
    err_cnt = 0
    for i in range(m):
        kernel_eval = kernel_trans(sv_s, data_mat[i, :], ('rbf', k1))
        predict = kernel_eval.T * np.multiply(label_sv, alphas[sv_ind]) + b
        if np.sign(predict) != np.sign(label_arr[i]):
            err_cnt += 1
    print('the training error rate is: %f' % (float(err_cnt) / m))
    data_arr, label_arr = load_data('../../data/ch6/testSetRBF2.txt')
    err_cnt = 0
    data_mat = np.mat(data_arr)
    label_mat = np.mat(label_arr).transpose()
    m, n = np.shape(data_mat)
    for i in range(m):
        kernel_eval = kernel_trans(sv_s, data_mat[i, :], ('rbf', k1))
        predict = kernel_eval.T * np.multiply(label_sv, alphas[sv_ind]) + b
        if np.sign(predict) != np.sign(label_arr[i]):
            err_cnt += 1
    print('the test error rate is: %f' % (float(err_cnt) / m))


def img2vector(filename):
    return_vec = np.zeros((1, 1024))
    fr = open(filename)
    for i in range(32):
        line_str = fr.readline()
        for j in range(32):
            return_vec[0, 32 * i + j] = int(line_str[i])
    return return_vec


def load_image(dir_name):
    from os import listdir
    hw_labels = []
    training_file_list = listdir('../../data/ch6/%s' % dir_name)
    m = len(training_file_list)
    training_mat = np.zeros((m, 1024))
    for i in range(m):
        file_name_str = training_file_list[i]
        file_str = file_name_str.split('.')[0]
        class_num_str = int(file_str.split('_')[0])
        if class_num_str == 9:
            hw_labels.append(-1)
        else:
            hw_labels.append(1)
        training_mat[i, :] = img2vector('../../data/ch6/%s/%s' % (dir_name, file_name_str))
    return training_mat, hw_labels


def test_digits(k_tup=('rbf', 10)):
    data_arr, label_arr = load_image('trainingDigits')
    b, alphas = smo_p(data_arr, label_arr, 200, 1e-4, 10000, k_tup)
    data_mat = np.mat(data_arr)
    label_mat = np.mat(label_arr).transpose()
    sv_ind = np.nonzero(alphas.A > 0)[0]
    sv_s = data_mat[sv_ind]
    label_sv = label_mat[sv_ind]
    print('there are %d Support Vectors' % np.shape(sv_s)[0])
    m, n = np.shape(data_mat)
    err_cnt = 0
    for i in range(m):
        kernel_eval = kernel_trans(sv_s, data_mat[i, :], k_tup)
        predict = kernel_eval.T * np.multiply(label_sv, alphas[sv_ind]) + b
        if np.sign(predict) != np.sign(label_arr[i]):
            err_cnt += 1
    print('the training error rate is: %f' % (float(err_cnt) / m))
    data_arr, label_arr = load_image('testDigits')
    err_cnt = 0
    data_mat = np.mat(data_arr)
    label_mat = np.mat(label_arr).transpose()
    m, n = np.shape(data_mat)
    for i in range(m):
        kernel_eval = kernel_trans(sv_s, data_mat[i, :], k_tup)
        predict = kernel_eval.T * np.multiply(label_sv, alphas[sv_ind]) + b
        if np.sign(predict) != np.sign(label_arr[i]):
            err_cnt += 1
    print('the test error rate is: %f' % (float(err_cnt) / m))


if __name__ == '__main__':
    pass
