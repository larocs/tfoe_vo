import numpy as np
import cv2
from liegroups import SE3
import torch
from matplotlib import pyplot as plt


def reproj(p, T, d, c):
    ''' Computes rerpojection of points p given pose T and camera intrinsics c.
        T is in SE3 form.
        d is 1xN -- point depths.
        c is in 3x3 form.
        p is 3xN in image coordinates.
    '''
    c_ = np.linalg.inv(c)
    p = c_ @ p
    x = p * d
    x_ = T[:3,:3] @ x + T[:3,3:]
    p_ = x_ / x_[-1:]
    p_ = c @ p_
    return p_


def reproj_tc(p, T, d, c):
    ''' Computes rerpojection of points p given pose T and camera intrinsics c.
        T is in SE3 form.
        d is 1xN -- point depths.
        c is in 3x3 form.
        p is 3xN in image coordinates.
    '''
    c_ = torch.inverse(c)
    p = c_ @ p
    x = p * d
    x_ = T[:3,:3] @ x + T[:3,3:]
    p_ = x_ / x_[-1:]
    p_ = c @ p_
    return p_


def triangulate(p, p_, T, c, e):
    '''
    p is 3xN in pixel coordinates
    T is 4x4
    c is 3x3
    e is 2x1 in pixel coordinates
    '''
    c_ = np.linalg.inv(c)
    z = np.ones((1, 1))
    e = e * 1e3
    e = np.expand_dims(e, axis=-1)
    e = np.concatenate([e, z], axis=0)
    e = c_ @ e

    d = depth_np2(p, (p_ - p), T, e)
    x = p * d
    return x


def triangulate_(p, p_, T, c):
    '''
    p is 2xN in pixel coordinates
    T is 4x4
    c is 3x3
    '''
    P0 = c @ np.eye(4)[:3] # 3x4
    P1 = c @ T[:3] # 3x4
    #P0 = np.eye(4)[:3]  # 3x4
    #P1 = T[:3]  # 3x4
    P0 = np.array(P0, dtype=np.float32)
    P1 = np.array(P1, dtype=np.float32)
    p = np.array(p, dtype=np.float32)
    p_ = np.array(p_, dtype=np.float32)
    X = cv2.triangulatePoints(P0, P1, p, p_)
    X = X / X[3]
    return X


def rel_scale(T01, T12, T02):
    '''
    T* is 4x4 (SE3 form)
    '''
    ival = np.arange(0.9, 1.1, 1e-2)

    min_e = np.inf
    min_s = 1.0
    R12t01 = T12[:3, :3] @ T01[:3, 3:]
    errs = []
    for s in ival:
        t_ = R12t01 + s * T12[:3, 3:]
        t_ = t_ / np.linalg.norm(t_)
        err = np.linalg.norm(T02[:3, 3:] - t_)
        errs.append(err)
        if err < min_e:
            min_e = err
            min_s = s

    plt.plot(ival, errs, '.')
    plt.show()
    #med = np.median(errs)
    #rs = np.argmin(np.abs(errs - med))

    return min_s


def rel_scale_(T01, T12, T02):
    '''
    T* is 4x4 (SE3 form)
    '''
    t02 = T02[:3, 3:]
    t12 = T12[:3, 3:]
    t01_ = (T12[:3, :3] @ T01[:3, 3:])
    A = np.concatenate([t01_, -t02], axis=-1)
    b = -t12[:, 0]
    s = np.linalg.lstsq(A, b)
    #s = np.linalg.solve(A[[0, 1]], b[[0, 1]])
    #print('solve', s)
    return 1.0 / s[0][0]


def reproj_tc_foe(p, p_, T, foe, c):
    ''' Computes rerpojection of points p given pose T and camera intrinsics c.
        T is in SE3 form.
        d is 1xN -- point depths.
        c is in 3x3 form.
        p is 3xN in image coordinates.
    '''
    c_ = torch.inverse(c)
    p = c_ @ p
    p_ = c_ @ p_
    z = torch.ones(1, 1).double()

    foe = foe * 1e3  ###
    foe = torch.cat([foe, z], dim=0)
    foe = c_ @ foe

    #d = depth_tc(p[:2], (p_-p)[:2], foe[:2])
    d = depth_tc2(p, (p_ - p), T, foe)

    x = p * d
    x_ = T[:3, :3] @ x + T[:3, 3:]
    p_rep = x_ / x_[-1:]

    ##p_rep = c @ p_rep
    return p_rep


def reproj_tc_foe_ba(p, p_, T, foe, c):
    ''' Computes rerpojection of points p given pose T and camera intrinsics c.
        T is in SE3 form.
        d is 1xN -- point depths.
        c is in 3x3 form.
        p is 3xN in image coordinates.
    '''
    T = torch.inverse(T)
    c_ = torch.inverse(c)
    p = c_ @ p
    p_ = c_ @ p_
    z = torch.ones(1, 1).double()
    foe = foe * 1e3  ###
    foe = torch.cat([foe, z], dim=0)
    foe = c_ @ foe
    d = depth_tc2(p, (p_ - p), T, foe)
    x = p * d
    x_ = T[:3, :3] @ x + T[:3, 3:]
    p_rep = x_ / x_[-1:]
    return p_rep


def reproj_tc_foe_local(p, p_, T, foe, c):
    ''' Computes rerpojection of points p given pose T and camera intrinsics c.
        T is in SE3 form.
        d is 1xN -- point depths.
        c is in 3x3 form.
        p is 3xN in image coordinates.
    '''
    T = torch.inverse(T)
    c_ = torch.inverse(c)
    p = c_ @ p
    p_ = c_ @ p_
    z = torch.ones(1, 1).double()
    foe = foe * 1e3  ###
    foe = torch.cat([foe, z], dim=0)
    foe = c_ @ foe
    d = depth_tc2(p, (p_ - p), T, foe)
    x = p * d
    x_ = T[:3, :3] @ x + T[:3, 3:]
    p_rep = x_ / x_[-1:]
    return p_rep


def reproj_tc_foe_slocal(p, p_, T, foe, c):
    ''' Computes rerpojection of points p given pose T and camera intrinsics c.
        T is in SE3 form.
        d is 1xN -- point depths.
        c is in 3x3 form.
        p is 3xN in image coordinates.
    '''
    T = torch.inverse(T)
    c_ = torch.inverse(c)
    p = c_ @ p
    p_ = c_ @ p_
    #z = torch.ones(1, 1).double()
    #foe = foe * 1e3
    foe = torch.abs(foe[-1]) * foe / (foe[-1].clone() + 1e-10) ### singularity at tz = 0
    #foe = torch.cat([foe, z], dim=0)
    foe = c_ @ foe
    d = depth_tc2(p, (p_ - p), T, foe)
    x = p * d
    x_ = T[:3, :3] @ x + T[:3, 3:]
    p_rep = x_ / x_[-1:].clone()
    return p_rep


def reproj_tc_(p, p_, T, foe, c):
    ''' Computes rerpojection of points p given pose T and camera intrinsics c.
        T is in SE3 form.
        d is 1xN -- point depths.
        c is in 3x3 form.
        p is 3xN in image coordinates.
    '''
    c_ = torch.inverse(c)
    p = c_ @ p
    p_ = c_ @ p_
    z = torch.ones(1, 1).double()

    foe = torch.cat([foe, z], dim=0)
    # foe = c_ @ foe

    foe = c @ T[:3, 3:] + 0.0*foe
    foe = foe / (foe[-1] + 1e-8)
    foe = c_ @ foe

    d = depth_tc(p[:2], (p_-p)[:2], foe[:2])

    x = p * d
    x_ = T[:3, :3] @ x + T[:3, 3:]
    p_rep = x_ / x_[-1:]

    return p_rep


def depth_tc(p, f, foe):
    ''' p is 2xN
        f is 2xN (flow)
        foe is 2x1
    '''
    mag = torch.norm(f, dim=0)
    mag = torch.clamp(mag, min=1e-3) # 1e-3
    dist = (p+f)-foe
    dist = torch.norm(dist, dim=0)
    d = dist / mag
    return d


def depth_tc2(p, f, T, foe):
    ''' p is 3xN
        f is 3xN (flow)
        foe is 3x1
    '''
    n = p.size(1)
    Rt = T[:3, :3] @ foe #T[:3, 3:] # 3,1
    Rx = T[:3, :3] @ p # 3,N
    I = torch.eye(2).double()
    I = I.unsqueeze(0).repeat(n, 1, 1) # N,2,2
    I = torch.cat([I, -(p+f)[:2].permute(1, 0).unsqueeze(-1)], dim=-1) # N,2,3
    den = I @ Rx.permute(1, 0).unsqueeze(-1) # N,2,1
    den = den.squeeze(-1)
    den = torch.norm(den, dim=-1) + 1e-8 # N
    num = I @ Rt.unsqueeze(0).repeat(n, 1, 1) # N,2,1
    num = num.squeeze(-1)
    num = torch.norm(num, dim=-1) # N
    d = num / den # N
    return d


def depth_np2(p, f, T, foe):
    ''' p is 3xN
        f is 3xN (flow)
        foe is 3x1
    '''
    p = torch.from_numpy(p)
    f = torch.from_numpy(f)
    T = torch.from_numpy(T)
    foe = torch.from_numpy(foe)
    d = depth_tc2(p, f, T, foe)
    d = d.detach().numpy()
    return d


def depth_tc_(p, f, T, foe):
    ''' p is 3xN
        f is 3xN (flow)
        T is 4x4
        foe is 3x1
    '''
    #T = torch.inverse(T)
    p_ = p + f
    v = T[0, :3].unsqueeze(-1) - p_[[0], :]*T[2, :3].unsqueeze(-1)
    v = v.T.unsqueeze(1) # n,1,3
    num = v[:, 0] @ T[:3, 3:] # n,1
    #num = v[:, 0] @ foe  # n,1
    den = v @ p.T.unsqueeze(-1) # n,1,1
    den = den + 1e-8 #torch.clamp(den, min=1e-3)

    #print(torch.min(num), torch.max(num))
    #print(torch.min(den), torch.max(den))
    #input()

    d = num / den.squeeze(-1) # n,1
    d = d.squeeze(-1) # n
    #d = torch.clamp(d, min=1e-3, max=1e4)
    return d


def depth(p,f,foe):
    ''' p is 2xN
        f is 2xN (flow)
        foe is 2x1
    '''
    mag = np.linalg.norm(f,axis=0)
    dist = p-foe
    dist = np.linalg.norm(dist,axis=0)
    d = dist / mag
    return d


def E_from_T(T):
    '''
    T is in SE3 form.
    '''
    R = T[:3, :3]
    t = T[:3, 3]
    tn = torch.norm(t)
    if tn == 0.0:
        t = t + 1e-3*torch.randn(t.size())
        tn = torch.norm(t)
    t = t / tn
    tx = torch.tensor([[0.0, -t[2], t[1]],
                       [t[2], 0.0, -t[0]],
                       [-t[1], t[0], 0.0]])
    tx = tx.double()
    E = tx @ R
    return E


def gen_pts(n):
    ''' returns x,x'
        x and x' are 3xN
    '''
    x = 1e4*np.random.randn(3,n)
    x[-1] = 1.0
    d = 1e4*np.abs(np.random.randn(1,n))
    
    tse3 = 1e-2*np.random.randn(6)
    tse3[[3,5]] = 0.0
    T = SE3.exp(tse3)
    T = T.as_matrix()
    R = T[:3,:3]
    t = T[:3,3:]
    
    #print(x*d)
    #print(R)
    #print(R @ (x*d))
    #print()
    
    x_ = R @ (x*d) + t
    x_ = x_ / x_[[-1]]
    
    return x,x_,d,R,t


if __name__ == '__main__':
    x,x_,d,R,t = gen_pts(60)
    f = x_-x
    c = np.eye(3)
    T = np.eye(4)
    T[:3,:3] = R
    T[:3,3:] = t
    
    x_rep = reproj_tc(torch.from_numpy(x),\
                      torch.from_numpy(T),\
                      torch.from_numpy(d),\
                      torch.from_numpy(c))
    print(np.linalg.norm(x_-x_rep.detach().numpy()))
    
    x_rep = reproj(x,T,d,c)
    print(np.linalg.norm(x_-x_rep))
    foe = np.zeros((2,1))
    d_ = depth(x[:2],f,foe)
    x_rep = reproj(x,T,d_,c)
    print(np.linalg.norm(x_-x_rep))

