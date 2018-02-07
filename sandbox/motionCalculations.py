
from nipy.algorithms.registration import HistogramRegistration, Rigid

import nibabel as nib





# Convert from 4x4 to 1x12
class Rigid(Affine):
    param_inds = list(range(6))

    def from_matrix44(self, aff):
        """
        Convert a 4x4 matrix describing a rigid transform into a
        12-sized vector of natural affine parameters: translation,
        rotation, log-scale, pre-rotation (to allow for pre-rotation
        when combined with non-unitary scales). In case the transform
        has a negative determinant, set the `_direct` attribute to
        False.
        """
        vec12 = np.zeros((12,))
        vec12[:3] = aff[:3, 3]
        R = aff[:3, :3]

        # if the determinant is negative, set the _direct attribute to False (not sure what that changes)
        if spl.det(R) < 0:
            R = -R
            self._direct = False
        vec12[3:6] = rotation_mat2vec(R)
        vec12[6:9] = 0.0
        self._vec12 = vec12

    def __str__(self):
        string = 'translation : %s\n' % str(self.translation)
        string += 'rotation    : %s\n' % str(self.rotation)
        return string


def rotation_mat2vec(R):
    """ Rotation vector from rotation matrix `R`
    Parameters
    ----------
    R : (3,3) array-like
        Rotation matrix
    Returns
    -------
    vec : (3,) array
        Rotation vector, where norm of `vec` is the angle ``theta``, and the
        axis of rotation is given by ``vec / theta``
    """
    ax, angle = quat2axangle(mat2quat(R))
    return ax * angle



def mat2quat(M):
    ''' Calculate quaternion corresponding to given rotation matrix
    Parameters
    ----------
    M : array-like
      3x3 rotation matrix
    Returns
    -------
    q : (4,) array
      closest quaternion to input matrix, having positive q[0]
    Notes
    -----
    Method claimed to be robust to numerical errors in M
    Constructs quaternion by calculating maximum eigenvector for matrix
    K (constructed from input `M`).  Although this is not tested, a
    maximum eigenvalue of 1 corresponds to a valid rotation.
    A quaternion q*-1 corresponds to the same rotation as q; thus the
    sign of the reconstructed quaternion is arbitrary, and we return
    quaternions with positive w (q[0]).

    Examples
    --------
    >>> import numpy as np
    >>> q = mat2quat(np.eye(3)) # Identity rotation
    >>> np.allclose(q, [1, 0, 0, 0])
    True
    >>> q = mat2quat(np.diag([1, -1, -1]))
    >>> np.allclose(q, [0, 1, 0, 0]) # 180 degree rotn around axis 0
    True
    Notes
    -----
    http://en.wikipedia.org/wiki/Rotation_matrix#Quaternion
    Bar-Itzhack, Itzhack Y. (2000), "New method for extracting the
    quaternion from a rotation matrix", AIAA Journal of Guidance,
    Control and Dynamics 23(6):1085-1087 (Engineering Note), ISSN
    0731-5090
    '''
    # Qyx refers to the contribution of the y input vector component to
    # the x output vector component.  Qyx is therefore the same as
    # M[0,1].  The notation is from the Wikipedia article.
    Qxx,Qyx,Qzx,Qxy,Qyy,Qzy,Qxz,Qyz,Qzz=M.flat
    # Fill only lower half of symmetric matrix
    K = np.array([
        [Qxx-Qyy-Qzz, 0, 0, 0],
        [Qyx+Qxy, Qyy-Qxx-Qzz, 0, 0],
        [Qzx+Qxz, Qzy+Qyz, Qzz-Qxx-Qyy, 0],
        [Qyz-Qzy, Qzx-Qxz, Qxy-Qyx, Qxx+Qyy+Qzz]]) / 3
    # Use Hermitian eigenvectors, values for speed
    vals, vecs = np.linalg.eigh(K)
    # Select largest eigenvector, reorder to w,x,y,z quaternion
    q = vecs[[3, 0, 1, 2],np.argmax(vals)]
    # Prefer quaternion with positive w
    # (q * -1 corresponds to same rotation as q)
    if q[0]<0:
        q *= -1
    return q


def quat2axangle(quat, identity_thresh=None):
    ''' Convert quaternion to rotation of angle around axis
    Parameters
    ----------
    quat : 4 element sequence
       w, x, y, z forming quaternion
    identity_thresh : None or scalar, optional
       threshold below which the norm of the vector part of the
       quaternion (x, y, z) is deemed to be 0, leading to the identity
       rotation.  None (the default) leads to a threshold estimated
       based on the precision of the input.

    Returns
    -------
    theta : scalar
       angle of rotation
    vector : array shape (3,)
       axis around which rotation occurs
    Examples
    --------
    >>> vec, theta = quat2axangle([0, 1, 0, 0])
    >>> vec
    array([ 1.,  0.,  0.])
    >>> np.allclose(theta, np.pi)
    True
    If this is an identity rotation, we return a zero angle and an
    arbitrary vector

    >>> quat2axangle([1, 0, 0, 0])
    (array([ 1.,  0.,  0.]), 0.0)
    Notes
    -----
    A quaternion for which x, y, z are all equal to 0, is an identity
    rotation.  In this case we return a 0 angle and an  arbitrary
    vector, here [1, 0, 0]
    '''
    w, x, y, z = quat
    vec = np.asarray([x, y, z])
    if identity_thresh is None:
        try:
            identity_thresh = np.finfo(vec.dtype).eps * 3
        except ValueError:  # integer type
            identity_thresh = _FLOAT_EPS * 3
    len2 = x * x + y * y + z * z
    if len2 < identity_thresh ** 2:
        # if vec is nearly 0,0,0, this is an identity rotation
        return np.array([1.0, 0, 0]), 0.0
    theta = 2 * math.acos(max(min(w, 1), -1))
    if len2 == float('inf'):
        return np.zeros((3,)), theta
    return vec / math.sqrt(len2), theta
