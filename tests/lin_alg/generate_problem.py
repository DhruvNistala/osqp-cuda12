import numpy as np
from scipy import sparse
import scipy.sparse.linalg as sla
import utils.codegen_utils as cu
from numpy.random import Generator, PCG64

# Set random seed for reproducibility
rg = Generator(PCG64(1))

# Test sparse matrix construction vs dense
test_sp_matrix_Adns = np.around(.6*rg.random((5, 6))) + rg.standard_normal((5,6))
test_sp_matrix_A = sparse.csc_matrix(test_sp_matrix_Adns)


# Test vector operations
test_vec_ops_n = 10
test_vec_ops_v1 = rg.standard_normal(test_vec_ops_n)
test_vec_ops_v2 = rg.standard_normal(test_vec_ops_n)
test_vec_ops_sc1 = rg.standard_normal()
test_vec_ops_sc2 = rg.standard_normal()
test_vec_ops_norm_inf = np.linalg.norm(test_vec_ops_v1, np.inf)
test_vec_ops_norm_inf_diff = np.linalg.norm(test_vec_ops_v1 - test_vec_ops_v2,
                                            np.inf)
test_vec_ops_add_scaled = test_vec_ops_sc1 * test_vec_ops_v1 + test_vec_ops_sc2 * test_vec_ops_v2
test_vec_ops_ew_reciprocal = np.reciprocal(test_vec_ops_v1)
test_vec_ops_vec_prod = test_vec_ops_v1.dot(test_vec_ops_v2)
test_vec_ops_ew_max_vec = np.maximum(test_vec_ops_v1, test_vec_ops_v2)
test_vec_ops_ew_min_vec = np.minimum(test_vec_ops_v1, test_vec_ops_v2)


# Test matrix operations
test_mat_ops_n = 2
test_mat_ops_A = sparse.random(test_mat_ops_n, test_mat_ops_n, density=0.8, format='csc', random_state=rg)
test_mat_ops_d = rg.standard_normal(test_mat_ops_n)
D = sparse.diags(test_mat_ops_d, format='csc')
test_mat_ops_prem_diag = D.dot(test_mat_ops_A).tocoo().tocsc()   # Force matrix reordering
test_mat_ops_postm_diag = test_mat_ops_A.dot(D).tocoo().tocsc()  # Force matrix reordering
test_mat_ops_inf_norm_cols = np.amax(np.abs(
    np.asarray(test_mat_ops_A.todense())), axis=0)
test_mat_ops_inf_norm_rows = np.amax(np.abs(
    np.asarray(test_mat_ops_A.todense())), axis=1)

# Test matrix vector operations
m = 5
n = 4
p = 0.4

test_mat_vec_n = n
test_mat_vec_m = m
test_mat_vec_A = sparse.random(m, n, density=1.0, format='csc', random_state=rg)
test_mat_vec_P = sparse.random(n, n, density=0.8, format='csc', random_state=rg)
test_mat_vec_P = test_mat_vec_P + test_mat_vec_P.T
test_mat_vec_Pu = sparse.triu(test_mat_vec_P, format='csc')
test_mat_vec_x = rg.standard_normal(n)
test_mat_vec_y = rg.standard_normal(m)
test_mat_vec_Ax = test_mat_vec_A.dot(test_mat_vec_x)
test_mat_vec_Ax_cum = test_mat_vec_A.dot(test_mat_vec_x) + test_mat_vec_y
test_mat_vec_ATy = test_mat_vec_A.T.dot(test_mat_vec_y)
test_mat_vec_ATy_cum = test_mat_vec_A.T.dot(test_mat_vec_y) + test_mat_vec_x
test_mat_vec_Px = test_mat_vec_P.dot(test_mat_vec_x)
test_mat_vec_Px_cum = test_mat_vec_P.dot(test_mat_vec_x) + test_mat_vec_x


# Test extract upper triangular
test_mat_extr_triu_n = 5
test_mat_extr_triu_P = sparse.random(test_mat_extr_triu_n, test_mat_extr_triu_n, density=0.8, format='csc', random_state=rg)
test_mat_extr_triu_P = test_mat_extr_triu_P + test_mat_extr_triu_P.T
test_mat_extr_triu_Pu = sparse.triu(test_mat_extr_triu_P, format='csc')
test_mat_extr_triu_P_inf_norm_cols = np.amax(np.abs(
    np.asarray(test_mat_extr_triu_P.todense())), axis=0)


# Test compute quad form
test_qpform_n = 4
test_qpform_P = sparse.random(test_qpform_n, test_qpform_n, density=0.8, format='csc', random_state=rg)
test_qpform_P = test_qpform_P + test_qpform_P.T
test_qpform_Pu = sparse.triu(test_qpform_P, format='csc')
test_qpform_x = rg.standard_normal(test_qpform_n)
test_qpform_value = .5 * test_qpform_x.T.dot(test_qpform_P.dot(test_qpform_x))


# Generate test data and solutions
data = {'test_sp_matrix_A': test_sp_matrix_A,
        'test_sp_matrix_Adns': test_sp_matrix_Adns,
        'test_vec_ops_n': test_vec_ops_n,
        'test_vec_ops_v1': test_vec_ops_v1,
        'test_vec_ops_v2': test_vec_ops_v2,
        'test_vec_ops_sc1': test_vec_ops_sc1,
        'test_vec_ops_sc2': test_vec_ops_sc2,
        'test_vec_ops_norm_inf': test_vec_ops_norm_inf,
        'test_vec_ops_norm_inf_diff': test_vec_ops_norm_inf_diff,
        'test_vec_ops_add_scaled': test_vec_ops_add_scaled,
        'test_vec_ops_ew_reciprocal': test_vec_ops_ew_reciprocal,
        'test_vec_ops_vec_prod': test_vec_ops_vec_prod,
        'test_vec_ops_ew_max_vec': test_vec_ops_ew_max_vec,
        'test_vec_ops_ew_min_vec': test_vec_ops_ew_min_vec,
        'test_mat_ops_n': test_mat_ops_n,
        'test_mat_ops_A': test_mat_ops_A,
        'test_mat_ops_d': test_mat_ops_d,
        'test_mat_ops_prem_diag': test_mat_ops_prem_diag,
        'test_mat_ops_postm_diag': test_mat_ops_postm_diag,
        'test_mat_ops_inf_norm_cols': test_mat_ops_inf_norm_cols,
        'test_mat_ops_inf_norm_rows': test_mat_ops_inf_norm_rows,
        'test_mat_vec_n': test_mat_vec_n,
        'test_mat_vec_m': test_mat_vec_m,
        'test_mat_vec_A': test_mat_vec_A,
        'test_mat_vec_Pu': test_mat_vec_Pu,
        'test_mat_vec_x': test_mat_vec_x,
        'test_mat_vec_y': test_mat_vec_y,
        'test_mat_vec_Ax': test_mat_vec_Ax,
        'test_mat_vec_Ax_cum': test_mat_vec_Ax_cum,
        'test_mat_vec_ATy': test_mat_vec_ATy,
        'test_mat_vec_ATy_cum': test_mat_vec_ATy_cum,
        'test_mat_vec_Px': test_mat_vec_Px,
        'test_mat_vec_Px_cum': test_mat_vec_Px_cum,
        'test_mat_extr_triu_n': test_mat_extr_triu_n,
        'test_mat_extr_triu_P': test_mat_extr_triu_P,
        'test_mat_extr_triu_Pu': test_mat_extr_triu_Pu,
        'test_mat_extr_triu_P_inf_norm_cols':
        test_mat_extr_triu_P_inf_norm_cols,
        'test_qpform_n': test_qpform_n,
        'test_qpform_Pu': test_qpform_Pu,
        'test_qpform_x': test_qpform_x,
        'test_qpform_value': test_qpform_value,
        }

# Generate test data
cu.generate_data('lin_alg', data)
