import os
from struct import pack_into
from utils import infix_to_prefix

# Manual: https://picture.iczhiku.com/resource/eetop/shIGapEosdWkLCxn.pdf

class SDE_generator():
    """ Base class to write the .cmd file.

    It has methods to write scheme commands for the main commands that we use, both for 3D and 2D simulations.
    It is mostly tailored to our needs (basically writing squares or cuboids and that's pretty much it),
    although it can be extended if it gains traction.
    """

    def __init__(self, filename='sde_dvs.cmd', path='./', sim_type='2D', overwrite=False, comment=True):
        """
        Initializes the writer.
        :param filename: name of the cmd file to be created
        :param path: path where we create the file
        :param sym_type: either '2D' or '3D', indicates dimenions of the simulation
        :param overwrite: if False, it will throw an error if the file already exists
        :param comment: if True, it will comments to the sde file make it easier to follow
        """

        self.filename = filename
        self.path = path
        self.sim_type = sim_type
        self.comment = comment

        if os.path.exists(os.path.join(path, filename)) and not overwrite:
            # The file already exists. Throw an error
            raise FileExistsError('There is already a file with the specified name in the specifed path')

        # Open the file we will write
        self.file = open(os.path.join(path, filename), "w")

    ######################### GENERIC #########################

    def postamble(self):
        # Clause to generate the mesh
        if self.comment:
            self.write("; Generate the mesh")
        self.write('(sde:build-mesh "snmesh" "" "n@node@")')

        # Close the file handle
        self.file.close()

    def write(self, expression, newline=True):
        """
        Simply writes a scheme expression to the current end of file, adn adds an newline

        :param expression: string with the exoression to write
        :param newline: if True, it adds a newline at the end of the expression
        """

        if expression == "\n":
            newline = False

        if newline:
            expression = expression + "\n"

        self.file.write(expression)

    def preamble(self, clear=True, default_boolean="ABA"):
        """ Writes the preamble of the sde file.

        :param clear: if True, adds the clause to clear any existing structure
        :param default_boolean: sets the default boolean behavior. Options:
            "ABA": subtracts all overlapping regions from the existing regions
            "AB": newly created regions are merged (united) automatically with
                all existing overlapping regions
            "BAB": subtracts all existing regions from the newly created regions
            "ABiA": similar to the "ABA" behavior, except that the overlaps are
                separate regions (with the DATEX material inherited from the new regions).
            "ABiB": similar to "ABiA", except that the overlap regions inherit the DATEX material
                from the existing regions
            "XX": allows the creation of overlapping regions. In this case, you must modify the model
                by explicitly deleting the overlapping parts, 
        """

        if self.comment:
            # Initial comments
            self.write("; SDE file created by pysde_sentaurus.")
            self.write("; The sde file is the file that constructs the structure to be simulated.")
            self.write("; This includes defining the regions, its doping and the mesh.")
            self.write("\n")
            self.write("; ******************")
            self.write("; INITIAL SETUP")
            self.write("\n")

        if clear:
            if self.comment:
                self.write('(sde:clear) ; clear any existing structure')
            else:
                self.write('(sde:clear)')

        if default_boolean not in ["AB", "ABA", "BAB", "ABiA", "ABiB", "XX"]:
            raise ValueError('Indicated default boolean not recognized')
        self.write('(sdegeo:set-default-boolean "%s")' % default_boolean)
        self.write("\n")

    def write_if_clause(self, condition, statements_true, statements_false=None, write_to_file=True):
        """ Writes an if clause in scheme.

        :param condition: string with the condition to test (Ex: 'is_T_spoke = 1')
        :param statements_true: statements to evaluate if the condition is True
        :param statements_false: statements to evaluate if the condition is False (can be None and then we do nothing in case of False)
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
        """

        cond = infix_to_prefix(condition)

        statements = "(if (%s) \n (begin \n %s \n ) \n" % (cond, statements_true)

        if statements_false is not None:
            statements = statements + " (begin \n %s \n ) \n" % statements_false
        
        statements = statements + ") \n"

        if write_to_file:
            self.write(statements)
            return None
        else:
            return statements

    def _point_to_str(self, point):
        """ Converts a point to a string.
        """

        if self.sim_type == '2D':
                point = (point[0], point[1], 0)

        p = [0, 0, 0]
        for i in range(len(point)):
            if isinstance(point[i], str):
                p[i] = infix_to_prefix(point[i])
            else:
                p[i] = format(point[i], '.3e')
        
        p_str = '(%s) (%s) (%s)' % (p[0], p[1], p[2])

        return p_str    
    
    ######################### VARIABLES #########################

    def workbench_variables(self, vars, write_to_file=True):
        """ Instantiates the variables specified in the sentaurus workbench.

        :param vars: list of strings with the names of the variables in the sentaurus workbench
            Example: ["is_T_spoke", "inner_p"]
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
            If write_to_file is False, the string does not contain comments.
        """

        if self.comment and write_to_file:
            self.write("; ******************")
            self.write("; PARAMETER DEFINITION")
            self.write("\n")
            self.write("; We can directly specify variables from the script or take them from the Sentaurus Workbench.")
            self.write("; NOTE: length variables are in um by default in Sentaurus.")
            self.write("\n")
            self.write("; 1. Specify a given variable from the Sentaurus Workbench. This has the advantage that we can very easily do parameter sweeps.")
            self.write("; ---------------------------------------------")
            self.write("\n")

        statements = ""
        for var in vars:
            statements = statements + "(define %s @%s@) \n" % (var, var)

        if write_to_file:
            self.write(statements)
            return None
        else:
            return statements

    def script_variables(self, var_dict, write_to_file=True):
        """ Defines variables manually. 

        :param var_dict: dictionnary with the name of the variable as a key and its value as the value.
            Example: {"w_spoke": 0.5, "outer_spoke_l": 1.7}
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
        """

        if self.comment and write_to_file:

            self.write("; 2. Specify a variable from the script")
            self.write("; -------------------------------------")
            self.write("\n")

        statements = ""

        for var_name, var_val in var_dict.items():
            statements = statements + "(define %s %.5e) \n" % (var_name, var_val)

        if write_to_file:
            self.write(statements)
            return None
        else:
            return statements

    ######################### DOPINGS #########################

    def constant_doping(self, doping_types, region_doping, p_dopant="BoronActiveConcentration", n_dopant="PhosphorusActiveConcentration",
        write_to_file=True):
        """ Writes the doping section. Only constant dopings are supported for now.

        It defines doping species, doping concentrations, and doping regions.
        :param doping_types: dictionary with the name of the doping type as the key and as value a tuple with (doping_type, doping_concentration)
            Doping type is either "p" or "n", doping concentration is the concentration in cm^-3.
            Example: {"P_doping": ("p", 1e18), "N++_doping": ("n", 1e20)}
            Note that the doping concentration can also be a variable name if it was previously defined. EX: ("p", "mid_doping"),
            where "mid_doping" has been defined in either self.script_variables or self.workbench_variables.
        :param region_doping: dictionary with the region name as the key and as value the doping type assigned.
            Example: {"middle_spoke": "P_doping", "outer_spoke": "N++_doping"}
        :param p_dopant: type of p dopant. For Si, available is either "BoronActiveConcentration"
        :param n_dopant: type of n dopant. For Si, available is either "PhosphorusActiveConcentration" or "ArsenicActiveConcentration"
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
        """

        if self.comment and write_to_file:
            self.write("; ******************")
            self.write("; DOPINGS")
            self.write("Specify the doping species and doping concentration for each region.")
            self.write("\n")
            self.write("; Step 1: generate all the different doping types existing in the structure")
            self.write("; -------------------------------------------------------------------------")
        
        statements = ""
        statements = statements + self._constant_doping_definitions(doping_types, p_dopant, n_dopant)
        statements = statements + "\n"

        if self.comment and write_to_file:

            self.write("; Step 2: assign the doping layers to the different regions")
            self.write("; ----------------------------------------------------------")

        statements = statements + self._doping_assignments(region_doping, doping_types)
        statements = statements + "\n"
        
        if write_to_file:
            self.write(statements)
            return None
        else:
            return statements

    def _constant_doping_definitions(self, doping_types, p_dopant="BoronActiveConcentration", n_dopant="PhosphorusActiveConcentration"):
        """ Generates the statements for the doping definitions
        :param doping_types: dictionary with the name of the doping type as the key and as value a tuple with (doping_type, doping_concentration)
            Doping type is either "p" or "n", doping concentration is the concentration in cm^-3.
            Example: {"P_doping": ("p", 1e18), "N++_doping": ("n", 1e20)}
            Note that the doping concentration can also be a variable name if it was previously defined. EX: ("p", "mid_doping"),
            where "mid_doping" has been defined in either self.script_variables or self.workbench_variables.
        :param p_dopant: type of p dopant. For Si, available is either "BoronActiveConcentration"
        :param n_dopant: type of n dopant. For Si, available is either "PhosphorusActiveConcentration" or "ArsenicActiveConcentration"
        """
        statements = ""

        self.doping_types = doping_types
        for dop_name, dop_desc in doping_types.items():
            dop_type, dop_conc = dop_desc
            dopant = p_dopant if dop_type == 'p' else n_dopant
            
            if not isinstance(dop_conc, str):
                dop_conc = format(dop_conc, '.3e')
            statements = statements + '(sdedr:define-constant-profile "%s"  %s %s) \n' % (dop_name, dopant, dop_conc)
        return statements

    def _doping_assignments(self, region_doping):
        """ Generates the assignments for assignment of dopings to regions.

        :param region_doping: dictionary with the region name as the key and as value the doping type assigned.
            Example: {"middle_spoke": "P_doping", "outer_spoke": "N++_doping"}
        """

        statements = ""
        for region, dop_type in region_doping.items():
            if dop_type not in self.doping_types:
                raise ValueError('The specified doping type %s is not defined' % dop_type)
            statements = statements + '(sdedr:define-constant-profile-region "%s" "%s" "%s") \n' % (region[:-1], dop_type, region)

        return statements

    ######################### GEOMETRIC STRUCTURES #########################

    def create_rectangle(self, p1, p2, material, region_name, write_to_file=True):
        """ Writes the command to create a rectangular shape.
        This is an actual rectangle in a 2D simulation or a cuboid in a 3D simulation.

        :param p1: vertex 1 of the rectangle, a tuple of 2 elements (in a 2D simulation) or 3 elements
            (in a 3D simulation). The elements can either be a number or a string with a variable or an operation.
            Example: (0, "(outer_spoke_l + 0.5)/2")
        :param p2: vertex 2 of the rectangle, a tuple of 2 elements (in a 2D simulation) or 3 elements
            (in a 3D simulation). The elements can either be a number or a string with a variable or an operation.
            Example: (0, "(outer_spoke_l + 0.5)/2")
        :param material: Relevant materials are "Silicon", "Aluminum", "SiO2", "Si3N4", "PolySi".
        :param region_name: string with the name of the region being created
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
        """

        p1_str = self._point_to_str(p1)
        p2_str = self._point_to_str(p2)

        if self.sim_type == "2D":
            statement = '(sdegeo:create-rectangle (position %s) (position %s) "%s" "%s")' % (p1_str, p2_str, material, region_name)
        else:
            statement = '(sdegeo:create-cuboid (position %s) (position %s) "%s" "%s")' % (p1_str, p2_str, material, region_name)

        if write_to_file:
            self.write(statement)
            return None
        else:
            return statement

    def create_regular_polygon(self, center_pos, radius, n_faces, start_angle, material, region_name, write_to_file=True):
        """ Writes the command to create a regular polygon with a given radius and number of sides.

        :param center_pos: Position of the center of the regular polygon. A tuple of 2 elements (in a 2D simulation) or 3 elements
            (in a 3D simulation). The elements can either be a number or a string with a variable or an operation.
            Example: (0, "(outer_spoke_l + 0.5)/2")
        :param radius: The radius of the circle that defines the vertex points
        :param n_faces: Number of faces (ex: 3 makes a trinagle, 4 makes a square, 5 makes a pentagon...)
        :param start_angle: Angle [degree], counterclockwise from the x-axis, which defines the ‘rotation’ of the regular polygon.
        :param material: Relevant materials are "Silicon", "Aluminum", "SiO2", "Si3N4", "PolySi".
        :param region_name: string with the name of the region being created
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
        """

        p_str = self._point_to_str(center_pos)

        statement = '(sdegeo:create-reg-polygon (position %s) %.3e %d %.3e "%s" "%s")' % (p_str, radius, n_faces, start_angle, material, region_name)

        if write_to_file:
            self.write(statement)
            return None
        else:
            return statement

    def create_2D_polygon(self, point_list, material, region_name, write_to_file=True):
        """ Writes the command to create a 2D polygon.

        :param point list: list of tuples with the polygon points. It has to start an end with the same point.
            Each point is a tuple of 2 elements (in a 2D simulation) or 3 elements
            (in a 3D simulation). The elements can either be a number or a string with a variable or an operation.
            Example: (0, "(outer_spoke_l + 0.5)/2")
        :param material: Relevant materials are "Silicon", "Aluminum", "SiO2", "Si3N4", "PolySi".
        :param region_name: string with the name of the region being created
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
        """

        points_str = ""

        for p in point_list:
            p_str = self._point_to_str(p)
            points_str = points_str + " (position %s) " % p_str

        statement = '(sdegeo:create-polygon (list %s) "%s" "%s")' % (points_str, material, region_name)
  
        if write_to_file:
            self.write(statement)
            return None
        else:
            return statement

    def create_circle(self, center_pos, radius, material, region_name, write_to_file=True):
        """ Writes the command to create a circle (or sphere in 3D) with a given radius.

        :param center_pos: Position of the center of the regular polygon. A tuple of 2 elements (in a 2D simulation) or 3 elements
            (in a 3D simulation). The elements can either be a number or a string with a variable or an operation.
            Example: (0, "(outer_spoke_l + 0.5)/2")
        :param radius: The radius of the circle that defines the vertex points
        :param material: Relevant materials are "Silicon", "Aluminum", "SiO2", "Si3N4", "PolySi".
        :param region_name: string with the name of the region being created
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
        """

        p_str = self._point_to_str(center_pos)

        if self.sim_type == '2D':
            statement = '(sdegeo:create-circular-sheet (position %s) %.3e "%s" "%s")' % (p_str, radius, material, region_name)
        else:
            statement = '(sdegeo:create-sphere (position %s) %.3e "%s" "%s")' % (p_str, radius, material, region_name)

        if write_to_file:
            self.write(statement)
            return None
        else:
            return statement

    ######################### CONTACTS #########################

    def create_vertex(self, pos, write_to_file=True):
        """ Creates a vertex at the specified position.

        This is useful for defining contacts. A vertex splits an exisitng line into two so that they
        can be assigned different contacts.

        :param pos: Position of the vertex, a tuple of 2 elements (in a 2D simulation) or 3 elements
            (in a 3D simulation). The elements can either be a number or a string with a variable or an operation.
            Example: (0, "(outer_spoke_l + 0.5)/2")
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
        """

        p_str = self._point_to_str(pos)

        statement = "(sdegeo:insert-vertex (position %s))" % p_str

        if write_to_file:
            self.write(statement)
            return None
        else:
            return statement

    def contacts(self, contact_dict, write_to_file=True):
        """ Generates the statements to define the contacts.

        :param contact_dict: dictionary with the name of the contact as the key and as value a 2 or 3 element tuple
            indicating the position of the edge (2D simulation) or face (3D simulation) where the contact is located.
            This is necessary because we use the find-face-id or find-edge-id to define the edge/face of the contact.
            Ex: {'middle_contact': (0, 'long_contact_l + l_metal')}
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
        """

        statements = ""

        if self.comment and write_to_file:
            statements = statements + "; ******************\n"
            statements = statements + "; DEFINE THE CONTACTS\n"

        for contact_name, contact_point in contact_dict.items():

            statements = statements + '(sdegeo:define-contact-set "%s" 4 (color:rgb 1 0 0) "##") \n' % contact_name  
                # The 4 sets the thickness of the line
            statements = statements + '(sdegeo:set-current-contact-set "%s") \n'  % contact_name

            p_str = self._point_to_str(contact_point)

            if self.sim_type == '2D':
                statements = statements + '(sdegeo:define-2d-contact (find-edge-id (position %s) "%s") \n\n' % (p_str, contact_name)

            else:
                statements = statements + '(sdegeo:set-contact-faces (find-face-id (position %s) "%s") \n\n' % (p_str, contact_name)

        if write_to_file:
            self.write(statements)
            return None
        else:
            return statements

    ######################### MESHING #########################

    def rectangular_mesh(self, name, p1, p2, sizes, refinements, write_to_file=True):
        """ Defines a rectangular mesh with the given name, placement and refinements.
        
        Notice that multiple meshes can be defined by repeated calls to this function.

        :param name: name for the mesh
        :param p1: first corner of the rectangle/cuboid where the mesh is applied.
        :param p2: second coner of the rectangle/cuboid where the mesh is applied.
        :param sizes: list with max and min mesh sizes (xmax xmin ymax ymin) or (xmax xmin ymax ymin zmax zmin)
        :param refinements: list of lists, where each list contains all the elements needed to describe the refinement.
            Ex: [["MaxLenInt", "Silicon", "Aluminum", 0.001, 1.4, "DoubleSide"], ["DopingConcentration",  "MaxTransDiff",  1]]
            This will define two refinement functions.
        :param write_to_file: if True, it writes the satements to the file. If False, it just returns the statements.
        """
        
        statements = ""

        if self.comment and write_to_file:
            statements = statements + "; ******************\n"
            statements = statements + "; MESHING \n\n"
        
        # Define the region
        p1_str = self._point_to_str(p1)
        p2_str = self._point_to_str(p2)

        if self.sim_type == '2D':
            statements = statements + '(sdedr:define-refinement-window  "RefWin.%s"  "Rectangle"  (position %s) (position %s)) \n\n' % (name, p1_str, p2_str)
        else:
            statements = statements + '(sdedr:define-refinement-window  "RefWin.%s"  "Cuboid"  (position %s) (position %s)) \n\n' % (name, p1_str, p2_str)

        # Specify max and min lengths
        if self.sim_type == '2D':
            max_min_str = "%.3e %.3e %.3e %.3e" % (sizes[0], sizes[2], sizes[1], sizes[3])  # xmax ymax xmin ymin
        else:
            max_min_str = "%.3e %.3e %.3e %.3e %.3e %.3e" % (sizes[0], sizes[2], sizes[4], sizes[1], sizes[3], sizes[5])  # xmax ymax zmax xmin ymin zmin

        statements = statements + '(sdedr:define-refinement-size "RefDef.%s" %s) \n\n' % (name, max_min_str)

        # Now write the refinements
        for refinement in refinements:
            statements = statements + '(sdedr:define-refinement-function "RefDef.%s" ' % name
            for ref_param in refinement:
                if isinstance(ref_param, str):
                    statements = statements + '"%s" ' % ref_param
                else:
                    statements = statements + '%.2e ' % ref_param
            
            statements = statements + ') \n\n'

        # Finally, actually apply the mesh
        statements = statements + '(sdedr:define-refinement-placement  "PlaceRF.%s"  "RefDef.%s"  "RefWin.%s") \n\n' % (name, name, name)

        if write_to_file:
            self.write(statements)
            return None
        else:
            return statements

    

    






    

    



