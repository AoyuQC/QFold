import numpy as np
import matplotlib.pyplot as plt
import utils
import copy
import math

class Metropolis():

    ## TODO: generalise to more than 2 angles

    def __init__(self, bits_rotation, n_iterations, number_angles, scaling_factor, deltas_dict):

        self.bits_rotation = bits_rotation
        self.n_iterations = n_iterations
        self.scaling_factor = scaling_factor 
        self.deltas_dict = deltas_dict
        self.number_angles = int(number_angles)

        self.rotatition_steps = 2**self.bits_rotation
        self.bits_number_angles = math.ceil(np.log2(number_angles))

        self.tools = utils.Utils()

    def execute_metropolis(self):

        #Final structure calculated with metropolis. This variable will be returned to angle calculator

        # Data structure with the rotatation (0-rotation steps) of each phi/psi angle
        # for example, if there are 3 aminoacids, there are two phis and two psi
        # the data structure for phis contains two positions the rotation for first phi and for the second phi, etc.
        anglePhi_old = []
        anglePsi_old = []

        for _ in range(self.number_angles):

            # Random initialization of angles
            anglePsi_old.append(np.random.choice(self.rotatition_steps))
            anglePhi_old.append(np.random.choice(self.rotatition_steps))

        for iteration in range(self.n_iterations):

            # initially the new angles are equal to the old (then one angle will be randomly modified)
            # deep copy is necessary to avoid two pointer to the same data structure (it is necessary only to modify one of the arrays)
            anglePhi_new = copy.deepcopy(anglePhi_old)
            anglePsi_new = copy.deepcopy(anglePsi_old)
            
            # Propose a change
            # 0 = phi | 1 = psi
            change_angle = np.random.choice((0,1))

            # number of angle (it is possible to have more than one phi/psi)
            position_angle = np.random.choice(self.number_angles)
            position_angle_binary = self.tools.angle_to_binary(position_angle, self.bits_number_angles)

            # 0 = 1 | 1 = -1
            change_plus_minus = np.random.choice((0,1))
            pm = -2*change_plus_minus + 1

            # Calculate the new angles
            if change_angle == 0:
                #Change just +1 or -1 step in the energies dictionary
                anglePhi_new[position_angle] = (anglePhi_old[position_angle] + pm) % self.rotatition_steps
            elif change_angle == 1:
                #Change just +1 or -1 step in the energies dictionary
                anglePsi_new[position_angle] = (anglePsi_old[position_angle] + pm) % self.rotatition_steps
            

            binary_key = ''
            for index in range(len(anglePhi_new)):

                # binary key should contain: phi_1 | psi_1 | phi_2 | psi_2 | ...
                binary_key += self.tools.angle_to_binary(anglePhi_new[index], self.bits_rotation)
                binary_key += self.tools.angle_to_binary(anglePsi_new[index], self.bits_rotation)

            # This choice of Delta_E seems weird.
            # Correspondingly: (state = angle_phi, angle_psi...) +  (move_id = phi/psi+  position_angle_binary) +  move_value
            Delta_E = self.deltas_dict[binary_key + str(change_angle) + position_angle_binary + str(change_plus_minus)]

            # Lets use a non_optimal simple schedule
            beta = iteration / self.n_iterations
            probability_threshold = np.exp(-beta*Delta_E)
            random_number = np.random.random_sample()

            # We should accept the change if probability_threshold > 1 (the energy goes down) or if beta is small.
            # If beta small, np.exp(-beta*Delta_E) approx 1.
            if random_number < min(1,probability_threshold): # Accept the change
                anglePhi_old = copy.deepcopy(anglePhi_new)
                anglePsi_old = copy.deepcopy(anglePsi_new)

        return [anglePhi_old, anglePsi_old]