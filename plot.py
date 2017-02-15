# workaround to select Agg as backend consistenly
import matplotlib as mpl
mpl.use('Agg')
mpl.rcParams['text.latex.preamble'] = [r'\usepackage{amsmath}']
import matplotlib.pyplot as plt
import seaborn as sns

plt.rc('text', usetex=True)
sns.set_style("whitegrid")
sns.set_context(font_scale=1.5)

def rescale_barplot_width(ax, factor=0.6):
    for bar in ax.patches:
        x = bar.get_x()
        new_width = bar.get_width() * factor
        center = x + bar.get_width() / 2.
        bar.set_width(new_width)
        bar.set_x(center - new_width / 2.)
