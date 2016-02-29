from __future__ import division
from warnings import warn

import numpy as np

from revrand.optimize import sgd, decorated_minimize, structured_sgd, logtrick_sgd, Bound, Positive
from revrand.utils import flatten

try:
    import nlopt
    nlopt_test = True
except ImportError:
    warn('NLopt could not be imported, not testing nlopt routines.')
    nlopt_test = False


def test_unbounded(make_quadratic):

    a, b, c, data, _ = make_quadratic
    w0 = np.random.randn(3)

    res = sgd(qobj, w0, data, eval_obj=True, gtol=1e-4, passes=1000, rate=0.95,
              eta=1e-7)
    Ea, Eb, Ec = res['x']
    assert np.allclose((a, b, c), (Ea, Eb, Ec), atol=1e-2, rtol=0)

    res = minimize(qobj, w0, args=(data,), jac=True, method='L-BFGS-B')
    Ea, Eb, Ec = res['x']
    assert np.allclose((a, b, c), (Ea, Eb, Ec), atol=1e-3, rtol=0)

    if nlopt_test:
        res = minimize(qobj, w0, args=(data, False), jac=False,
                       method='LN_BOBYQA', backend='nlopt')
        Ea, Eb, Ec = res['x']
        assert np.allclose((a, b, c), (Ea, Eb, Ec), atol=1e-3, rtol=0)

    res = minimize(qobj, w0, args=(data, False), jac=False, method=None)
    Ea, Eb, Ec = res['x']
    assert np.allclose((a, b, c), (Ea, Eb, Ec), atol=1e-3, rtol=0)


def test_bounded(make_quadratic):

    a, b, c, data, bounds = make_quadratic
    w0 = np.concatenate((np.random.randn(2), [1.5]))

    res = minimize(qobj, w0, args=(data,), jac=True, bounds=bounds,
                   method='L-BFGS-B')
    Ea_bfgs, Eb_bfgs, Ec_bfgs = res['x']

    res = sgd(qobj, w0, data, bounds=bounds, eval_obj=True, gtol=1e-4,
              passes=1000, rate=0.95, eta=1e-6)
    Ea_sgd, Eb_sgd, Ec_sgd = res['x']

    assert np.allclose((Ea_bfgs, Eb_bfgs, Ec_bfgs),
                       (Ea_sgd, Eb_sgd, Ec_sgd),
                       atol=1e-2, rtol=0)

    if nlopt_test:
        res = minimize(qobj, w0, args=(data, False), jac=False, bounds=bounds,
                       method='LN_BOBYQA', backend='nlopt')
        Ea_bq, Eb_bq, Ec_bq = res['x']
        assert np.allclose((Ea_bfgs, Eb_bfgs, Ec_bfgs),
                           (Ea_bq, Eb_bq, Ec_bq), atol=1e-3, rtol=0)


def test_structured_params(make_quadratic):

    a, b, c, data, _ = make_quadratic
    w0 = [np.random.randn(2), np.random.randn(1)[0]]

    nmin = structured_minimizer(minimize)
    res = nmin(qobj_struc, w0, args=(data,), jac=True, bounds=None,
               method='L-BFGS-B')
    (Ea_bfgs, Eb_bfgs), Ec_bfgs = res['x']

    assert np.allclose((Ea_bfgs, Eb_bfgs, Ec_bfgs), (a, b, c), atol=1e-3,
                       rtol=0)

    nsgd = structured_sgd(sgd)
    res = nsgd(qobj_struc, w0, data, bounds=None, eval_obj=True, gtol=1e-4,
               passes=1000, rate=0.95, eta=1e-6)
    (Ea_sgd, Eb_sgd), Ec_sgd = res['x']

    assert np.allclose((Ea_sgd, Eb_sgd, Ec_sgd), (a, b, c), atol=1e-1, rtol=0)

    if nlopt_test:
        res = nmin(qobj_struc, w0, args=(data, False), jac=False, bounds=None,
                   method='LN_BOBYQA', backend='nlopt')
        (Ea_bq, Eb_bq), Ec_bq = res['x']

        assert np.allclose((Ea_bq, Eb_bq, Ec_bq), (a, b, c), atol=1e-3, rtol=0)


def test_log_params(make_quadratic):

    a, b, c, data, _ = make_quadratic
    w0 = np.abs(np.random.randn(3))
    bounds = [Positive(), Bound(), Positive()]

    nmin = logtrick_minimizer(minimize)
    res = nmin(qobj, w0, args=(data,), jac=True, bounds=bounds,
               method='L-BFGS-B')
    Ea_bfgs, Eb_bfgs, Ec_bfgs = res['x']

    assert np.allclose((Ea_bfgs, Eb_bfgs, Ec_bfgs), (a, b, c), atol=1e-3,
                       rtol=0)

    nsgd = logtrick_sgd(sgd)
    res = nsgd(qobj, w0, data, bounds=bounds, eval_obj=True, gtol=1e-4,
               passes=1000, rate=0.95, eta=1e-6)
    Ea_sgd, Eb_sgd, Ec_sgd = res['x']

    assert np.allclose((Ea_sgd, Eb_sgd, Ec_sgd), (a, b, c), atol=1e-1, rtol=0)

    if nlopt_test:
        res = nmin(qobj, w0, args=(data, False), jac=False, bounds=bounds,
                   method='LN_BOBYQA', backend='nlopt')
        Ea_bq, Eb_bq, Ec_bq = res['x']

        assert np.allclose((Ea_bq, Eb_bq, Ec_bq), (a, b, c), atol=1e-3, rtol=0)


def test_logstruc_params(make_quadratic):

    a, b, c, data, _ = make_quadratic
    w0 = [np.abs(np.random.randn(2)), np.abs(np.random.randn(1))[0]]
    bounds = [Positive(shape=(2,)), Bound()]

    res = decorated_minimize(qobj_struc, w0, args=(data,), jac=True,
                             bounds=bounds, method='L-BFGS-B')
    (Ea_bfgs, Eb_bfgs), Ec_bfgs = res['x']

    assert np.allclose((Ea_bfgs, Eb_bfgs, Ec_bfgs), (a, b, c), atol=1e-2,
                       rtol=0)

    nsgd = structured_sgd(logtrick_sgd(sgd))
    res = nsgd(qobj_struc, w0, data, bounds=bounds, eval_obj=True, gtol=1e-4,
               passes=1000, rate=0.95, eta=1e-6)
    (Ea_sgd, Eb_sgd), Ec_sgd = res['x']

    assert np.allclose((Ea_sgd, Eb_sgd, Ec_sgd), (a, b, c), atol=1e-1, rtol=0)

    if nlopt_test:
        res = nmin(qobj_struc, w0, args=(data, False), jac=False, bounds=None,
                   method='LN_BOBYQA', backend='nlopt')
        (Ea_bq, Eb_bq), Ec_bq = res['x']

        assert np.allclose((Ea_bq, Eb_bq, Ec_bq), (a, b, c), atol=1e-3, rtol=0)


def qobj(w, data, grad=True):

    y, x = data[:, 0], data[:, 1]
    N = len(data)
    a, b, c = w

    u = y - (a * x**2 + b * x + c)
    f = (u**2).sum() / N
    df = -2 * np.array([(x**2 * u).sum(), (x * u).sum(), u.sum()]) / N

    if grad:
        return f, df
    else:
        return f


def qobj_struc(w12, w3, data, grad=True):

    return qobj(flatten([w12, w3], returns_shapes=False), data, grad)


if __name__ == "__main__":
    from conftest import make_quadratic
    test_unbounded(make_quadratic())
    test_bounded(make_quadratic())
    test_structured_params(make_quadratic())
    test_log_params(make_quadratic())
    test_logstruc_params(make_quadratic())