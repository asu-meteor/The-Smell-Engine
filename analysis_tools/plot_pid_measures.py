import json
import pandas as pd  
import numpy as np 
import matplotlib.pyplot as plt
from scipy.stats import linregress
import matplotlib
from matplotlib.ticker import FormatStrFormatter, ScalarFormatter
from scipy import stats
import os 
plt.rcParams.update({'figure.dpi': 125.0})

SMALL_SIZE = 10
MEDIUM_SIZE = 14
BIG_SIZE = 20

#plt.rc('font', size=SMALL_SIZE)
plt.rc('axes', titlesize=BIG_SIZE)       # fontsize of the axes title
plt.rc('axes', labelsize=BIG_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIG_SIZE)     # fontsize of the figure title

corr_factor = 1#1180.92989951

def get_super(x):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=()"
    super_s = "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿˢᵀᵁⱽᵂˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖ۹ʳˢᵗᵘᵛʷˣʸᶻ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾"
    res = x.maketrans(''.join(normal), ''.join(super_s))
    return x.translate(res)

def plot_var_vs_conc(variances, concs, title_details=''): 
    print(concs)
    fig, ax = plt.subplots()
    ax.scatter(concs, variances)
    ax.set_xlabel(f'Concentration (mol/m{get_super(str(3))})', fontweight='bold')
    ax.set_ylabel('Variance', fontweight='bold')
    ax.set_title('Variance vs Concentration' + title_details, fontweight='bold')
    ax.set_xscale('log')
    ax.set_yscale('log')
    #ax.set_yticks(np.linspace(-5e-3, 1.5e-2, 10))
    #ax.yaxis.set_major_formatter(FormatStrFormatter("%.1e"))
    #plt.ylim([-5e-3, 1.5e-2])
    plt.xticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.yticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.tight_layout()
    #plt.ylim([-4e-2, 8e-1])
    plt.show()

def plot_error_bars(concs, pid_vals, title_details=''):
    pid_std = np.std(pid_vals, axis=0)
    pid_avg = np.mean(pid_vals, axis=0)
    concs = np.mean(concs, axis=0)

    fig, ax = plt.subplots()
    ax.errorbar(concs, pid_avg, yerr=pid_std, ecolor='black', capsize=5, fmt='o')
    ax.set_xlabel(f'Concentration (mol/m{get_super(str(3))})', fontweight='bold')
    ax.set_ylabel('PID Response (V)', fontweight='bold')
    ax.set_title('PID Response vs Concentration' + title_details, fontweight='bold')
    #ax.yaxis.set_label_coords(-0.075, 0.53)
    ax.set_xscale('log')
    ax.set_yscale('symlog')
    #plt.tick_params(axis='y', which='minor')
    ax.set_yticks(np.linspace(-5e-3, 1.5e-2, 10))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.1e"))
    #plt.ylim([-5e-3, 1.5e-2])
    plt.xticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.yticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.tight_layout()
    #plt.ylim([-4e-2, 8e-1])
    plt.show()

    plot_var_vs_conc(np.square(pid_std), concs)

def conc_measures(fn, title_details='', plot=False, plot_error=False):
    with open(fn, 'r') as json_file:
        pid_data = json.load(json_file)

    concs = []
    pid_vals = []
    for entry in pid_data["data"]:
        concs.append(entry["conc"])
        pid_vals.append(entry["pid"])
    
    concs = np.array(concs)
    pid_vals = np.array(pid_vals)

    n_concs = np.unique(concs).size
    n_trials = concs.size // n_concs
    
    concs = corr_factor*concs[:n_trials*n_concs].reshape((n_trials, -1))
    pid_vals = pid_vals[:n_trials*n_concs].reshape((n_trials, -1))
    baselines = np.tile(np.expand_dims(pid_vals[:, 0], axis=1), n_concs)
    pid_vals =  pid_vals - baselines
    print(baselines[0,0])

    if plot: 
        fig, ax = plt.subplots()
        for i in range(n_trials):
            ax.scatter(concs[i, :], pid_vals[i, :], label=f"Trial {i + 1}")
        #ax.scatter(np.mean(concs, axis=0), np.mean(pid_vals, axis=0))
    
        ax.set_xlabel(f'Concentration (mol/m{get_super(str(3))})', fontweight='bold')
        ax.set_ylabel('PID Response (V)', fontweight='bold')
        ax.set_title('PID Response vs Concentration' + title_details, fontweight='bold')
        ax.yaxis.set_label_coords(-0.075, 0.53)
        plt.xscale('log')
        plt.yscale('symlog')
        plt.ylim([-5e-3, 1.5e-2])
        #plt.ylim([-4e-2, 8e-1])
        plt.legend()
        plt.xticks(fontsize=MEDIUM_SIZE, fontweight='bold')
        plt.yticks(fontsize=MEDIUM_SIZE, fontweight='bold')
        plt.tight_layout()
        plt.show()

    if plot_error: 
        plot_error_bars(concs, pid_vals[1:, :])

    return concs, pid_vals 

def plot_piecewise(x1, y1, x2, y2, title_details): 
    n_trials, _ = x1.shape 

    fig, ax = plt.subplots()
    ax.scatter(x1[0, :], y1[0, :], label="0.25L Constant Flow")
    ax.scatter(np.mean(x2, axis=0), np.mean(y2, axis=0), label="1.0L Constant Flow")
    """
    for i in range(n_trials):
        ax.scatter(x1[i, 1:], y1[i, 1:], label=f"Trial {i + 1}")

        baseline = y2[i, 0]
        ax.scatter(x2[i, 1:], y2[i, 1:], label=f"Trial {i + 1}")
    """
    ax.set_xlabel(f'Concentration (mol/m{get_super(str(3))})')
    ax.set_ylabel('PID Response (V)')
    ax.set_title('Piecewise Average PID Response vs Concentration' + title_details, fontweight='bold')
    ax.yaxis.set_label_coords(-0.075, 0.53)
    plt.xscale('log')
    plt.yscale('symlog')
    plt.ylim([-4e-2, 8e-1])
    plt.legend()
    plt.xticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.yticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.tight_layout()
    plt.show() 

    c1 = x1[0, :]
    c2 = x2[0, :]
    x_intersects = np.nonzero(np.in1d(c1, c2))
    y1_intersects = np.squeeze(y1[:, x_intersects], axis=1)
    x_intersects = np.nonzero(np.in1d(c2, c1))
    y2_intersects = np.squeeze(y2[:, x_intersects], axis=1)

    y_intersects = np.concatenate((y1_intersects, y2_intersects), axis=0)
    y_intersects_avg = np.mean(y_intersects, axis=0)
    y_intersects_std = np.std(y_intersects, axis=0)
    x_intersects = np.intersect1d(c1, c2)

    x1_no_intersects = c1[~np.in1d(c1, c2)]
    y1_no_intersects = y1[:, ~np.in1d(c1, c2)]
    x2_no_intersects = c2[~np.in1d(c2, c1)]
    y2_no_intersects = y2[:, ~np.in1d(c2, c1)]

    fig, ax = plt.subplots()
    ax.errorbar(x_intersects, y_intersects_avg, yerr=y_intersects_std, 
                ecolor='black', capsize=5, fmt='o', c='#1f77b4')
    ax.errorbar(x1_no_intersects, np.mean(y1_no_intersects, axis=0), 
                yerr=np.std(y1_no_intersects, axis=0), ecolor='black', 
                capsize=5, fmt='o', c='#1f77b4')
    ax.errorbar(x2_no_intersects, np.mean(y2_no_intersects, axis=0), 
                yerr=np.std(y2_no_intersects, axis=0), ecolor='black', 
                capsize=5, fmt='o', c='#1f77b4')
    ax.set_xlabel(f'Concentration (mol/m{get_super(str(3))})', fontweight='bold')
    ax.set_ylabel('PID Response (V)', fontweight='bold')
    ax.set_title('Piecewise PID Response vs Concentration' + title_details, fontweight='bold')
    ax.yaxis.set_label_coords(-0.075, 0.53)
    plt.xscale('log')
    plt.yscale('symlog')
    #plt.ylim([-5.5e-3, 3e-2])
    plt.ylim([-4e-2, 8e-1])
    plt.xticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.yticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.tight_layout()
    plt.show()

def machine_state_measures(fn, constant, value, variable, title_details='', show=False): 
    with open(fn, 'r') as json_file:
        state_data = json.load(json_file)
    
    print(state_data["info"])

    pid_data_frame_array = [] #[state, pidC,pid,wave]
    
    for entry in state_data["data"]:
        pid_data_frame_array.append([entry["state"],entry["pidC"],entry["pid"],entry["wave"]])
        pid_data_frame_array[-1] = entry["state"] + pid_data_frame_array[-1]

    pid_df = pd.DataFrame(pid_data_frame_array, columns=["mfcA","mfcB","h1","h2","h3","h4","h5","h6","h7","h8","h9","h10","L1","L2","L3","L4","L5","L6","L7","L8","L9","L10","state", "pidC", "pid", "wave"])
    baseline = pid_df.iloc[0]["pid"]
    pid_df["pid"] = pid_df["pid"] - baseline

    pid_data_frame_split = []

    mfc1x = []
    mfc1y = []
    mfc1y_err = []

    mfc1_index = pid_df.loc[(pid_df[constant] == value) & ((10*pid_df[variable]) % 1 ==0) & (np.abs(stats.zscore(pid_df[variable])) < 3)][variable].index
    mfc1_index_nc = pid_df.loc[(pid_df[constant] == value) & ((10*pid_df[variable]) % 1 ==0)][variable].index
    print(f"Number of Points: {mfc1_index.shape[0]}")
    print(f"Number of Outliers: {mfc1_index.shape[0] - mfc1_index_nc.shape[0]}")

    for i in range(1,11):
        mfc1x.append(i/10)
        pid = pid_df.loc[(pid_df[constant] == value) & (pid_df[variable] ==(i/10))]["pid"]
        mfc1y.append(pid.mean())
        mfc1y_err.append(pid.std())
            
    if(show):
        plt.title(f"{constant} {value} all, log pid vs log ocupancy")
        plt.xscale('log')
        plt.yscale('log')
        plt.ylabel("log pid")
        plt.xlabel(f"log {variable}")
        plt.scatter(pid_df.iloc[mfc1_index][variable],pid_df.iloc[mfc1_index]["pid"])
        plt.show()

        plt.title(f"{constant} {value} Average, log pid vs log ocupancy")
        plt.xscale('log')
        plt.yscale('log')
        plt.ylabel("log pid")
        plt.xlabel(f"log {variable}")
        plt.scatter(mfc1x,mfc1y)
        plt.show()
    
    return mfc1x, mfc1y, mfc1y_err

def machine_state_combined(x, y, err, title_detail, xlabel, legend_labels, ylim, 
                           error_bars=False, scale='log'): 
    fig, ax = plt.subplots()
    
    # Combined 
    ax.set_title("PID Response vs" + title_detail, fontweight='bold')
    ax.set_ylabel("PID Response (V)", fontweight='bold')
    ax.set_xlabel(xlabel, fontweight='bold')

    for i in range(y.shape[0]):
        if error_bars: 
            ax.errorbar(x[i, :], y[i, :], yerr=err[i, :], ecolor='black',
                        capsize=5, fmt='o', label=legend_labels[i])
        else: 
            ax.plot(x[i, :], y[i, :], '-o', label=legend_labels[i])

    plt.xscale(scale)
    if scale == 'log': 
        plt.yscale('symlog')
        ax.set_yticks(ticks=[0, 1])
        #ax.set_ylim([-0.05, 1.0e-1])
    else: 
        plt.yscale(scale)
        ax.set_ylim(ylim)
        
   #ax.yaxis.set_label_coords(-0.075, 0.53)
    ax.set_xticks(ticks=x[0, :])
    
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    plt.legend(loc="upper left", prop={'size': 14, 'weight': 'bold'})
    plt.xticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.yticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.tight_layout()
    plt.show()

def plot_machine_state_measures(data_path, plots, title_detail, x_label, units, 
                                constant, var, scale):
    const_scale = 1
    if constant == "mfcB": 
        const_scale = 10 
        ylim = [-5e-2, 15e-2]
    elif constant == "mfcA": 
        const_scale = 1
        ylim = [-0.05, 3.5]

    var_scale = 1
    if var == "mfcB": 
        var_scale = 10 
        ylim = [-5e-2, 15e-2]
    elif var == "mfcA": 
        var_scale = 1
        ylim = [-0.05, 3.5]

    pid = np.zeros((len(plots[1]), 10))
    x = np.zeros((len(plots[1]), 10))
    error = np.zeros((len(plots[1]), 10))
    labels = []
    for i, plot in enumerate(plots[1]): 
        x_, y, err = machine_state_measures(data_path, constant, plot, var)
        pid[i, :] = y 
        x[i, :] = var_scale * np.array(x_)
        error[i, :] = err 
        labels.append(f"{plots[0]} = {const_scale * plot} {units}")

    machine_state_combined(x, pid, error, title_detail, 
        x_label, labels, ylim, error_bars=False, scale=scale)

def pid_calibration_constant(): 
    dilution = [1, 4, 16, 64]

    c_septum = [2.44, 1.88, 0.98, 0.34]
    pid_septum = [2.434, 0.082, 0.076, -0.0013]

    c_machine = [0.000237]

def plot_multiple_trials(x_data, y_data): 
    if x_data.ndim > 1: 
        x_data = np.squeeze(x_data)

    n_trials, _ = y_data.shape
    ymin, ymax = -0.1, 1.5 #-2e-3, 1.7e-2 #-0.1, 1.5
    yticks = np.linspace(ymin, ymax, 10)

    fig, ax = plt.subplots()
    for i in range(n_trials):
        ax.semilogx(x_data, y_data[i, :], '.', label=f"Trial {i + 1}", alpha=0.5)
    
    ax.set_xlabel(f'Concentration (mol/m{get_super(str(3))})', fontweight='bold')
    ax.set_ylabel('PID Response (V)', fontweight='bold')
    ax.set_title('PID Response vs Concentration' + title_details, fontweight='bold')
    #ax.set_yticks(yticks)
    #ax.set_yticklabels([str(round(tick, 1)) for tick in yticks])
    #plt.xscale('log')
    #plt.yscale('symlog')
    plt.ylim([ymin, ymax])
    plt.legend(loc="upper left")
    plt.xticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.yticks(fontsize=MEDIUM_SIZE, fontweight='bold')
    plt.tight_layout()
    plt.show()

def plot_saturation_experiment(): 
    path = '/Users/jess/Documents/Meteor/Smell Engine/data/'
    fn = 'auto_results_conc_full_1-11_1L_const.json'
    data_path = os.path.join(path, fn)
    title_details = ''
    concs, pid_vals1 = conc_measures(data_path, title_details)

    fn = 'auto_results_conc_full_1-11_1L_const_trial_2.json'
    data_path = os.path.join(path, fn)
    title_details = ''
    _, pid_vals2 = conc_measures(data_path, title_details)

    fn = 'auto_results_conc_full_1-12_1L_const_trial_3.json'
    data_path = os.path.join(path, fn)
    title_details = ''
    _, pid_vals3 = conc_measures(data_path, title_details)

    fn = 'auto_results_conc_full_1-12_1L_const_trial_4.json'
    data_path = os.path.join(path, fn)
    title_details = ''
    _, pid_vals4 = conc_measures(data_path, title_details)

    fn = 'auto_results_conc_full_1-12_1L_const_trial_5.json'
    data_path = os.path.join(path, fn)
    title_details = ''
    _, pid_vals5 = conc_measures(data_path, title_details)

    y_data = np.vstack((pid_vals1, pid_vals2, pid_vals3, pid_vals4, pid_vals5))
    plot_multiple_trials(concs, y_data)

def plot_publication_1(): 
    path = '/Users/jess/Documents/Meteor/Smell Engine/data/submission 11-5-21'
    fn = 'auto_results_conc_lower_11-3_250mL_const.json'
    data_path = os.path.join(path, fn)
    title_details = ''
    low_concs, low_pid_vals =  conc_measures(data_path, title_details, plot=True, plot_error=True)

    fn = 'auto_results_conc_higherA_11-1_v2.json'
    data_path = os.path.join(path, fn)
    title_details = ''
    high_concs, high_pid_vals = conc_measures(data_path, title_details, plot=True, plot_error=True)

    title_details = ''
    plot_piecewise(low_concs, low_pid_vals, high_concs, high_pid_vals, 
                   title_details)

    fn = "auto_results_state10-11.json"
    data_path = os.path.join(path, fn)
    plots = ("Flow Rate", [1.0, 0.75, 0.5, 0.25])
    title_detail = " Valve A"
    x_label = "Occupancy Time (s)"
    units = "L/min"
    constant = "mfcA"
    var = "h1"
    scale = "linear"
    plot_machine_state_measures(data_path, plots, title_detail, x_label,
                                units, constant, var, scale)

    plots = ("Occupancy", [1.0, 0.75, 0.5, 0.25])
    title_detail = " MFC A"
    x_label = "Flow Rate (L/min)"
    units = "s"
    constant = "h1"
    var = "mfcA"
    scale = "linear"
    plot_machine_state_measures(data_path, plots, title_detail, x_label,
                                units, constant, var, scale)

    fn = "auto_results_state10-11-mfcB_trials_mfcC_half.json"
    data_path = os.path.join(path, fn)
    plots = ("Flow Rate", [1.0, 0.75, 0.5, 0.25])
    title_detail = " Valve B"
    x_label = "Occupancy Time (s)"
    units = "cc/min"
    constant = "mfcB"
    var = "L1"
    scale = "linear"
    plot_machine_state_measures(data_path, plots, title_detail, x_label,
                                units, constant, var, scale)

    plots = ("Occupancy", [1.0, 0.75, 0.5, 0.25])
    title_detail = " MFC B"
    x_label = "Flow Rate (cc/min)"
    units = "s"
    constant = "L1"
    var = "mfcB"
    scale = "linear"
    plot_machine_state_measures(data_path, plots, title_detail, x_label,
                                units, constant, var, scale)

if __name__ ==  '__main__': 
    plot_publication_1()
