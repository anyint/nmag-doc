
import nmag1 as mag, nmesh as nm, sys
import math

import time

# Note: we should make a habit of always starting out by defining
# the additional intensive parameters of our model.

#This adds a Zeeman field:
PermAlloy=mag.MagMaterial("Funny",extra_H="""
h_total_Funny[0] += H_x;
h_total_Funny[1] += H_y;
h_total_Funny[2] += H_z;
""")

mag.set_default_material(PermAlloy)



mag.set_intensive_parameters(["T","p","H_x","H_y","H_z"])

mag.defregion("Ball 1",nm.ellipsoid([3.0,3.0,3.0],transform=[("shift",[-3.0,0.0,0.0])]))

print "OK 1"
sys.stdout.flush()

mag.defregion("Ball 2",nm.ellipsoid([3.0,3.0,3.0],transform=[("shift",[3.0,0.0,0.0])]))

# Note: clearly, we DO need a better way to specify geometries. Ideally, I would like to be
# able to write instead:
#
# mag.defregion("Ball 1",nm.shifted([-3,0,0],nm.sphere(3)))
# mag.defregion("Ball 2",nm.shifted([ 3,0,0],nm.sphere(3)))
#
# or alternatively:
#
# sphere = nm.sphere(3)
# mag.defregion("Ball 1",nm.shifted([-3,0,0],sphere))
# mag.defregion("Ball 2",nm.shifted([ 3,0,0],sphere))


mag.set_meshing_parameters(cache_name="two-balls")

mag.create_mesh()

def initial_M(dof_name,coords):
    dir=dof_name[1][0]
    if dir==0:
        return math.cos(coords[0])
    elif dir==1:
        return math.sin(coords[0])
    else: return 0
    
mag.set_magnetization([1.0,0.0,0.0]) # may also provide a function here!

#mag.set_magnetization(initial_M) # may also provide a function here!

# NOTE: set_magnetization should also be able
# to take just a constant vector as an argument.

print "Total magnetization: ", mag.integrate()

f=open("data.dat","w")

# XXXDDDXXXDDD
for n in range(1,5000):
    #Here we set Hy to 1.0
    print "T=",mag.default_simulation_context.timestepper.advance_time([0.0,0.0,0.0,1.0,0.0])
    # this needs the intensive params!
    M=mag.integrate()[0][1]
    print "Total magnetization: ", M
    Mx,My,Mz=M
    f.write("%d %f %f %f\n" % (n,Mx,My,Mz))
f.close()
#generate some plots
import os
os.system("xmgrace -block data.dat -bxy 1:2 -printfile Mxoft.eps -hardcopy")
os.system("xmgrace -block data.dat -bxy 1:3 -printfile Myoft.eps -hardcopy")
os.system("xmgrace -block data.dat -bxy 1:4 -printfile Mzoft.eps -hardcopy")
os.system("xmgrace -block data.dat -bxy 2:4 -printfile MxofMz.eps -hardcopy")

time.sleep(1000) # so we do not lose the dynamically generated C code...

