import utils
import psiFour
import json
import copy
import minifold
import math
import random
import sys

class Initializer():

    def __init__(self, psi4_path, input_file_energies_psi4, output_file_energies_psi4, energy_method, precalculated_energies_path, model_path, window_size, max_aa_length, initialization_option):

        ## PARAMETERS ##

        self.model_path = model_path
        self.window_size = window_size
        self.max_aa_length = max_aa_length
        self.initialization_option = initialization_option
        self.precalculated_energies_path = precalculated_energies_path

        #Declare the instances to use the functions of these classes
        self.psi = psiFour.PsiFour(psi4_path, input_file_energies_psi4, output_file_energies_psi4, precalculated_energies_path, energy_method)
        self.tools = utils.Utils()

        #HARDCODED. It is assumed that all aminoacids has the nitro and carboxy conexions like that
        #TODO: To study if it is necessary to generalize this assumption
        self.nitroConnections = [['C', 2]]
        self.carboxyConnections = [['C', 1], ['O', 2]]

        #It contains the energy of each angle combination
        self.anglesEnergy = []

    #Calculate all posible energies for the protein and the number of rotations given
    def calculateEnergies(self, proteinName, numberBitsRotation, aminoacids):

        #Get all atoms from the protein with x/y/z positions and connections
        atoms = self.extractAtoms(proteinName)

        #Identify the nitro and carboxy atoms
        nitroAtom = self.findAtom(atoms, 'N', '', self.nitroConnections)
        carboxyAtom = self.findAtom(atoms, '', 'Carboxy', self.carboxyConnections)

        #Get initial structure of the protein to rotate from it
        atoms = self.calculateInitialStructure(atoms, aminoacids, nitroAtom, carboxyAtom)

        #Calculate all posible energies for the phi and psi angles
        energiesJson = self.calculateAllEnergiesOfRotations(atoms, nitroAtom, carboxyAtom, proteinName, numberBitsRotation)

        self.writeFileEnergies(energiesJson, proteinName, numberBitsRotation)

    #Get the atoms (and the properties) of a protein
    def extractAtoms(self, proteinName):

        #call psi4 to get the atoms of the protein
        atoms = self.psi.getAtomsFromProtein(proteinName)

        #Calculate the connection between atoms
        atoms = self.tools.calculateAtomConnection(atoms)

        return atoms

    #Find the atom that satisfies the parameters
    def findAtom(self, atoms, element, cType, connections):

        #Search in the whole atom list
        for at in atoms:

            #The element for the angle phi is nitrogen (N)
            if ((element != '' and at.element == element) or (cType != '' and at.c_type == cType)):

                #Check all the atom connections
                for conn in connections:

                    linkedElement = conn[0]
                    numberLinkedElements = conn[1]
                    counterLinkedElements = 0

                    #The valid nitrogen is the connected with two carbons
                    for elementConn in at.linked_to:

                        if(elementConn.element == linkedElement):
                            counterLinkedElements += 1

                    #Atom found and saved in variable
                    if (counterLinkedElements == numberLinkedElements):
                        return at

                    else:
                        raise Exception('Element '+at.element+' not found with the proper connections of '+linkedElement+'! '+str(counterLinkedElements)+' found but there should be ' + str(numberLinkedElements))

    def calculateInitialStructure(self, atoms, aminoacids, nitro_atom, carboxy_atom):       
    
        #Set angles to 0. PSI4 returns the optimal angles for the protein, so it is necessary to set these angles to 0
        #Get the value of angles returned by psi4
        phi_angle_psi4 = self.tools.calculateAngle(atoms[8], atoms[5], atoms[3], atoms[6], 'phi')
        psi_angle_psi4 = self.tools.calculateAngle(atoms[4], atoms[7], atoms[6], atoms[3], 'psi')


        #Rotate the inverse (*-1) angles of psi4 to get angles to 0
        self.tools.rotate('phi', -phi_angle_psi4, nitro_atom) 
        self.tools.rotate('psi', -psi_angle_psi4, carboxy_atom)

        #Apply the calculated rotations for the angles
        phi_initial_rotation = 0
        psi_initial_rotation = 0

        #random between -π and π
        if self.initialization_option == 'random':
            phi_initial_rotation = random.uniform(-math.pi, math.pi)
            psi_initial_rotation = random.uniform(-math.pi, math.pi)

        #minifold
        elif self.initialization_option == 'minifold':

            mfold = minifold.Minifold(self.model_path, self.window_size, self.max_aa_length)
            angles = mfold.predictAngles(aminoacids)
            phi_initial_rotation = angles[0][0]
            psi_initial_rotation = angles[0][1]

        #Rotate the inverse angles of psi4 to get angles to 0
        self.tools.rotate('phi', -phi_initial_rotation, nitro_atom) 
        self.tools.rotate('psi', -psi_initial_rotation, carboxy_atom)


        #Calculate the precision in constrast of the real value calculated by psi4
        self.tools.calculatePrecisionOfAngles(phi_angle_psi4, psi_angle_psi4, phi_initial_rotation, psi_initial_rotation)
        return atoms

    #This method returns the json with all rotations and energies associated to these rotations
    def calculateAllEnergiesOfRotations(self, atoms, nitroAtom, carboxyAtom, proteinName, numberBitsRotation):

        rotationSteps = pow(2, int(numberBitsRotation))

        #Get the size of each step to rotate
        anglePhi = 1/rotationSteps
        anglePsi = 1/rotationSteps

        #Write the headers of the energies json that is going to be returned
        energiesJson = {}
        energiesJson['protein'] = proteinName
        energiesJson['numberBitsRotation'] = numberBitsRotation
        energiesJson['initialPhiAngle'] = self.tools.calculateAngle(atoms[8], atoms[5], atoms[3], atoms[6], 'phi')
        energiesJson['initialPsiAngle'] = self.tools.calculateAngle(atoms[4], atoms[7], atoms[6], atoms[3], 'psi')
        energiesJson['energies'] = []

        #These two nested loops are hardcoded (it could be n nested loops, 1 per AA) because QFold is going to be used just with two and three aminoacids
        #if it is scale to more aminoacids, it should be necessary to implement a recursive function
        #TODO: To study how to generalize to any number of aminoacids
        for x in range(0, rotationSteps):

            for y in range(0, rotationSteps):

                #Perform the rotations over a copy
                copied_atoms = copy.deepcopy(atoms)
                copied_nitroAtom = self.findAtom(copied_atoms, 'N', '', self.nitroConnections)
                copied_carboxyAtom = self.findAtom(copied_atoms, '', 'Carboxy', self.carboxyConnections)

                #Always rotate from state (0,0)
                self.tools.rotate('phi', x * 2*math.pi * anglePhi, copied_nitroAtom) 
                self.tools.rotate('psi', y * 2*math.pi * anglePsi, copied_carboxyAtom)
                
                #Calculate the energy of the protein structure after the previous rotations
                energy = self.calculateEnergyOfRotation(copied_atoms)

                #Normalize the energy
                normalizedEnergy = energy*-1
                normalizedEnergy = "%.6f" % normalizedEnergy

                #Add the angles to list with angles and energies
                self.anglesEnergy.append([anglePhi, anglePsi, normalizedEnergy])

                #Add the values to the file with the precalculated energies
                energiesJson['energies'].append({
                    'phi': x,
                    'psi': y,
                    'energy': energy,
                })

                # We eliminate previous copies
                del copied_atoms
                del copied_carboxyAtom
                del copied_nitroAtom

                #Increment the angle psi counter INSIDE the SECOND loop
                anglePsi += 1/rotationSteps

            #Increment the angle psi counter INSIDE the FIRST loop (OUTSIDE the SECOND)
            anglePhi += 1/rotationSteps

        return energiesJson

    def calculateEnergyOfRotation(self, copied_atoms):

        #Write the file with the actual rotations
        self.psi.writeFileEnergies(copied_atoms)

        #Calculate the energy of the actual rotations using PSI4
        self.psi.executePsiCommand()

        #Read the PSI4 output file and get the energy
        energy = self.psi.readEnergyFromFile()

        return energy

    def writeFileEnergies(self, energiesJson, proteinName, numberBitsRotation):

        #Create json with calculated energies
        #TODO: extract the path to a config file
        with open(self.precalculated_energies_path+'energies_'+proteinName+'_'+str(numberBitsRotation)+'.json', 'w') as outfile:
            json.dump(energiesJson, outfile)
