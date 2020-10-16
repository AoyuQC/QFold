import sys
import initializer
import angleCalculator
import psiFour
import utils
import time

if len(sys.argv) != 5 and len(sys.argv) != 6:
    print ("<*> ERROR: Wrong number of parameters - Usage: python main.py proteinName aminoacids_chain numberBitsForRotations method_rotations_generation")
    print ("<!> Example: python main.py Glycylglycine GG 6 random optional_protein_id (6 bits for rotations are 64 steps)")
    sys.exit(0)

print('\n###################################################################')
print('##                             QFOLD                             ##')
print('##                                                               ##')
print('## Tool that combines AI and QC to solve protein folding problem ##')
print('###################################################################\n')

start_time = time.time()

proteinName = sys.argv[1].lower()
aminoacids = sys.argv[2]
numberBitsRotation = int(sys.argv[3])
method_rotations_generation = sys.argv[4]

if len(sys.argv) == 6:
    protein_id = sys.argv[5]
else:
    protein_id = -1

rotationSteps = 2**(int(numberBitsRotation))

#Read config file with the QFold configuration variables
config_path = './config/config.json'

tools = utils.Utils(config_path)
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
#The format should be energies[proteinName][numberBitsForRotation] ex: energiesGlycylglycine2.json
try:
    f = open(config_variables['precalculated_energies_path']+'delta_energies_'+proteinName+'_'+str(numberBitsRotation)+'_'+method_rotations_generation+'.json')
    f.close()
except IOError:
    print('<!> Info: No precalculated energies file found => Calculating energies\n')
    angleInitializer.calculate_delta_energies(proteinName, numberBitsRotation, method_rotations_generation, aminoacids, protein_id)

#Create an empty list of enery list
#HARDCODED for proteins with only two aminoacids
#TODO modify to any number of aminoacids (it should a list of list, each position of the list contains a list of phi and psi values of this list position)
[deltas_dict, psi4_min_energy, initial_min_energy, index_min_energy, inizialitation_stats] = psi.readEnergyJson(proteinName, numberBitsRotation, method_rotations_generation)

print('## 3D STRUCTURE CALCULATOR FOR', proteinName,'with', numberBitsRotation,'bits and', method_rotations_generation,'initialization##\n')

angleCalculator = angleCalculator.AngleCalculator(
    numberBitsRotation, 
    config_variables['ancilla_bits'], 
    config_variables['scaling_factor'], 
    config_variables['number_iterations'],
    len(aminoacids)
    )

q_accumulated_tts = []
c_accumulated_tts = []
x_axis = []

min_q_tts = {'step': 0, 'value': -1}
min_c_tts = {'step': 0, 'value': -1}

results = []
for step in range(config_variables['initial_step'], config_variables['final_step']):

    # execute for option 0 (quantum) and option 1 (classical)
    for option in [0,1]:

        # calculate the probability matrix of the optimization algorithms
        probabilities_matrix = angleCalculator.calculate3DStructure(deltas_dict, step, config_variables['beta_max'], option)

        p_t = 0
        # if the index of min energy calculated by psi 4 is in the results of metropolis, p_t is extracted
        # else, the p_t is set to a very small value close to 0 (not 0 to avoid inf values)
        if index_min_energy in probabilities_matrix.keys():
            p_t = probabilities_matrix[index_min_energy]
        else:
            p_t = 0

        # Result is the calculated TTS
        if p_t >= 1:
            results.append([1, step])

        elif p_t == 0:
            results.append([9999, step])

        else:
            results.append([tools.calculateTTS(config_variables['precision_solution'], step, p_t), step])

for index in range(0, len(results), 2):

    quantum_TTS = results[index][0]
    quantum_step = results[index][1]
    classical_TTS = results[index+1][0]
    classical_step = results[index+1][1]

    if quantum_TTS < min_q_tts['value'] or min_q_tts['value'] == -1:
        
        min_q_tts['value'] = quantum_TTS
        min_q_tts['step'] = quantum_step

    if classical_TTS < min_c_tts['value'] or min_c_tts['value'] == -1:
        
        min_c_tts['value'] = classical_TTS
        min_c_tts['step'] = classical_step

    q_accumulated_tts.append(quantum_TTS)
    c_accumulated_tts.append(classical_TTS)

    tools.plot_tts(q_accumulated_tts, c_accumulated_tts, proteinName, aminoacids, numberBitsRotation, method_rotations_generation, config_variables['initial_step'])

# Difference between the minimum energy of initializer minus the minimum energy of psi4
min_energy_difference = (1 - (initial_min_energy - psi4_min_energy)) *100
delta_mean = tools.calculate_delta_mean(deltas_dict)
std_dev_deltas = tools.calculate_std_dev_deltas(deltas_dict)

final_stats = {'q': min_q_tts, 'c': min_c_tts}

tools.write_tts(
    config_variables['initial_step'], 
    config_variables['final_step'], 
    q_accumulated_tts, 
    c_accumulated_tts, 
    proteinName,
    aminoacids,
    numberBitsRotation, 
    method_rotations_generation,
    inizialitation_stats,
    final_stats)

# Compare the difference between the minimum energy of initializer minus the minimum energy of psi4 with the mean of energy deltas
precision_vs_delta_mean = tools.calculate_diff_vs_mean_diffs(min_energy_difference, delta_mean)

# MERGE RESULTS: if the results generated are comparable with similar results generated previously, it generates the shared plot
# For example, if this execution generates results for minifold 4 bits rotation GG and there are results for random 4 bits GG
# it combines the results into only one plot

results = {}
alternative_results_found = False
for alternative_method in config_variables['methods_initialization']:

    if alternative_method != method_rotations_generation:

        try:
            f = open(config_variables['path_tts_plot']+'tts_results_'+proteinName+'_'+str(numberBitsRotation)+'_'+alternative_method+'.json')
            results[alternative_method] = tools.read_results_file(config_variables['path_tts_plot']+'tts_results_'+proteinName+'_'+str(numberBitsRotation)+'_'+alternative_method+'.json')
            alternative_results_found = True
            f.close()
        except IOError:
            print('<!> Info: No results for method', alternative_method,'found\n')

if alternative_results_found:

    results[method_rotations_generation] = tools.read_results_file(config_variables['path_tts_plot']+'tts_results_'+proteinName+'_'+str(numberBitsRotation)+'_'+method_rotations_generation+'.json') 
    tools.generate_combined_results_plot(results, proteinName, numberBitsRotation)

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
print('** Precision QFold     =>', min_energy_difference,'%        **')
print('** Precision vs Δ mean =>', precision_vs_delta_mean ,'     **')
print('** Mean Δ              =>', delta_mean, '                  **')
print('** Standard deviation  =>', std_dev_deltas, '        **')
print('** Execution time     =>', execution_time          ,' seconds   **')
print('********************************************************\n\n')