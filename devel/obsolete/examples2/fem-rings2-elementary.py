#!../bin/nmesh2

import nmesh, math,time, sys
import nfem

nfem.set_default_dimension(2)
nfem.set_default_order(1)

# Simulation parameters

h_x=1.6
h_y=1.2

sigma0=1.0
#alpha=0.01
alpha=-0.1


print
"""
** Example: meshing four rings & solving the laplace equation
   for a space-dependent resistivity that depends on outer parameters

   (Presumably, we will encounter bugs at our first try)
**
"""

##### Creating the mesh #####

# For now, we use a very very simple mesh...

rings = nmesh.union([nmesh.difference(nmesh.ellipsoid([3.0,3.0],
                                                      transform=[("shift",[-2.5,0.0])]),
                                      [nmesh.ellipsoid([1.5,1.5],
                                                       transform=[("shift",[-2.5,0.0])])]),
                     nmesh.difference(nmesh.ellipsoid([3.0,3.0],
                                                      transform=[("shift",[2.5,0.0])]),
                                      [nmesh.ellipsoid([1.5,1.5],
                                                       transform=[("shift",[2.5,0.0])])])])

boxed_rings=nmesh.intersect([rings,nmesh.box([-8.0,-2.5],[8.0,2.5])])

N = 100
density = "density=1.;"

the_mesh = nmesh.mesh(objects = [boxed_rings],
                      cache_name="rings-mesh",
                      a0=0.3,
                      bounding_box=[[-10.0,-3.5],[10.0,3.5]],
                      neigh_force_scale = 1.,
                      density = density,
                      initial_settling_steps = 50,
                      max_relaxation = 4,
                      # callback=(my_function, N),
                      # max_steps=677
                      max_steps=200
                      )

nfem.set_default_mesh(the_mesh)

##### Making the elements... #####

# conductivity (scalar)
element_sigma     = nfem.make_element("sigma",[]);
element_drho_by_dt= nfem.make_element("drho_by_dt",[]);
element_phi       = nfem.make_element("phi",[]);
element_J         = nfem.make_element("J",[2]);

mwe_sigma      = nfem.make_mwe("mwe_sigma",     [(1,element_sigma)])
mwe_drho_by_dt = nfem.make_mwe("mwe_drho_by_dt",[(1,element_drho_by_dt)])
mwe_phi        = nfem.make_mwe("mwe_phi",       [(1,element_phi)])
mwe_J          = nfem.make_mwe("mwe_J",         [(1,element_J)])

diffop_laplace=nfem.diffop("-<d/dxj drho_by_dt|sigma|d/dxj phi>, j:2")
diffop_J=nfem.diffop("<J(k)|sigma|d/dxk phi>, k:2")

# Initial conductivity is spatially constant:

def fun_sigma0(dof_name_indices,position):
    return sigma0

# Later on, we will modify this field:

field_sigma=nfem.make_field(mwe_sigma,fun_sigma0)

# Dirichlet Boundary Conditions on our sample:

def laplace_dbc(coords):
    if(abs(coords[1]) > (2.5-0.05)):
        return 1
    else:
        return 0

def laplace_dbc_values(dof_name_indices,coords):
    if(coords[1] > 0.0):
        return 1.0
    else:
        return -1.0    


cofield_drho_by_dt=nfem.make_cofield(mwe_drho_by_dt)

prematrix_laplace=nfem.prematrix(diffop_laplace,
                                  mwe_drho_by_dt,mwe_phi,
                                  mwe_mid=mwe_sigma)

prematrix_J=nfem.prematrix(diffop_J,
                                   mwe_J,mwe_phi,
                                   mwe_mid=mwe_sigma)

# Note the ignore_jumps parameter:
# we indeed ARE interested just in the
# surface outflow of electrical current!


code_recompute_conductivity="""
double len2_J, sprod_HJ, cos2;
double len2_H=H_x*H_x+H_y*H_y;

len2_J=J(0)*J(0)+J(1)*J(1);
sprod_HJ=H_x*J(0)+H_y*J(1);

cos2=(fabs(len2_J)<1e-8)?0.0:(sprod_HJ*sprod_HJ/(len2_H*len2_J));
sigma = sigma0 + alpha * cos2;
/* printf(\"cos2=%f sigma = %8.6f\\n \",cos2, sigma); */
"""

recompute_conductivity=nfem.site_wise_applicator(parameter_names=["H_x","H_y","sigma0","alpha"],
                                                  # all the names of extra parameters
                                                  code=code_recompute_conductivity,
                                                  field_mwes=[mwe_sigma,mwe_J]
                                                  )

# computing the total current through the sample:

code_integrate_div_J="""
if(coords(1)>2.45)
{
  total_current_up+=drho_by_dt;
}
else if(coords(1)<-2.45)
{
  total_current_down+=drho_by_dt;
}
else
{
  double j=drho_by_dt;

  if(j>0)total_bad_current_plus+=j;
  else   total_bad_current_minus+=j;
}
"""

accumulate_J_total=nfem.site_wise_applicator(parameter_names=["total_current_up",
                                                               "total_current_down",
                                                               "total_bad_current_plus",
                                                               "total_bad_current_minus"
                                                               ],
                                              code=code_integrate_div_J,
                                              position_name="coords",
                                              cofield_mwes=[mwe_drho_by_dt])




def compute_total_current(the_field_sigma):
    laplace_solver=nfem.laplace_solver(prematrix_laplace,
                                        dirichlet_bcs=[(-1,1,laplace_dbc)],
                                        mwe_mid=the_field_sigma)
    compute_div_J=nfem.prematrix_applicator(prematrix_laplace,
                                             field_mid=the_field_sigma)
    field_phi=laplace_solver(cofield_drho_by_dt,
                             dbc_values=laplace_dbc_values)

    cofield_div_J=compute_div_J(field_phi)
    return accumulate_J_total([0.0,0.0,0.0,0.0],cofields=[cofield_div_J])


def update_sigma(the_field_sigma,i):
    compute_J=nfem.prematrix_applicator(prematrix_J,
                                         field_mid=the_field_sigma)
    laplace_solver=nfem.laplace_solver(prematrix_laplace,
                                        dirichlet_bcs=[(-1,1,laplace_dbc)],
                                        mwe_mid=the_field_sigma)
    #
    field_phi = laplace_solver(cofield_drho_by_dt,
                               dbc_values=laplace_dbc_values)
    field_J = nfem.cofield_to_field(compute_J(field_phi))

   

    #print "field_J contents:", nfem.data_doftypes(field_J)
    
    # XXX NOTE: we should be able to make an applicator that does the
    # cofield_to_field conversion automatically!
    #
    #
    # Next, let us compute the new condictivity by site-wise operation on
    # field_J. We just overwrite field_sigma:
    #
    recompute_conductivity([h_x,h_y,sigma0,alpha],fields=[the_field_sigma,field_J])
    print "Refcount field_sigma:",ocaml.sys_refcount(the_field_sigma)
    return the_field_sigma


for i in range(1,5): # was: range(1,5)
    update_sigma(field_sigma,i)
    print "Forcing ocaml GC!"
    sys.stdout.flush()
    ocaml.sys_check_heap()
    print "Iteration ",i," sigma at origin: ",nfem.probe_field(field_sigma,[0.0,0.0])

print "Current: ",compute_total_current(field_sigma)

# nfem.field_print_contents( field_sigma)

print "field_sigma contents:", nfem.data_doftypes(field_sigma)

nfem.plot_scalar_field(field_sigma,"sigma","/tmp/sigma.ps",
                        color_scheme=[(0.9,[0.2,0.2,1.0]),(1.0,[0.2,1.0,0.2]),(1.1,[1.0,1.0,0.2])])
