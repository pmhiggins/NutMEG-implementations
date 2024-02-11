import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
from matplotlib.ticker import ScalarFormatter
from uncertainties import ufloat as uf


mpl.rcParams['lines.linewidth'] = 3.
mpl.rcParams['axes.linewidth'] = 3.
mpl.rcParams["axes.labelweight"] = "bold"
mpl.rcParams["axes.labelsize"] = 9


def get_H2_bio(H2_in, R_abb, R_p):
    """
    For a H2 inflow H2_in, and abio to bio methane ratio, compute an estimate
    of the biological H2 consumption.
    """
    return -H2_in / (1+(0.25*R_p*(1+R_abb)))

def Mp_consistency(M_p, H_b, R_b, R_abb):
    """ Check for consistency in the methane plume observations M_p with the
    methane generated by H2 bio flux H_b.
    where all are directional properties.
    returns H_b, with impossible combinations relaced with np.nan
    """

    # Calculate proposed M_out based on the bio H consumption, and plume R_ab:b
    M_out = (H_b / R_b) * (1+R_abb)
    # H_b is a ufloat, so uncertainties propagate.
    # separate out the ufloat to max and min 'tops', 'bottoms'
    # for H2 and CH4 (CH4 is M).
    tops = M_out.n + M_out.s
    bottoms = M_out.n - M_out.s

    # M_p is the plume observation of methane we want to check,
    # so take out absolute values to compare.
    topM = - (M_p.n) + M_p.s
    bottomM = - (M_p.n) - M_p.s

    # b and t define the top and bottom of where abs(M_P) and M_out overlap
    b= max(bottoms, bottomM)
    t= min(tops, topM)

    if b < t:
        # there is overlap between the uncertainties of space plume obs,
        # and this combination of H_b and R_ab:b.
        nom = (b+t)/2
        # identify the range of H_b that facilitates this
        consistentM = uf(nom, abs(nom-b))
        consistentH = consistentM* R_b / (1+R_abb)
        # print(consistentH)
        return consistentH
    else:
        return uf(np.nan,np.nan)

def Hp_consistency(H2in, H_b, H_p):
    """ Check for consistency in the expression
    H2in + H_b + H_p = 0
    where all are directional properties.
    returns H_b, with nonphysical combinations relaced with np.nan
    """
    # H2in + H_b + H_p = 0 needs to be checked for
    H_est = H2in + H_b # should be consistent with -H_p, a positive number

    # compare upper and lower limits of the estimates vs plume quantities
    tops = H_est.n + H_est.s
    bottoms = H_est.n - H_est.s

    topM = - (H_p.n) + H_p.s
    bottomM = - (H_p.n) - H_p.s

    # b and t define the top and bottom of where abs(H_p) and H_est overlap
    b= max(bottoms, bottomM)
    t= min(tops, topM)
    if b < t:
        # there is overlap between the uncertainties of space plume obs,
        # and this combination of H2in and H_b.
        nom = (b+t)/2
        # need to subtract H2in to get H2bio ranges back
        return uf(nom, abs(nom-b)) - H2in
    else:
        return uf(np.nan,np.nan)

def criticalH2bio(H2p, R_H2toCH4, R_abb, R_b=-4.):
    """
    Get the maximum possible H2 bio consumption for the plume methane to
    make sense for a given abio to bio methane ratio.
    """
    return H2p*R_b/(R_H2toCH4*(1+R_abb))

def everyother(ls, num=1):
    """
    Return a list of strings that only contains every num entries in ls,
    converted to scientific notation.
    """
    eo =[]
    i=0
    for l in ls:
        if i==num:
            o = int(np.log10(l))
            eo.append(r'$10^{{{0}}}$'.format(o))
        else:
            eo.append('')
            i=0
        i+=1
    return eo

def interticks(axis, num=1):
    """
    Set the ticks on a parasite axis axis.
    """
    ymin, ymax  = axis.get_ylim()
    yminr = int(round(np.log10(ymin), 0))
    ymaxr = int(round(np.log10(ymax), 0))

    axticks = np.logspace(yminr, ymaxr, num=abs(ymaxr-yminr)+1)
    axis.set_yticks(axticks)
    axis.set_yticklabels(everyother(axticks, num=int(num)))
    axis.tick_params(axis='both', direction='inout')
    axis.axis["right"].major_ticks.set_tick_out(True)
    return axis


def Fig5_BiomassTurnover_vs_abiobioratio():
    """
    Generate Figure 5 from Higgins et al. 2024. Data for this figure is
    hard-coded, so will not update if new simulations are performed.
    """
    # ranges of H2 input to examine for panel A
    H2in = np.logspace(-5, 5, num=10000)

    # nominal output flux of CH4 in space plume
    # converted to mol/s per Higgins (2022)
    plumeCH4nom = -(5.55+167)/2
    plumeCH4dev = abs(plumeCH4nom+5.55)
    CH4p = uf(plumeCH4nom, plumeCH4dev)

    # as above for H2
    plumeH2nom = -(22.2+777)/2
    plumeH2dev = abs(plumeH2nom+22.2)
    H2pobs = uf(plumeH2nom, plumeH2dev)

    # space plume molar ratio between H2 and CH4 per Waite et al. 2017
    R_H2toCH4 = uf(0.9,0.5)/uf(0.2, 0.1)
    # same ratio for the methanogenesis metabolism
    R_bio = -4.

    # range of abio to bio CH4 ratios to examine
    R_abbvals = np.logspace(-6, 6, num=100)

    # maximum and minimum H2 rates consumed by biology, and
    # required prodction in the core to support both that and the space plume escape
    maxH2bios, minH2bios = [],[]
    upper_maxH2ins, lower_maxH2ins = [],[]
    upper_minH2ins, lower_minH2ins = [],[]


    for R_abb in R_abbvals:
        # R_abb = R_abbvals[i]
        # calculate flux of H2 consumed by biology at this ratio and H2 input
        # across the entire y axis range
        H2bio = get_H2_bio(H2in, R_abb, R_H2toCH4)
        # update the H2bio list values to those which are consistent with
        # space plume methane uncertainty (those wihch aren't become np.nan)
        H2bio = [Mp_consistency(CH4p, H_b, R_bio, R_abb) for H_b in H2bio]
        # update the H2bio list values to those which are consistent with
        # space plume H2 estimates (those which aren't become np.nan).
        # take absolute value for easier plotting.
        absH2bio = [abs(Hp_consistency(H_i, H_b, H2pobs)) for H_b, H_i in zip(H2bio, H2in)]

        # absH2bio is now a list of ufloats made up of either nans or H2bio ranges
        # which are possible within uncertainty of the plume fluxes.
        # extract the upper and lower limits of each possibility.
        upperH2bio = np.array([a.n + a.s for a in absH2bio])
        lowerH2bio = np.array([a.n - a.s for a in absH2bio])

        # find indicies of the maximum and minimum consistent bio consumption rates
        e_maxH2bio =  np.where(upperH2bio == np.nanmax(upperH2bio))
        e_minH2bio = np.where(lowerH2bio == np.nanmin(lowerH2bio))

        # as these are max and min, there should only be one index returned.
        maxH2bio = upperH2bio[e_maxH2bio[0][0]]
        minH2bio = lowerH2bio[e_minH2bio[0][0]]

        maxH2bios.append(maxH2bio)
        minH2bios.append(minH2bio)

        # using endmember concentrations of the plume H2 observations,
        # estimate the max and min H2 input to ocean required to support
        # both biosphere and plume output.
        upper_maxH2ins.append(- H2pobs.n + H2pobs.s + maxH2bio)
        lower_maxH2ins.append(- H2pobs.n - H2pobs.s + maxH2bio)

        upper_minH2ins.append(- H2pobs.n + H2pobs.s + minH2bio)
        lower_minH2ins.append(- H2pobs.n - H2pobs.s + minH2bio)


    fig = plt.figure(figsize=(11.5,7.5))

    # we want to create the axes seperately, so the upper right one
    # can have parasite axes and the bottom right one can be
    # narrower than the others.
    ax = [None, None, None, None, None]

    ax[0] = fig.add_subplot(2,5,(1,2))
    ax[1] = host_subplot(2,5,(3,4), axes_class=AA.Axes)
    ax[2] = fig.add_subplot(2,5,(6,7))
    ax[3] = fig.add_subplot(2,5,(8,9))
    ax[4] = fig.add_subplot(2,5,10)

    maxH2bios = np.array(maxH2bios)
    minH2bios = np.array(minH2bios)

    # top left panel: H2 consumption/input as calculated above
    ax[0].plot(R_abbvals, maxH2bios, c='b', label=r'Maximum methanogen H$_{2}$ consumption')
    ax[0].plot(R_abbvals, minH2bios, c='b', ls='dashed', label='Minimum methanogen H2 consumption')

    ax[0].fill_between(R_abbvals, upper_maxH2ins, lower_maxH2ins, label=r'H$_{2}$ inflow corresponding to max. consumption', facecolor='none', hatch='X', edgecolor='r', alpha=0.3)
    ax[0].fill_between(R_abbvals, upper_minH2ins, lower_minH2ins, label=r'H$_{2}$ inflow corresponding to min. consumption', facecolor='none', hatch='O', edgecolor='m', alpha=0.3)

    ax[0].set_ylabel(r'H$_{\mathregular{2}}$ flux [mol / s]')
    ax[0].set_xscale('log')
    ax[0].set_yscale('log')

    ax[0].set_ylim(1e-4,1e4)
    ax[0].set_xlim(1e-6,1e6)

    ax[0].legend(fontsize=6, handlelength=4, handleheight=2)
    ax[0].grid()



    dry_mass = 300*3.44128688529157*10**-18 # TOM in kg (Higgins & Cockell 2020)
    cellfrac_C = 0.5 # approx fraction of a cell mass that is carbon (Atlas, 1995)

    # turnover estimates
    TOnames = [r'MC upper limit turnover $\approx10^{14}$ cells / mol H$_{2}$',
      r'MC lower limit turnover $\approx10^{12.5}$ cells / mol H$_{2}$',
      r'Earth-like methanogen turnover $\approx10^{11.6}$ cells / mol H$_{2}$',
      r'Conservative minimum turnover $\approx10^{11}$ cells / mol H$_{2}$',]
    # endmember turnover values as determined in the main text
    TOvals = [1e14,3e12,0.4 / (dry_mass*1000),1e11]

    # print and colorblind-friendly colors
    c = ['#e66101','#fdb863','#5e3c99','#b2abd2',]
    for i in range(len(TOnames)):
        ax[1].plot(R_abbvals, maxH2bios*TOvals[i], c=c[i], ls='dotted',label=TOnames[i])
        ax[1].plot(R_abbvals, minH2bios*TOvals[i], c=c[i], ls='dashed')
    ax[1].fill_between(R_abbvals, maxH2bios*TOvals[-1], minH2bios*TOvals[-1], facecolor= '#b2abd2', alpha=0.4)
    ax[1].set_yscale('log')
    ax[1].set_ylabel('Total biomass turnover [cells / s]')
    ax[1].set_ylim(1e6, 1e18)
    ax[1].legend(fontsize=6, handlelength=4)

    ax[1] = interticks(ax[1])
    ax[1].grid()


    # now create the parasite axes
    twax1 = ax[1].twinx()
    twax2= ax[1].twinx()
    twax3 = ax[1].twinx()

    # twax1 is like a normal twinx
    # make hidden lines to have a second legend on the main plot
    twax1.plot(1e-9, 1e-9, c='k', ls='dotted', label=r'max methanogen H$_{2}$ consumption')
    twax1.plot(1e-9, 1e-9, c='k', ls='dashed', label=r'min methanogen H$_{2}$ consumption')
    twax1.legend(loc='upper right', fontsize=6, handlelength=4)

    twax1.axis["right"].toggle(all=True)
    twax2.axis["right"].toggle(all=True)
    twax3.axis["right"].toggle(all=True)

    twax1.set_ylabel('Cellular carbon flux to top of ocean [kg C / yr]')
    # create conversion factor between cells/s and kgC/yr
    convkgC = dry_mass*cellfrac_C
    convkgCyr = convkgC* 3600 * 24 * 365
    # set the axis limits to the conversion of the existing LHS axis limits
    twax1.set_ylim(ax[1].get_ylim()[0]*convkgCyr, ax[1].get_ylim()[1]*convkgCyr)
    twax1.set_yscale('log')
    twax1 = interticks(twax1)

    offset = 60 # the offset of this parasite axis
    twax2.axis["right"] = twax2.new_fixed_axis(loc="right", offset=(offset, 0))
    twax2.set_ylabel(r'Max. cells in space plume$^{\blacktriangle}$ [cells / g]', backgroundcolor='w')

    # there is an upper bound of 1000 kg / s of H2O coming up
    # so that is 1e6 g / s
    twax2.set_ylim(ax[1].get_ylim()[0]*1e-6, ax[1].get_ylim()[1]*1e-6)
    twax2.set_yscale('log')
    twax2 = interticks(twax2)


    twax3.axis["right"] = twax3.new_fixed_axis(loc="right", offset=(120, 0))
    twax3.set_ylabel(r'Max. cellular carbon in space plume$^{\blacktriangle}$ [g C / kg]')

    # convert using the 1000 kg per second (x1e-3), then to kg C / kh H2O, then to g C / kg H2O(x1e3)
    twax3.set_ylim(ax[1].get_ylim()[0]*0.001*1000*convkgC, ax[1].get_ylim()[1]*0.001*1000*convkgC)
    twax3.set_yscale('log')
    twax3 = interticks(twax3)


    #add horizontal lines not bound by the axes
    ax[1].annotate('', xy=(1e-6, maxH2bios[0]*TOvals[-1]), xytext=(8e11, maxH2bios[0]*TOvals[-1]), arrowprops=dict(arrowstyle="-", color='#5e3c99', linewidth=2., alpha=0.65),zorder=2)
    ax[1].annotate('', xy=(1e-6, minH2bios[0]*TOvals[-1]), xytext=(8e11, minH2bios[0]*TOvals[-1]), arrowprops=dict(arrowstyle="-", color='#5e3c99', linewidth=2., alpha=0.65),zorder=2)
    ax[1].annotate('', xy=(5e5, minH2bios[0]*TOvals[-1]), xytext=(5e5, maxH2bios[0]*TOvals[-1]), arrowprops=dict(arrowstyle="<->", color='#5e3c99', linewidth=1., alpha=0.65),zorder=2)

    ax[1].text( 3e5, 1.2e13, 'Conservative \n 100% biotic \n endmember', color='#5e3c99', ha='right', va='center', fontsize=6)

    ax[1].text( 1e15, 1e12, r'$\blacktriangle$ Assumes no diluting or concentrating mechanisms after leaving habitat', color='k', ha='center', va='center', rotation='vertical', fontsize=6.5)

    # now for the lower two panels of biomass

    cmap=plt.cm.get_cmap('coolwarm')
    Tvals = [273.15, 293.15, 313.15, 333.15, 353.15, 373.15, 393.15]

    # these are hard coded and pulled from the output of BiomassWindow.py
    pH8_BMs = {'EL': 10**np.array([21.36597115, 20.24115261, 19.21049981,
      18.28892984, 17.43741759, 16.64208399, 15.88770475]),
      'ALL': 10**np.array([20.79381304, 19.11069861, 17.42397541,
      15.86177034,  14.41758129,  13.19506159, 12.14756325]),
      'min': 10**7.75368542,
      'max': 10**23.30382862}

    pH9_BMs = {'EL': 10**np.array([22.95860457, 21.58720607,  20.22866652,
      19.02796195,  18.02763894,  17.12340047, 16.24818359]),
      'ALL': 10**np.array([22.95860457, 21.58720607, 20.22771856,
      18.89025471, 17.63163126,  16.4660584, 15.43205872]),
      'min': 10**12.12892001,
      'max': 10**23.28333132}

    for i, col in enumerate(np.linspace(0,1,num=7)):
        ax[2].plot(R_abbvals, maxH2bios*pH8_BMs['EL'][i], c=cmap(col), ls='dotted')
        ax[2].plot(R_abbvals, maxH2bios*pH8_BMs['ALL'][i], c=cmap(col), ls='dashed')

        ax[3].plot(R_abbvals, maxH2bios*pH9_BMs['EL'][i], c=cmap(col), ls='dotted')
        ax[3].plot(R_abbvals, maxH2bios*pH9_BMs['ALL'][i], c=cmap(col), ls='dashed')

    ax[2].text(1e5, 1e26, 'ocean pH: 8', va='center', ha='right', backgroundcolor='w')
    ax[3].text(1e5, 1e26, 'ocean pH: 9', va='center', ha='right', backgroundcolor='w')


    ax[2].plot(R_abbvals, maxH2bios*pH8_BMs['min'], c='maroon', label='Lowest biomass from distribution')
    ax[2].plot(R_abbvals, maxH2bios*pH8_BMs['max'], c='navy', label='Largest biomass from distribution')
    ax[3].plot(R_abbvals, maxH2bios*pH9_BMs['min'], c='maroon', label='Lowest biomass from distribution')
    ax[3].plot(R_abbvals, maxH2bios*pH9_BMs['max'], c='navy', label='Largest biomass from distribution')

    # labelling for lower biomass axes
    for a in ax[2:4]:
        a.set_xlabel(r'Plume abio to bio CH$_{4}$ ratio')
        a.set_ylabel(r'Max.$^{*}$ total standing biomass [cells]')
        a.set_ylim(1e3,1e28)
        a.plot([1e-10], [1e-10], c='k', ls='dashed', label='Mean of entire habitable distribution (colors indicate T)')
        a.plot([1e-10], [1e-10], c='k', ls='dotted', label='Mean of energy-limited habitable distribution (colors indicate T)')
        a.set_yscale('log')
        a.grid()
        a.text(1.2e-6, 1.5e8, r'$^{*}$using maximum biological H$_\mathregular{2}$ consumption from A', fontsize=6)
        a.legend(fontsize=6, handlelength=4)

    twa = ax[3].twinx()
    twa.set_ylim(a.get_ylim()[0]*convkgC, a.get_ylim()[1]*convkgC)
    twa.set_yscale('log')
    twa.set_ylabel('Total standing biomass [kg C] [axes to left]')


    # universal properties for all main axes
    for a in ax[:4]:
        a.set_xlim(1e-6, 1e6)
        a.set_xscale('log')
        a.set_xlabel(r'Ratio of abiotic to biotic CH$_{\mathregular{4}}$ in space plume')
    for a, _i in zip(ax, ['A', 'B', 'C', 'D', 'E']):
        a.text(-0.02,1.02, _i, ha='center', va='bottom', fontweight='bold', fontsize=12, transform = a.transAxes)


    plt.colorbar(plt.cm.ScalarMappable(norm=mpl.colors.Normalize(273, 393), cmap=cmap), ax=ax[4], orientation='vertical', label='Temperature [K]', pad=0)
    ax[4].set_xlabel(r'Probability uninhabitable [%]')
    ax[4].set_ylim(273.15,393.15)

    # pulled from output in HabitabilityProbability.py
    Tvals = np.linspace(273.15, 393.15, num=25)
    prob_unin_9 = [97.50, 95.69,93.60,90.49,87.36,83.69,80.16,75.79,71.89,67.74,64.53,59.74,56.67,53.89,50.32,47.02,45.35,43.15,41.38,39.59, 38.35,37.50,36.71,36.05,35.72]
    prob_unin_8 = [11.48,8.66,6.78,5.41,3.98,3.09,2.37,1.86,1.24,0.94,0.62,0.44,0.39,0.30,0.14,0.14,0.08,0.07,0.05,0.04,0.02,0.03,0.02,0.02,0.02]

    acmap=plt.cm.get_cmap('autumn')

    ax[4].plot(prob_unin_9, Tvals, lw=4, c=acmap(0))
    ax[4].plot(prob_unin_8, Tvals, lw=4, c=acmap(6/8), ls='dashed')
    ax[4].set_yticklabels([])
    ax[4].set_yticks([])
    ax[4].text(15,280,'pH 8', ha='left', va='center', color=acmap(6/8))
    ax[4].text(50,385,'pH 9', ha='left', va='center', color=acmap(0))


    fig.subplots_adjust(top=0.967,
      bottom=0.083,
      left=0.072,
      right=0.95,
      hspace=0.25,
      wspace=0.75)
    plt.savefig('Figures/F5_BiomassTurnover_vs_abiobioratio.pdf')
    plt.savefig('Figures/F5_BiomassTurnover_vs_abiobioratio.png', dpi=200)
    plt.close()




def FigS4_Specific_abio_bio_ratio_H2flux():
    """
    Generate Fig S4 for Higgins et al 2024, which examines the ranges of
    biological H2 consumption that might be consistent with space plume fluxes
    of H2 and ratios of abiotic to biotic methane.
    Additionally plot ranges of biomass turnover that can be consistent with
    plume observations (but not necessarily H2 production estimates at the ocean floor)
    """
    # ranges of H2 input to examine
    H2in = np.logspace(-5, 5, num=10000)

    # three abio to bio CH4 ratios to examine in diffferent columns
    R_abbvals = [0.,1.,100.]

    # nominal output flux of CH4 in space plume
    # converted to mol/s per Higgins (2022)
    plumeCH4nom = -(5.55+167)/2
    plumeCH4dev = abs(plumeCH4nom+5.55)
    CH4p = uf(plumeCH4nom, plumeCH4dev)

    # as above for H2
    plumeH2nom = -(22.2+777)/2
    plumeH2dev = abs(plumeH2nom+22.2)
    H2pobs = uf(plumeH2nom, plumeH2dev)

    # space plume molar ratio between H2 and CH4 per Waite et al. 2017
    R_H2toCH4 = uf(0.9,0.5)/uf(0.2, 0.1)
    # same ratio for the methanogenesis metabolism
    R_bio = -4.

    fig, axs = plt.subplots(nrows=2,ncols=len(R_abbvals), figsize=(6*(len(R_abbvals)),10))

    absH2bios, H2ps = [],[]
    # first plot the top three panels, where we examine the H2-flux space that is
    # possible for an Enceladus biosphere
    for i, ax in enumerate(axs[0]):
        # each panel uses a different plume abiotic to biotic CH4 ratio.
        R_abb = R_abbvals[i]
        ax.set_title('Abiotic : biotic methane in plume = '+ str(R_abb))

        # compute the ranges of biological H2 consumption that are consistent
        # with this abio:bio methane ratio and the Cassini uncertainties
        H2bio = get_H2_bio(H2in, R_abb, R_H2toCH4)
        H2bio = [Mp_consistency(CH4p, H_b, R_bio, R_abb) for H_b in H2bio]
        absH2bio = [abs(Hp_consistency(H_i, H_b, H2pobs)) for H_b, H_i in zip(H2bio, H2in)]

        # H2p is then how much H2 would be anticipated in the space plume.
        # i.e. input - bio consumed
        H2p = H2in - absH2bio
        absH2bios.append(absH2bio)
        H2ps.append(H2p)

        # maximum possible H2 bio consumption for the plume methane to
        # make sense for a given abio to bio methane ratio.
        abscritH2b = criticalH2bio(H2pobs, R_H2toCH4, R_abb, R_b=R_bio)

        ax.axhline(abscritH2b.n+abscritH2b.s, c='g', label='Maximum methanogen H$_2$ consumption')
        ax.fill_between(H2in, [a.n-a.s for a in absH2bio], [a.n+a.s for a in absH2bio], facecolor='b', alpha=0.3, label='H$_2$ consumed by methanogens')
        ax.fill_between(H2in, [a.n-a.s for a in H2p], [a.n+a.s for a in H2p], facecolor='r', alpha=0.3, label='H$_2$ in space plume')

        ax.plot(H2in, H2in, c='r', label='H$_2$ in plume for 100% abiotic CH$_4$')

        ax.set_yscale('log')
        ax.set_xscale('log')

        ax.set_xlabel('Total H$_2$ flux at bottom of ocean [mol/s]')
        ax.set_ylabel('H$_2$ consumption or escape [mol/s]')

        ax.fill_between([1e-5,1e5],[-H2pobs.n-H2pobs.s, -H2pobs.n-H2pobs.s], [-H2pobs.n+H2pobs.s,-H2pobs.n+H2pobs.s], alpha=0.2, facecolor="none", hatch="X", label='Inferred range of plume H$_2$')

        ax.axvline(1e-3, c='slategray', ls='dashdot')
        ax.axvline(0.6, c='slategray', ls='dashdot')
        ax.axvline(34., c='slategray', ls='dashdot')
        ax.axvline(100., c='slategray', ls='dashdot', label='Literature estimates of H$_2$ flux')

        ax.axhline(-H2pobs.n+H2pobs.s, c='k', lw=4., ls='dashed', label='Max H$_2$ escape for consistency')
        ax.axvline(22.2, c='k', lw=4., label='Minimum H$_2$ flux at bottom of ocean for consistency')
        ax.set_xlim(1e-4,1e5)
        ax.set_ylim(1e-2, 1.5e7)
        ax.legend(loc='upper left', framealpha=0.9, handlelength=4.)


    cellfrac_C = 0.5  # approx fraction of a cell mass that is carbon (Atlas 1995)
    dry_mass = 300*3.44128688529157*10**-18 # TOM in kg (Higgins & Cockell 2020)

    TOnames = [r' MC upper limit',
      r' MC lower limit',
      r' Conservative minimum',
      r' Earth-like methanogen']
    # endmember turnover values as determined in the main text
    TOvals = [1e14,3e12,1e11,0.4 / (dry_mass*1000)]
    TOarrs_1to1 = [[],[],[],[]]
    TOarrs_allCH4 = [[],[],[],[]]

    hatches = ['', 'X', 'O', '/']
    for i, R_abb in enumerate(R_abbvals):

        H2bio_nom = np.array([a.n for a in absH2bios[i]])
        c = ['b', 'r', 'g', 'k']

        for j, TO in enumerate(TOvals):

            TOs = TO*dry_mass*1000*cellfrac_C*1e-3 * 3600 * 24 * 365 * np.array(absH2bios[i]) #/ (R_H2toCH4)

            axs[1][i].fill_between(H2in, [a.n-a.s for a in TOs], [a.n+a.s for a in TOs], alpha=0.5, facecolor=c[j], hatch=hatches[j], edgecolor=c[j])
            topTOs = np.array([a.n-a.s for a in TOs])
            itopTOs = np.nanargmax(topTOs)
            axs[1][i].text(H2in[itopTOs], topTOs[itopTOs], TOnames[j], c=c[j], alpha=0.8, va='top', fontsize=8)

        axs[1][i].fill_between(H2in, [10e-10 for a in H2in], [10e-10 for a in H2in], alpha=0.4, facecolor=c[0], hatch=hatches[i], edgecolor=c[0], label='Cell turnover if abio:bio methane ratio = '+str(R_abb)+'(all colors)')

        axs[1][i].plot(H2in, len(H2in)*[1e5,], c='slategray', ls='dashed', alpha=0.8, label='Plume-informed turnover range from Affholder et al., 2022')
        axs[1][i].plot(H2in, len(H2in)*[1e7,], c='slategray', ls='dashed', alpha=0.8)

        axs[1][i].set_yscale('log')
        axs[1][i].set_xscale('log')

        axs[1][i].axvline(22.2, c='k', lw=4., label='Minimum H$_2$ flux at bottom of ocean for consistency')

        axs[1][i].set_xlim(10,1e4)
        axs[1][i].set_ylim(100,1e11)

        axs[1][i].set_xlabel('Total H$_2$ flux at bottom of ocean [mol/s]')
        axs[1][i].set_ylabel('Biomass Turnover [kg C /yr]')

        axs[1][i].legend(framealpha=0.9)


    plt.tight_layout()

    plt.savefig('Figures/FS4_Specific_abio_bio_ratio_H2flux.pdf')
    plt.savefig('Figures/FS4_Specific_abio_bio_ratio_H2flux.png', dpi=200)

    plt.close()




Fig5_BiomassTurnover_vs_abiobioratio()
FigS4_Specific_abio_bio_ratio_H2flux()
