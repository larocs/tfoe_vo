# id0 = j - 1
# id1 = j
# id2 = j + 1
# print(id0, id1)
# print(ge[j] - c_[:2, -1])
# print(ge[i] - c_[:2, -1])
# sc = np.linalg.norm(ge[j] - c_[:2, -1])\
#     / np.linalg.norm(ge[i] - c_[:2, -1])
# print(sc)
# input()

# ptid00 = np.random.randint(low=0, high=x[(id0, id1)].shape[1] - 1)
##ptid01 = np.random.randint(low=0, high=x[(id0, id1)].shape[1] - 1)
# ptid01 = (ptid00 + 83) % x[(id0, id1)].shape[1]

# if ptid00 == ptid01:
#    ptid01 = ptid00 + 1

# ptid10 = np.argmin([np.linalg.norm(x_[(id0, id1)][:, ptid00].T - p01)
#                    for p01 in x[(id1, id1 + 1)].T])
# ptid11 = np.argmin([np.linalg.norm(x_[(id0, id1)][:, ptid01].T - p11)
#                    for p11 in x[(id1, id1 + 1)].T])

# X00 = triangulate(x[(id0, id1)][:, [ptid00]], x_[(id0, id1)][:, [ptid00]],
#                  kp._T0[id0], kp.camera_matrix, ge[id0])
# X01 = triangulate(x[(id0, id1)][:, [ptid01]], x_[(id0, id1)][:, [ptid01]],
#                  kp._T0[id0], kp.camera_matrix, ge[id0])

# X10 = triangulate(x[(id1, id1 + 1)][:, [ptid10]], x_[(id1, id1 + 1)][:, [ptid10]],
#                  kp._T0[id1], kp.camera_matrix, ge[id1])
# X11 = triangulate(x[(id1, id1 + 1)][:, [ptid11]], x_[(id1, id1 + 1)][:, [ptid11]],
#                  kp._T0[id1], kp.camera_matrix, ge[id1])

# rs = np.linalg.norm(X00[-1] - X01[-1])\
#     / (np.linalg.norm(X10[-1] - X11[-1]) + 1e-10)

# X01 = triangulate(x[(id0, id1)], x_[(id0, id1)],
#                  kp._T0[id0], kp.camera_matrix, ge[id0])
# X12 = triangulate(x[(id1, id2)], x_[(id1, id2)],
#                  kp._T0[id1], kp.camera_matrix, ge[id1])
# rs = np.mean(np.linalg.norm(X12[-1], axis=0))\
#     / np.mean(np.linalg.norm(X01[-1], axis=0))
# print(rs)
# input()

# n12 = np.linalg.norm(f[(id1, id2)][kp._vids[(id1, id2)], 0, :], axis=-1)
# n01 = np.linalg.norm(f[(id0, id1)][kp._vids[(id0, id1)], 0, :], axis=-1)
# rs = (np.median(n12) / np.median(n01))**(1.0/1.0)
# print(rs)
# rs_ = rs * rs_
# gs[j] = rs_

kpids = list(range(len(kp0)))
if i == 0 and False:
    ids0 = np.random.choice(kpids, 10, replace=False)
    ids1 = np.random.choice(kpids, 10, replace=False)
    trpt00 = kp0[ids0][:, 0]
    trpt01 = kp0[ids1][:, 0]
    trpt10 = p1[ids0][:, 0]
    trpt11 = p1[ids1][:, 0]
    self._trpt[i] = [(trpt00, trpt01), (trpt10, trpt11)]
    self._rs0[i] = 1.0
elif False:
    trpt00 = self._trpt[i - 1][1][0]
    trpt01 = self._trpt[i - 1][1][1]
    trpts = np.concatenate([trpt00, trpt01], axis=0)
    trpts_, _, _ = cv2.calcOpticalFlowPyrLK(im0, im1, trpts,
                                            None, **self.lk_params)
    # self._trpt[i] = [(trpt00, trpts_[0]), (trpt01, trpts_[1])]
    trpts_0 = np.concatenate([self._trpt[i - 1][0][0],
                              self._trpt[i - 1][0][1]], axis=0)
    trpts_1 = np.concatenate([self._trpt[i - 1][1][0],
                              self._trpt[i - 1][1][1]], axis=0)

    X0 = triangulate_(trpts_0.T, trpts_1.T,
                      np.linalg.inv(self._T0[i - 1]),
                      self.camera_matrix)
    X1 = triangulate_(trpts.T, trpts_.T,
                      np.linalg.inv(T0),
                      self.camera_matrix)

    rss = []
    for i0 in range(len(X0[0])):
        for i1 in range(len(X1[0])):
            if i0 == i1:
                continue
            d0 = np.linalg.norm(X0[:, i0] - X0[:, i1])
            d1 = np.linalg.norm(X1[:, i0] - X1[:, i1])
            rss.append(d1 / (d0 + 1e-10))
    self._rs0[i] = np.median(rss)
    print(self._rs0[i])
    input()

    ids0 = np.random.choice(kpids, 10, replace=False)
    ids1 = np.random.choice(kpids, 10, replace=False)
    trpt00 = kp0[ids0][:, 0]
    trpt01 = kp0[ids1][:, 0]
    trpt10 = p1[ids0][:, 0]
    trpt11 = p1[ids1][:, 0]
    self._trpt[i] = [(trpt00, trpt01), (trpt10, trpt11)]
else:
    self._rs0[i] = 1.0

if False:
    w, h = self.camera_matrix[:2, 2]
    spt = [j for j, p in enumerate(kp0)
           if p[0, 1] > 3 * h // 2
           and np.abs(p[0, 0] - w) < 200]
    spt0 = kp0[spt][:, 0].T  # spt
    spt1 = p1[spt][:, 0].T

    # Ts = np.linalg.inv(T0.copy())
    Ts = T0.copy()
    Ts[:3, 3] /= np.linalg.norm(Ts[:3, 3])

    c_ = np.linalg.inv(self.camera_matrix)
    spt0 = c_[:2, :2] @ spt0 + c_[:2, 2:]
    spt1 = c_[:2, :2] @ spt1 + c_[:2, 2:]

    nt = np.zeros((1, 3))
    nt[0, -1] = 1.0
    nt = (Ts[:3, :3] @ nt.T).T

    H, _ = cv2.findHomography(spt0.T, spt1.T, method=cv2.RANSAC)
    sc = Ts[:3, 3:] @ nt @ np.linalg.inv(H - Ts[:3, :3])
    sgt = np.linalg.norm(Tgt[:3, 3:])
    self._rs0[i] = np.mean(np.abs(sc))

gs[i] = 1.0
for j in range(i + 1, i + baw - 1, 1):
    continue
    # gs[j] = kp._rs0[j]
    # rs_ *= gs[j]
    # continue
    # id0 = j - 1
    # id1 = j
    # id2 = j + 1

    T01 = kp._Tgt[id0].copy()  #
    T12 = kp._Tgt[id1].copy()  #
    T02 = T12 @ T01  #

    # T01 = kp._T0[id0].copy() #
    # T12 = kp._T0[id1].copy() #
    # T02 = kp._Tij0[(id0, id2)].copy() #

    T01[:3, 3:] /= np.linalg.norm(T01[:3, 3])
    T12[:3, 3:] /= np.linalg.norm(T12[:3, 3])
    T02[:3, 3:] /= np.linalg.norm(T02[:3, 3])
    sc = rel_scale_(T01, T12, T02)
    rs_ *= sc
    rec_sc.append(rs_)

if True and False:
    # w, h = self.camera_matrix[:2, 2]
    # spt = [j for j, p in enumerate(kp0)
    #       if p[0, 1] > 3 * h // 2
    #       and np.abs(p[0, 0] - w) < 230
    #       and j in avids]
    # if len(spt) < 8:
    #    spt = [j for j, p in enumerate(kp0)
    #           if p[0, 1] > 3 * h // 2
    #           and np.abs(p[0, 0] - w) < 230]
    ## and np.abs(p[0, 0] - w) < 300
    # spt0 = kp0[avids][:, 0].T # spt
    # spt1 = kp0r[avids][:, 0].T #p1[:][:, 0].T

    # Ts = np.linalg.inv(T0.copy())
    # Ts[:3, 3] /= np.linalg.norm(Ts[:3, 3])
    # Ts = np.eye(4)
    # Ts[0, -1] = 1.0
    # Ts = np.linalg.inv(Ts)
    # sx = triangulate_(spt0, spt1, Ts,
    #                  self.camera_matrix)
    # sx, den = triangulate(spt0, spt1, Ts,
    #                      self.camera_matrix,
    #                      self.camera_matrix @ Ts[:3, 3:])
    # good = [j for j in range(sx.shape[1])
    #        if sx[2, j] < 400
    #        and sx[2, j] > 0.0]
    # and den[j] > 0.05
    # sx = sx[:, good]
    # spt0 = spt0[:, good]

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(elev=90.0, azim=-90.0)
    ax.scatter(sx[0], sx[1], sx[2], marker='.')
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')
    plt.show()

    # c_ = np.linalg.inv(self.camera_matrix)
    # spt0 = c_[:2, :2] @ spt0 + c_[:2, 2:]
    # sc = 1.0 / np.abs(sx[2] * (spt0[1]))
    # sc = np.median(sc) # / np.min(sc)
    # sc2 = np.std(np.abs(sx[2]))
    # if np.isnan(sc):
    #    if i == 0:
    #        self._rs0[i] = 1.0
    #    else:
    #        self._rs0[i] = self._rs0[i - 1]
    # else:
    #    self._rs0[i] = sc
    #    #if i == 0:
    #    #    self._rs0[i] = sc
    #    #elif 0.9 < sc / self._rs0[i - 1] < 1.1:
    #    #    self._rs0[i] = sc
    #    #else:
    #    #    self._rs0[i] = self._rs0[i - 1]

    # sgt = np.linalg.norm(Tgt[:3, 3:])
