import random
import re
import numpy as np
import itertools
from collections import OrderedDict

from bokeh.plotting import figure, show, output_file, gridplot
from bokeh.io import export_png
from bokeh.palettes import Turbo256
from bokeh.models import Legend, LegendItem, ColumnDataSource, LabelSet, Label
from bokeh.palettes import Dark2_5 as palette
from bokeh.models import SingleIntervalTicker, LinearAxis, Slope


def plot_q_vs_c(data):
    
    output_file("TTS comparison quantum vs random.html")

    width = 800
    height = 450

    x_range = (2**5, 2**11)
    x_min, x_max = x_range
    plot_tts = figure(
        x_axis_type="log", 
        y_axis_type="log", 
        y_range=(2*10**1, 3*10**4),
        x_range=(x_min, x_max),
        plot_height=height,
        plot_width=width
        )

    plot_tts.xaxis.ticker = [2**6, 2**8, 2**10]

    # fix xaxis to cross y axis in the point (1,1)
    #plot_tts.xaxis.fixed_location = 1

    x_point = []
    c_point = []
    q_point = []
    minirandom = []

    # filter by fixed beta
    data = dict(filter(lambda item: item[1]['schedule'] == 'fixed', data.items()))

    for protein_key in data:

        min_tts_q = data[protein_key]['min_tts_q']
        min_tts_c = data[protein_key]['min_tts_c']

        c_point.append(min_tts_c)
        q_point.append(min_tts_q)

        #relation = min_tts_c / min_tts_q
        #min_tts = min(min_tts_q, min_tts_c)

        if 'minifold' in protein_key:
            color_point = 'red'
            minirandom.append('minifold')
        elif 'random' in protein_key:
            color_point = 'blue'
            minirandom.append('random')
        elif 'original' in protein_key:
            color_point = 'green'
        else:
            color_point = 'black'

        size_point = int(data[protein_key]['number_bits'])*3
        space_size = 2**(int(data[protein_key]['number_bits']) * (2*int(data[protein_key]['number_aas']) -2))
        x_point.append(space_size)

        # plot dipeptides
        if data[protein_key]['number_aas'] == 2:

            # paint the point in the plot (only the point, the label is plotted out of the loop)
            #plot_tts.circle(min_tts, relation, size=size_point, fill_color=color_point, fill_alpha=0.6, line_color=color_point)
            plot_tts.circle(space_size, min_tts_q, size=size_point, fill_color=color_point, fill_alpha=1, line_color=color_point)
            plot_tts.circle(space_size, min_tts_c, size=size_point, line_color=color_point, fill_alpha=0, fill_color='white')

        elif data[protein_key]['number_aas'] == 3:

            #plot_tts.triangle(min_tts, relation, size=size_point, fill_color=color_point, fill_alpha=0.6, line_color=color_point)
            plot_tts.triangle(space_size, min_tts_q, size=size_point, fill_color=color_point, fill_alpha=1, line_color=color_point)
            plot_tts.triangle(space_size, min_tts_c, size=size_point, line_color=color_point, fill_alpha=0, fill_color='white')

        elif data[protein_key]['number_aas'] == 4:

            #plot_tts.square(min_tts, relation, size=size_point, fill_color=color_point, fill_alpha=0.6, line_color=color_point)
            plot_tts.square(space_size, min_tts_q, size=size_point, fill_color=color_point, fill_alpha=1, line_color=color_point)
            plot_tts.square(space_size, min_tts_c, size=size_point, line_color=color_point, fill_alpha=0, fill_color='white')

    # plot the plane for classical and quantum region
    #plot_tts.quad(top=[10**10], bottom=[1], left=[1],right=[10**10], color="green", fill_alpha=0.1)
    #plot_tts.quad(top=[1], bottom=[10**-10], left=[1], right=[10**10], color="red", fill_alpha=0.1)
    #'''
    x_fit_rand = []
    q_fit_rand = []
    c_fit_rand = []
    x_fit_mini = []
    q_fit_mini = []
    c_fit_mini = []

    assert(len(x_point) == len(q_point))
    for i in range(len(x_point)):
        if minirandom[i] == 'random':
            x_fit_rand.append(x_point[i])
            q_fit_rand.append(q_point[i])
            c_fit_rand.append(c_point[i])
        elif minirandom[i] == 'minifold':
            x_fit_mini.append(x_point[i])
            q_fit_mini.append(q_point[i])
            c_fit_mini.append(c_point[i])
        
    logx_fit_rand = np.log(x_fit_rand)
    logq_fit_rand = np.log(q_fit_rand)
    logc_fit_rand = np.log(c_fit_rand)
    logx_fit_mini = np.log(x_fit_mini)
    logq_fit_mini = np.log(q_fit_mini)
    logc_fit_mini = np.log(c_fit_mini)
    

    modelqr = np.polynomial.polynomial.polyfit(logx_fit_rand, logq_fit_rand, 1)
    modelqm = np.polynomial.polynomial.polyfit(logx_fit_mini, logq_fit_mini, 1)
    modelcr = np.polynomial.polynomial.polyfit(logx_fit_rand, logc_fit_rand, 1)
    modelcm = np.polynomial.polynomial.polyfit(logx_fit_mini, logc_fit_mini, 1)
    models = [modelcm, modelcr, modelqm, modelqr]

    model_renders = {}
        
    for model, mod, ini in zip(models, ['c', 'c', 'q', 'q'], ['m', 'r', 'm', 'r']):
        logb, a = model
        b = np.exp(logb)
        # 100 linearly spaced numbers
        x_min, x_max = x_range
        x_fit = np.linspace(x_min, x_max)

        # the function, which is y = x^2 here
        y_fit = b*x_fit**a
        print('a,b',a,b)
        line_color = 'red' if 'm' in ini else 'blue'
        line_dash = 'solid' if 'q' in mod else 'dashed'  
        x_fit = list(x_fit)

        plot_tts.line(x_fit, y_fit, line_color=line_color, line_dash = line_dash)

        x = -1
        y = -1
        model_renders[(mod,ini)] = plot_tts.line(x, y, line_color=line_color, line_dash = line_dash)

        y0 = 0
        if 'c' in mod:
            y0 += 280
        if 'r' in ini:
            y0 -= 25

        background_fill_alpha = 0.1 if line_dash == 'solid' else 0

        citation = Label(x=270, y=80 + y0, x_units='screen', y_units='screen',
            text='TTS = '+str(np.round(b, 3))+'* size**'+str(np.round(a, 3)), text_font_size='12px', render_mode='canvas',
            border_line_color=line_color, border_line_alpha=0.0, border_line_dash = line_dash,
            background_fill_color=line_color, background_fill_alpha=background_fill_alpha, text_color = line_color)

        plot_tts.add_layout(citation)

    red_circle = plot_tts.circle(x, y, color = 'red')
    blue_circle = plot_tts.circle(x, y, color = 'blue')

    red_circumphere = plot_tts.circle(x, y, line_color = 'red', color = 'white', fill_alpha = 0)
    blue_circumphere = plot_tts.circle(x, y, line_color = 'blue', color = 'white', fill_alpha= 0)
    #'''
    
    # create the label of each axis
    plot_tts.yaxis.axis_label='TTS'
    plot_tts.xaxis.axis_label='Size of the search space'

    legend = Legend(items=[
        ("minifold initialization, quantum", [model_renders[('q','m')], red_circle]),
        ("random initialization, quantum", [model_renders[('q','r')], blue_circle]),
        ("minifold initialization, classical", [model_renders[('c','m')], red_circumphere]),
        ("random initialization, classical", [model_renders[('c','r')], blue_circumphere])
    ], background_fill_alpha = 0, border_line_alpha = 0, location=(.37*width, .6*height))

    # add all legends to the plot
    plot_tts.add_layout(legend, 'left')

    # position all legends
    #plot_tts.legend.location = "top_left"
    #plot_tts.title.align = 'center'

    show(plot_tts)

def TTSplotter(data, schedule, width = 800, height = 450, title = None):
    # filter by fixed beta
    data = dict(filter(lambda item: item[1]['schedule'] == schedule, data.items()))

    x_range = (2*10**1, 3*10**4)

    plot_q_c_slop = figure(
        #title='Evolution of tts with different steps', # Usually graphs do not have title
        x_axis_label='Classical min(TTS)', 
        y_axis_label='Quantum min(TTS)',
        x_axis_type="log",
        y_axis_type="log",
        x_range= x_range, 
        y_range=(2*10**1, 3*10**4),
        plot_height=height,
        plot_width=width,
        title = title)

    al = []
    bl = []

    for init in ['minifold', 'random']:

        x_point = []
        y_point = []
        line_color = []
        marker = []
        legend = []
        size = []

        for protein_key in data:

            if init in protein_key:

                x_point.append(data[protein_key]['min_tts_c'])
                y_point.append(data[protein_key]['min_tts_q'])
                line_color.append('red' if 'minifold' in protein_key else 'blue')

                if re.search("[A-Z]{4}", protein_key):
                    marker.append('square')
                elif re.search("[A-Z]{3}", protein_key):
                    marker.append('triangle')
                elif re.search("[A-Z]{2}", protein_key):
                    marker.append('circle')
                else:
                    raise ValueError('The string {} does not fit the dipeptide, tripeptide or tetrapeptide description.'.format(protein_key))

                legend.append('minifold' if 'minifold initialization' in protein_key else 'random initialization')
                size.append(str(int(re.findall('_[0-9]_', protein_key)[0][1])*2))

        logcx = np.log(x_point)
        logqy = np.log(y_point)

        model = np.polynomial.polynomial.polyfit(logcx, logqy, 1)
        logb, a = model
        b = np.exp(logb)

        al.append(a)
        bl.append(b)

        # 100 linearly spaced numbers
        x_fit = np.linspace(x_range[0]/1e2, x_range[1]*1e2)

        # the function, which is y = x^2 here
        y_fit = b*x_fit**a
        print('a,b',a,b)

        source = ColumnDataSource(dict(x = x_point, y = y_point, line_color=line_color, marker=marker, legend=legend, size = size))

        #plot_q_c_slop.triangle(min_tts_c, min_tts_q, size=10, line_color='red', color='transparent')      
        #plot_q_c_slop.circle(min_tts_c, min_tts_q, size=10, line_color='blue', color='transparent')

        line_color = 'red' if init == 'minifold' else 'blue'    
        x_fit = list(x_fit)
        #fit_source = ColumnDataSource(dict(x = x_fit, y = y_fit, line_color='green', legend='y='+str(b)+'*x**'+str(a)))
        plot_q_c_slop.line(x_fit, y_fit, line_color=line_color) 
        # Failed attempt to picture an slope: we do not want a line, but a line when we are in log scale
        # slope = Slope(gradient=a, y_intercept=b, line_color=line_color, line_dash='dashed', line_width=3.5)
        # plot_q_c_slop.add_layout(slope)

        y0 = 25 if init == 'minifold' else 0
        citation = Label(x=width*.5, y=20 + y0, x_units='screen', y_units='screen',
            text='qTTS = '+str(np.round(b, 3))+'*cTTS^'+str(np.round(a, 3)), text_font_size='12px', render_mode='canvas',
            border_line_color=line_color, border_line_alpha=0.0, border_line_dash = 'solid',
            background_fill_color=line_color, background_fill_alpha=0, text_color = line_color)

        plot_q_c_slop.add_layout(citation)

        plot_q_c_slop.scatter(x="x", y="y", line_color="line_color", fill_alpha=0, marker="marker", source=source, size = "size") #legend_group='legend',

    x_diag = [1, 10**6]
    y_diag = [1, 10**6]
    plot_q_c_slop.line(x_diag, y_diag, line_width=2, line_color='gray', line_dash="dashed")

    plot_q_c_slop.yaxis.major_label_orientation = "vertical"
    plot_q_c_slop.xgrid.grid_line_color = None
    plot_q_c_slop.ygrid.grid_line_color = None

    return plot_q_c_slop, al, bl

def plot_q_vs_c_slope(data):

    output_file("TTS slope quantum vs random.html")
    width = 800
    height = 450

    plot_q_c_slop, al, bl = TTSplotter(data, schedule = 'fixed', width = width, height = height)
    
    x = -1
    y = -1
    rdb = plot_q_c_slop.diamond(x, y, color = 'blue')
    rlb = plot_q_c_slop.line(x, y, color = 'blue')

    rdr = plot_q_c_slop.diamond(x, y, color = 'red')
    rlr = plot_q_c_slop.line(x, y, color = 'red')

    rcg = plot_q_c_slop.circle(x, y, line_color="black", fill_alpha = 0)
    rtg = plot_q_c_slop.triangle(x, y, line_color="black", fill_alpha = 0)
    rsg = plot_q_c_slop.square(x, y, line_color="black", fill_alpha = 0)

    rdg2 = plot_q_c_slop.diamond(x, y, line_color="black", size = 4, fill_alpha = 0)
    rdg3 = plot_q_c_slop.diamond(x, y, line_color="black", size = 6, fill_alpha = 0)
    rdg4 = plot_q_c_slop.diamond(x, y, line_color="black", size = 8, fill_alpha = 0)
    rdg5 = plot_q_c_slop.diamond(x, y, line_color="black", size = 10, fill_alpha = 0)

    exp0 = str(np.round(al[0],3))
    exp1 = str(np.round(al[1],3))

    legend = Legend(items=[
        ("random initialization", [rdb, rlb]),
        #(r'qTTS ='+str(np.round(bl[1],3))+r'*cTTS^'+exp1, [rlb]),
        ("minifold initialization", [rdr, rlr]),
        #(r'qTTS ='+str(np.round(bl[0],3))+r'*cTTS^'+exp0, [rlr]),

        ("dipeptides", [rcg]),
        ("tripeptides", [rtg]),
        ("tetrapeptides", [rsg]),

        ("2 bits", [rdg2]),
        ("3 bits", [rdg3]),
        ("4 bits", [rdg4]),
        ("5 bits", [rdg5])
    ], location=(.3*width, .3*height), background_fill_alpha = 0, border_line_alpha = 0)

    plot_q_c_slop.add_layout(legend, 'left')

    citation = Label(x=1/3*width, y=1/7*height, x_units='screen', y_units='screen',
                    text='Quantum advantage', render_mode='canvas', text_font_size = '12px',
                    border_line_color='black', border_line_alpha=0.0,
                    background_fill_color='white', background_fill_alpha=0.0)

    plot_q_c_slop.add_layout(citation)

    citation = Label(x=1/4*width, y=5/6*height, x_units='screen', y_units='screen',
                    text='Classical advantage', render_mode='canvas', text_font_size = '12px',
                    border_line_color='black', border_line_alpha=0.0,
                    background_fill_color='white', background_fill_alpha=0.0)

    plot_q_c_slop.add_layout(citation)

    show(plot_q_c_slop)
    export_png(plot_q_c_slop, filename="fixed_beta_TTS_slope.png")

def plot_q_vs_c_slope_var(data):

    output_file("schedules.html")

    width = 500
    height = 500

    # create a new plot
    s1, al1, bl1 = TTSplotter(data, schedule = 'logarithmic', width = width, height = height, title = 'Boltzmann')

    # create another one
    s2, al2, bl2 = TTSplotter(data, schedule = 'linear', width = width, height = height, title = 'Cauchy')

    # create another
    s3, al3, bl3 = TTSplotter(data, schedule = 'geometric', width = width, height = height, title = 'geometric')

    # create final one
    s4, al4, bl4 = TTSplotter(data, schedule = 'exponential', width = width, height = height, title = 'exponential')

    # put all the plots in a grid layout
    p = gridplot([[s1, s2], [s3, s4]])

    # show the results
    show(p)
    export_png(p, filename="var_beta_TTS_slope.png")

def plot_q_opt_step(data):

    output_file("Quantum optimal step.html")
    quantum_optimal_step = {}

    for protein_key in data:

        protein_name = protein_key.split('_')[0]
        bits = protein_key.split('_')[1]
        init_method = protein_key.split('_')[2]
        step = data[protein_key]['min_tts_q_step']

        if len(protein_name) == 2:

            if protein_name+'-'+init_method in quantum_optimal_step.keys():
                quantum_optimal_step[protein_name+'-'+init_method][bits] = step
            else:
                quantum_optimal_step[protein_name+'-'+init_method] = {bits: step}

    p = figure(plot_width=400, plot_height=400, x_range=(3, 10), x_axis_type=None)
    ticker = SingleIntervalTicker(interval=1, num_minor_ticks=10)
    xaxis = LinearAxis(ticker=ticker)
    p.add_layout(xaxis, 'below')
    # create a color iterator
    colors = itertools.cycle(palette)    
    
    for protein, color in zip(quantum_optimal_step, colors):

        ordered_quantum_steps = OrderedDict(sorted(quantum_optimal_step[protein].items()))


        p.line(list(ordered_quantum_steps.keys()), list(ordered_quantum_steps.values()), line_width=2, color=color, legend=protein)

        #p.circle([1, 2], [3, 4], size=20, color="navy", alpha=0.5)


    show(p)