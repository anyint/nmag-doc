import nmag
from nmag import SI

mat_Py = nmag.MagMaterial(name="Py",
                          Ms=SI(0.86e6,"A/m"),
                          exchange_coupling=SI(13.0e-12, "J/m"),
                          llg_damping=0.5)

sim = nmag.Simulation("bar")

sim.load_mesh("bar30_30_100.nmesh.h5",
              [("Py", mat_Py)],
              unit_length=SI(1e-9,"m"))

sim.set_m([1,0,1])

dt = SI(5e-12, "s") 

for i in range(0, 61):
    sim.advance_time(dt*i)                  #compute time development

    if i % 10 == 0:			    #every 10 loop iterations, 
        sim.save_data(fields='all')         #save averages and all
                                            #fields spatially resolved
    else:
        sim.save_data()                     #otherwise just save averages

