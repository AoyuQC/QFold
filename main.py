import sys
import initializer
import angleCalculator
import psiFour
import utils

import time
import datetime

#Read config file with the QFold configuration variables
config_path = './config/config.json'
tools = utils.Utils(config_path)

args = tools.parse_arguments()

print('\n###################################################################')
print('##                             QFOLD                             ##')
print('##                                                               ##')
print('## Tool that combines AI and QC to solve protein folding problem ##')
print('###################################################################\n')

start_time = time.time()

rotationSteps = 2**(int(args.bits))
if args.id == None: args.id = -1

config_variables = tools.get_config_variables()
angleInitializer = initializer.Initializer(
    psi4_path = config_variables['psi4_path'],
    input_file_energies_psi4 = config_variables['input_filename_energy_psi4'], 
    output_file_energies_psi4 = config_variables['output_filename_energy_psi4'],
    energy_method = config_variables['energy_method'],
    precalculated_energies_path = config_variables['precalculated_energies_path'], 
    model_path = config_variables['model_path'], 
    window_size = config_variables['window_size'], 
    max_aa_length = config_variables['maximum_aminoacid_length'],
    initialization_option = config_variables['methods_initialization'],
    n_threads = config_variables['n_threads_pool'],
    basis = config_variables['basis']
    )

psi = psiFour.PsiFour(
    config_variables['psi4_path'], 
    config_variables['input_filename_energy_psi4'], 
    config_variables['output_filename_energy_psi4'], 
    config_variables['precalculated_energies_path'], 
    config_variables['energy_method'], 
    config_variables['n_threads_pool'],
    config_variables['basis'])

#Check if it existes a precalculated energy file with the same parameters, if not call initializer to calculate it
#The format should be energies[args.protein_name][numberBitsForRotation] ex: energiesGlycylglycine2.json
try:
    f = open(config_variables['precalculated_energies_path']+'delta_energies_'+args.protein_name+'_'+str(args.bits)+'_'+args.initialization+'.json')
    f.close()
except IOError:
    print('<!> Info: No precalculated energies file found => Calculating energies\n')
    angleInitializer.calculate_delta_energies(args.protein_name, args.bits, args.initialization, args.aminoacids, args.id)

#Create an empty list of enery list
#HARDCODED for proteins with only two args.aminoacids
#TODO modify to any number of args.aminoacids (it should a list of list, each position of the list contains a list of phi and psi values of this list position)
[deltas_dict, psi4_min_energy, initial_min_energy, index_min_energy, initialization_stats] = psi.readEnergyJson(args.protein_name, args.bits, args.initialization)

print('## 3D STRUCTURE CALCULATOR FOR', args.protein_name,'with', args.bits,'bits and', args.initialization,'initialization##\n')

angleCalculator = angleCalculator.AngleCalculator(
    args.bits, 
    config_variables['ancilla_bits'], 
    config_variables['number_iterations'],
    len(args.aminoacids),
    initialization_stats,
    tools,
    config_variables['path_qiskit_token'],
    config_variables['device_ibm_q']
    )

[min_q_tts, min_c_tts] = angleCalculator.calculate3DStructure(
    deltas_dict, 
    index_min_energy,
    config_variables['initial_step'], 
    config_variables['final_step'], 
    config_variables['beta'], 
    config_variables['beta_type'],
    config_variables['precision_solution']
    )

execution_time = time.time() - start_time

print('\n\n********************************************************')
print('**                       RESULTS                      **')
print('********************************************************')
print('**                                                    **')
print('** Quantum Metropolis   => Min TTS:', '{:.10f}'.format(min_q_tts['value']), 'at step:', min_q_tts['step'], ' **')
print('** Classical Metropolis => Min TTS:', '{:.10f}'.format(min_c_tts['value']), 'at step:', min_c_tts['step'], ' **')
print('**                                                    **')
print('** -------------------------------------------------- **')
print('**                                                    **')
print('** Execution time     =>', str(datetime.timedelta(seconds=execution_time)) ,' in hh:mm:ss  **')
print('********************************************************\n\n')