import vedo
import vedo.docs as docs
import vedo.utils as utils
import vtk
from vedo.base import Base3DProp

__doc__ = ("Submodule for grouping objects." + docs._defs)

__all__ = ["Assembly", "procrustesAlignment"]


#################################################
def procrustesAlignment(sources, rigid=False):
    """
    Return an ``Assembly`` of aligned source meshes with
    the `Procrustes` algorithm. The output ``Assembly`` is normalized in size.

    `Procrustes` algorithm takes N set of points and aligns them in a least-squares sense
    to their mutual mean. The algorithm is iterated until convergence,
    as the mean must be recomputed after each alignment.

    The set of average points generated by the algorithm can be accessed with
    ``algoutput.info['mean']`` as a numpy array.

    :param bool rigid: if `True` scaling is disabled.

    |align3| |align3.py|_
    """
    from vedo.mesh import Mesh
    group = vtk.vtkMultiBlockDataGroupFilter()
    for source in sources:
        if sources[0].N() != source.N():
            vedo.logger.error("in procrustesAlignment() sources have different nr of points")
            raise RuntimeError()
        group.AddInputData(source.polydata())
    procrustes = vtk.vtkProcrustesAlignmentFilter()
    procrustes.StartFromCentroidOn()
    procrustes.SetInputConnection(group.GetOutputPort())
    if rigid:
        procrustes.GetLandmarkTransform().SetModeToRigidBody()
    procrustes.Update()

    acts = []
    for i, s in enumerate(sources):
        poly = procrustes.GetOutput().GetBlock(i)
        mesh = Mesh(poly)
        mesh.SetProperty(s.GetProperty())
        if hasattr(s, 'name'):
            mesh.name = s.name
            mesh.flagText = s.flagText
        acts.append(mesh)
    assem = Assembly(acts)
    assem.transform = procrustes.GetLandmarkTransform()
    assem.info['mean'] = utils.vtk2numpy(procrustes.GetMeanPoints().GetData())
    return assem


#################################################
class Assembly(vtk.vtkAssembly, Base3DProp):
    """Group many meshes as a single new mesh as a ``vtkAssembly``.

    |gyroscope1| |gyroscope1.py|_
    """

    def __init__(self, *meshs):

        vtk.vtkAssembly.__init__(self)
        Base3DProp.__init__(self)

        if len(meshs) == 1:
            meshs = meshs[0]
        else:
            meshs = utils.flatten(meshs)

        self.actors = meshs

        if len(meshs) and hasattr(meshs[0], "top"):
            self.base = meshs[0].base
            self.top = meshs[0].top
        else:
            self.base = None
            self.top = None

        for a in meshs:
            if a: #and a.GetNumberOfPoints():
                self.AddPart(a)

    def __add__(self, meshs):
        if isinstance(meshs, list):
            for a in meshs:
                self.AddPart(a)
        else:  # meshs=one mesh
            self.AddPart(meshs)
        return self


    def __contains__(self, name):
        """Allows to use ``in`` to check if an object is in the Assembly."""
        return name in self.actors


    def clone(self):
        """Make a clone copy of the object."""
        newlist = []
        for a in self.actors:
            newlist.append(a.clone())
        return Assembly(newlist)


    def unpack(self, i=None):
        """Unpack the list of objects from a ``Assembly``.

        If `i` is given, get `i-th` object from a ``Assembly``.
        Input can be a string, in this case returns the first object
        whose name contains the given string.

        |customIndividualAxes| |customIndividualAxes.py|_
        """
        if i is None:
            return self.actors
        elif isinstance(i, int):
            return self.actors[i]
        elif isinstance(i, str):
            for m in self.actors:
                if i in m.name:
                    return m
        return None


    def lighting(self, style='', ambient=None, diffuse=None,
                 specular=None, specularPower=None, specularColor=None):
        """Set the lighting type to all ``Mesh`` in the ``Assembly`` object.

        :param str style: preset style, can be `[metallic, plastic, shiny, glossy]`
        :param float ambient: ambient fraction of emission [0-1]
        :param float diffuse: emission of diffused light in fraction [0-1]
        :param float specular: fraction of reflected light [0-1]
        :param float specularPower: precision of reflection [1-100]
        :param color specularColor: color that is being reflected by the surface
        """
        for a in self.actors:
            a.lighting(style, ambient, diffuse,
                       specular, specularPower, specularColor)
        return self
