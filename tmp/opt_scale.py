import numpy as np
from scipy.optimize import minimize, least_squares
from reproj import gen_pts
from reproj import reproj_tc_foe
from reproj import reproj_tc_foe_scale
from liegroups import SE3
import torch
import torch.nn.functional as F
from liegroups.torch import SE3 as SE3tc
from hessian import jacobian, hessian
from utils import compose_scale


class OptSingle:
    def __init__(self, x, x_, T0ij, c, g):
        ''' x and x_ are (i, j) -> 3xN
        '''
        self.g = g
        self.x = x # (i, j) -> x
        self.x_ = x_  # (i, j) -> x_
        self.T0ij = T0ij
        #self.f = {}  # (i, j) -> f
        #for k in x:
        #    self.f[k] = x_[k] - x[k]
        self.T = np.zeros(6)
        self.foe = np.zeros(2)
        self.c = torch.from_numpy(c) #.float()
        self.c_ = torch.inverse(self.c)
        self.min_obj = np.inf
    
    def obj_tc(self, Tfoe):
        T = Tfoe[:6]
        foe = Tfoe[6:]
        foe = foe.unsqueeze(-1)
        T = SE3tc.exp(T.clone())
        T = T.as_matrix()
        c = self.c
        c_ = self.c_
        x_rep = reproj_tc_foe(torch.from_numpy(self.x),
                              torch.from_numpy(self.x_),
                              T, foe, c)
        y = c_ @ torch.from_numpy(self.x_)-x_rep
        y = torch.mean(y**2.0)
        return y
   
    def obj_npy(self, Tfoe):
        Tfoe = torch.from_numpy(Tfoe)
        Tfoe = Tfoe.requires_grad_(True)
        Tfoe.retain_grad()
        Tfoe_ = Tfoe.clone()
        y = self.obj_tc(Tfoe_)
        y = y.detach().numpy()
        return y
    
    def jac_npy(self, Tfoe):
        Tfoe = torch.from_numpy(Tfoe)
        Tfoe = Tfoe.requires_grad_(True)
        jac = jacobian(self.obj_tc(Tfoe),Tfoe)
        jac = jac.detach().numpy()
        return jac
    
    def hess_npy(self, Tfoe):
        Tfoe = torch.from_numpy(Tfoe)
        Tfoe = Tfoe.requires_grad_(True)
        hess = hessian(self.obj_tc(Tfoe), Tfoe)
        hess = hess.detach().numpy()
        return hess
    
    def objective(self, Tfoe, grad=True, residuals=False):
        ''' Tfoe is n*9
        '''
        Tfoe = torch.from_numpy(Tfoe)
        Tfoe = Tfoe.requires_grad_(True)
        Tfoe.retain_grad()
        Tfoe_ = Tfoe.clone()
        Tfoe_ = Tfoe_.reshape(-1, 9)

        g = self.g # bundle graph
        c = self.c
        c_ = self.c_

        T = Tfoe_[:, :6]
        foe = Tfoe_[:, 6:8]
        scale = Tfoe_[:, 8:]
        foe = foe.unsqueeze(-1)
        T = SE3tc.exp(T.clone())
        T = T.as_matrix()

        y = 0.0
        #resid = []
        for ij in g:
            Tij, foeij, scji, ep_ = compose_scale(ij[0], ij[1],
                                            T.clone(), foe.clone(),
                                            scale.clone(), c, base=self.base)
            #print(Tij.detach().numpy())
            #print(torch.inverse(Tij).detach().numpy())
            #print(foeij.detach().numpy())
            x_rep = reproj_tc_foe_scale(torch.from_numpy(self.x[ij]),
                                        torch.from_numpy(self.x_[ij]),
                                        Tij, foeij, c)
            yij = F.smooth_l1_loss(c_ @ torch.from_numpy(self.x_[ij]), x_rep)

            T0ij = torch.from_numpy(self.T0ij[ij])
            #t0ij = T0ij[:3, 3:]
            #ep0ij = (c @ (t0ij / (t0ij[-1] + 1e-10))) / 1e3
            #ep0ij = ep0ij[:2]
            #x_rep0 = reproj_tc_foe_local(torch.from_numpy(self.x[ij]),
            #                             torch.from_numpy(self.x_[ij]),
            #                             T0ij, ep0ij, c)
            #yij0 = F.smooth_l1_loss(c_ @ torch.from_numpy(self.x_[ij]), x_rep0)

            #resid.append(torch.norm(c_ @ torch.from_numpy(self.x_[ij]) - x_rep, dim=0)**2)

            yt_ij = F.smooth_l1_loss(scji * Tij[:3, :3], T0ij[:3, :3])
            #yt_ij_t = F.smooth_l1_loss(Tij[:2, 3], T0ij[:2, 3] * Tij[2, 3]) ### * Tij[2, 3]
            #yt_ij_t = torch.sum(torch.abs(Tij[:2, 3] - T0ij[:2, 3]))
            y_ep = F.smooth_l1_loss(foeij, ep_)

            if ij[1] - ij[0] == 2 and False:
                print(ij)
                print(Tij)
                print(T0ij)
                #print(yt_ij_t)
                print(foeij.detach().numpy())
                print(ep_.detach().numpy())
                #print(yij.item(), yt_ij.item())
                input()

            #if yij < 1e-4:
            # y = y + 1e-1*yij + yt_ij # (0,1), (1,0)

            #if yij0 < 1e-8:
            #    y = y + yt_ij + yt_ij_t
            #elif yij < 1e-8:
            #    y = y + yij
            #else:
            y = y + yij + 1e-2*y_ep + 1e-2*yt_ij # + 1e-4*yt_ij #
        #input()
        #resid = torch.cat(resid, dim=0)

        y = y / len(g)
        y.backward()
        gradTfoe = Tfoe.grad.detach().numpy()
        y = y.detach().numpy()
        self.min_obj = min(self.min_obj, y)
        if grad:
            #print(gradTfoe)
            #print(Tfoe.detach().numpy())
            #input()
            return y, gradTfoe
        elif residuals:
            return None #resid.detach().numpy()
        else:
            return y

    def optimize(self, T0, foe0, scale, freeze=True):
        ''' T0 is n,6
            foe0 is n,2
            scale is n,1
        '''
        self.base = np.min([ij[0] for ij in self.g])
        self.min_obj = np.inf
        Tfoe0 = np.concatenate([T0, foe0, scale], axis=-1) # n,8
        Tfoe0 = Tfoe0.reshape((-1,))
        #Tfoe0 = np.expand_dims(Tfoe0, axis=-1)

        bounds = []
        if freeze:
            for par in Tfoe0:
                bounds.append((par-1e-10, par+1e-10))
            #for par in Tfoe0[:6]:
            #    bounds.append((par-1e-10, par+1e-10))
            #for par in Tfoe0[6:]:
            #    bounds.append((None, None))
        else:
            for i, par in enumerate(Tfoe0):
                #if i % 9 > 5 or i % 9 in [1, 3, 5]:
                if i == 8:
                    bounds.append((par - 1e-10, par + 1e-10))
                elif i % 9 == 2 and False:
                    bounds.append((par - 1e-10, par + 1e-10))
                elif i % 9 < 8 and False:
                    bounds.append((par - 1e-10, par + 1e-10))
                else:
                    bounds.append((None, None))

        res = minimize(self.objective,
                       Tfoe0, method='L-BFGS-B',
                       jac=True,
                       bounds=bounds,
                       tol=1e-14,
                       options={'disp': False,
                                'maxiter': 1e3,
                                'gtol': 1e-12,
                                'ftol': 1e-12,
                                'maxcor': len(Tfoe0)})

        #res = least_squares(self.objective,
        #                    Tfoe0, method='lm',
        #                    kwargs={'grad': False,
        #                            'residuals': True})

        return res.x


if __name__ == '__main__':
    x, x_, d, R, t = gen_pts(3)
    
    opt = OptSingle(x, x_)
    T0 = np.zeros(6)
    foe0 = np.zeros(2)
    with torch.autograd.set_detect_anomaly(False):
        Tfoe = opt.optimize(T0, foe0)
    T = Tfoe[:6]
    foe = Tfoe[6:]
    T = SE3.exp(T).as_matrix()
    print(T[:3, :3])
    print(R)
    print(foe)
    print()
    print(T[:3, 3:])
    print(t)
