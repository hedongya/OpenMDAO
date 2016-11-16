"""Temporary run file for the test components."""
from __future__ import division, print_function
import numpy

from six import iteritems
from six.moves import range
from collections import OrderedDict

import itertools
import unittest

from openmdao.api import Problem
from openmdao.test_suite.components.implicit_components \
    import TestImplCompNondLinear
from openmdao.test_suite.components.explicit_components \
    import TestExplCompNondLinear
from openmdao.test_suite.groups.group import TestGroupFlat
from openmdao.api import DefaultVector, NewtonSolver, ScipyIterativeSolver
from openmdao.api import DenseJacobian
from openmdao.parallel_api import PETScVector


class CompTestCase(unittest.TestCase):

    def test_comps(self):
        for key in itertools.product(
                [TestImplCompNondLinear, TestExplCompNondLinear],
                [DefaultVector, PETScVector],
                ['implicit', 'explicit'],
                ['matvec', 'dense'],
                range(1, 3),
                range(1, 3),
                [(1,), (2,), (2, 1), (1, 2)],
                ):
            Component = key[0]
            Vector = key[1]
            connection_type = key[2]
            derivatives = key[3]
            num_var = key[4]
            num_sub = key[5]
            var_shape = key[6]

            print_str = ('%s %s %s %s %i vars %i subs %s' % (
                Component.__name__,
                Vector.__name__,
                connection_type,
                derivatives,
                num_var, num_sub,
                str(var_shape),
            ))

            # print(print_str)

            group = TestGroupFlat(num_sub=num_sub, num_var=num_var,
                                  var_shape=var_shape,
                                  connection_type=connection_type,
                                  derivatives=derivatives,
                                  Component=Component,
                                  )
            prob = Problem(group).setup(Vector)
            prob.root.nl_solver = NewtonSolver(
                subsolvers={'linear': ScipyIterativeSolver(
                    ilimit=100,
                )}
            )
            if derivatives == 'dense':
                prob.root.jacobian = DenseJacobian()
            prob.root.setup_jacobians()
            prob.root.suppress_solver_output = True
            fail, rele, abse = prob.run()
            # if derivatives == 'dense':
            #     print('mtx:', prob.root.jacobian._int_mtx)
            #     print('')
            if fail:
                self.fail('re %f ; ae %f ;  ' % (rele, abse) + print_str)

            if Component == TestImplCompNondLinear and derivatives == 'dense':
                size = numpy.prod(var_shape)
                work = prob.root._vectors['output']['']._clone()
                work.set_const(1.0)
                prob.root._vectors['output'][''].set_const(1.0)
                prob.root._apply_linear([''], 'fwd')
                val = 1 - 0.01 + 0.01 * size * num_var * num_sub
                # print(prob.root._vectors['residual'][''].get_data())
                # print(work.get_data())
                # print(val)
                prob.root._vectors['residual'][''].add_scal_vec(-val, work)
                # print(prob.root._vectors['residual'][''].get_data())
                # print('')
                self.assertEqual(
                    prob.root._vectors['residual'][''].get_norm(), 0)

            if Component == TestExplCompNondLinear and derivatives == 'dense':
                size = numpy.prod(var_shape)
                work = prob.root._vectors['output']['']._clone()
                work.set_const(1.0)
                prob.root._vectors['output'][''].set_const(1.0)
                prob.root._apply_linear([''], 'fwd')
                val = 1 - 0.01 * size * num_var * (num_sub - 1)
                # print(prob.root._vectors['residual'][''].get_data())
                # print(work.get_data())
                # print(val)
                prob.root._vectors['residual'][''].add_scal_vec(-val, work)
                # print(prob.root._vectors['residual'][''].get_data())
                # print('')
                self.assertEqual(
                    prob.root._vectors['residual'][''].get_norm(), 0)




if __name__ == '__main__':
    unittest.main()