from qiskit.aqua.components.oracles import Oracle, TruthTableOracle

import math

class Beta_precalc_TruthTableOracle(TruthTableOracle):
    '''Outputs the binary angle of rotation to get the correct probability. Tested ok'''
    def __init__(self, deltas_dictionary, beta, out_bits, optimization=True, mct_mode='noancilla'):

        self.beta = beta
        self.out_bits = out_bits
        self.deltas_dictionary = deltas_dictionary
        
        self.bitmap = self.calculate_bitmap()
        print('\n')
        for bm in self.bitmap:
            print(len(bm))
        print('\n')

        super().__init__(self.bitmap, optimization, mct_mode)
        
    def calculate_bitmap(self):
        new_bitmap = []
        angles = {}

        for key in self.deltas_dictionary.keys():

            if self.deltas_dictionary[key] >= 0:
                probability = math.exp(-self.beta * self.deltas_dictionary[key])
            else: 
                probability = 1
                
            # Instead of encoding the probability, we will encode 1-probability. That way 1 -> 000, 
            # but if probability is 0 there is some small probability of acceptance
            probability = 1 - probability
            
            # Instead of probability save angles so rotations are easier to perform afterwards sqrt(p) = sin(theta)
            angle = math.asin(math.sqrt(probability))
            
            # Make the angle be between [0,1]. Since the maximum is pi/2
            angle /= (math.pi/2) 
            
            # Convert it into an integer and a string
            str_angle2 = self.int_angle_func(angle,self.out_bits)
            angles[key] = str_angle2
        
        # Encoding the new bitmap
        new_bitmap = []
        for o in range(self.out_bits):
            string = ''
            for key in self.deltas_dictionary.keys():
                string += str(angles[key])[o]
            new_bitmap += [string]

        return new_bitmap

    #Method to convert angles int to binary
    def int_angle_func(self, angle,out_bits):
        out_str = ''
        a = angle
        for bits in range(1,out_bits+1):

            if a + 1e-10 > 1/(2**(bits)):
                out_str += '1'
                a -= 1/(2**bits)
            else:
                out_str += '0'
        
        return out_str