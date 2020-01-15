import functools

import torch

from backpack.utils.einsum import einsum


def new_output_convention(old_mat, module):
    print("[to new]: in  {}".format(old_mat.shape))
    N = module.output_shape[0]
    V = old_mat.shape[-1]
    # (C_out, H_out, W_out, ...)
    out_features_shape = module.output_shape[1:]
    # C_out * H_out * W_out * ...
    out_features = torch.prod(out_features_shape)

    # [N, C_out * H_out * W_out, V]
    assert old_mat.shape == (N, out_features, V)
    # [V, N, C_out * H_out * W_out]
    new_mat = einsum("ndv->vnd", old_mat)
    # [V, N, C_out, H_out, W_out, ...]
    new_shape = (V, N) + tuple(out_features_shape)
    new_mat = new_mat.reshape(new_shape)

    print("[to new]: out {}".format(new_mat.shape))

    return new_mat


def old_input_convention(new_mat, module):
    print("[to old]: in  {}".format(new_mat.shape))
    N = module.input0_shape[0]
    V = new_mat.shape[0]
    # (C_in, H_in, W_in, ...)
    in_features_shape = module.input0_shape[1:]
    # C_in * H_in * W_in * ...
    in_features = torch.prod(in_features_shape)

    # [V, N, C_in, H_in, W_in]
    assert new_mat.shape == (V, N) + tuple(in_features_shape)
    # [V, N, C_in* H_in* W_in]
    old_mat = new_mat.reshape((V, N, in_features))
    # [N, C_in* H_in* W_in, V]
    old_mat = einsum("vnc->ncv", old_mat)

    print("[to old]: out {}".format(old_mat.shape))

    return old_mat


def add_V_dim(old_mat):
    return old_mat.unsqueeze(-1)


def remove_V_dim(old_mat):
    return old_mat.squeeze(-1)


def jac_t_new_shape_convention(jmp):
    """Use new convention internally, old convention for IO."""

    @functools.wraps(jmp)
    def wrapped_jac_t_use_new_convention(self, module, g_inp, g_out, mat, **kwargs):
        # [N, D, V]
        is_vec = len(mat.shape) == 2
        print(is_vec)
        mat_used = mat if not is_vec else add_V_dim(mat)

        # convert and run with new convention
        mat_used = new_output_convention(mat_used, module)
        result = jmp(self, module, g_inp, g_out, mat_used, **kwargs)
        result = old_input_convention(result, module)

        result = result if not is_vec else remove_V_dim(result)

        return result

    return wrapped_jac_t_use_new_convention