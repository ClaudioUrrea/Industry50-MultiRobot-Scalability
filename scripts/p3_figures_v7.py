#!/usr/bin/env python3
"""
IEEE Access Industry 5.0 Multi-Robot Architecture Paper - Figure Generation
Scalable Multi-Robot Architecture with Digital Twin Integration

ALL DATA IN THIS SCRIPT ARE SIMULATION OUTPUTS.
Every series plotted below was produced by the CoppeliaSim 4.10 / Unity 2022.3
LTS digital twin described in the manuscript. No physical multi-robot cell was
built and no human participant took part in any measurement. Axis labels and
titles must therefore read "simulated" / "predicted", never "actual",
"measured" or "deployment".

Author: Claudio Urrea
Institution: University of Santiago of Chile
Date: July 2026
---

"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import rcParams
from matplotlib.ticker import AutoMinorLocator
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# --- IEEE Access Typography ---
_FONT_FAMILY = 'serif'
_FONT_SERIF  = ['TeX Gyre Termes', 'Liberation Serif', 'Times New Roman',
                'DejaVu Serif']

rcParams.update({
    'font.family':        _FONT_FAMILY,
    'font.serif':         _FONT_SERIF,
    'mathtext.fontset':   'custom',
    'mathtext.rm':        'TeX Gyre Termes',
    'mathtext.it':        'TeX Gyre Termes:italic',
    'mathtext.bf':        'TeX Gyre Termes:bold',
    'font.weight':        'bold',
    'axes.labelweight':   'bold',
    'axes.titleweight':   'bold',
    'font.size':          11,
    'axes.labelsize':     12,
    'axes.titlesize':     13,
    'xtick.labelsize':    10,
    'ytick.labelsize':    10,
    'legend.fontsize':    9.5,
    'xtick.direction':    'in',
    'ytick.direction':    'in',
    'xtick.major.width':  1.0,
    'ytick.major.width':  1.0,
    'xtick.minor.width':  0.6,
    'ytick.minor.width':  0.6,
    'axes.linewidth':     1.2,
    'savefig.dpi':        600,
    'figure.autolayout':  True,
    'pdf.fonttype':       42,
    'ps.fonttype':        42,
})

# --- Professional colour palette ---
COLORS = {
    'primary':    '#1f77b4',
    'secondary':  '#ff7f0e',
    'tertiary':   '#2ca02c',
    'quaternary': '#d62728',
    'quinary':    '#9467bd',
}

# --- Master data: simulation outputs, reconciled with Tables 2-3 and Eq. 3 ---
# NOTE: Economic series (capex, revenue, opex, breakeven) are not plotted here;
#       cost modelling is deferred to the companion study.
MASTER = {
    'N':         np.array([1, 2, 3, 4, 5]),
    'T':         np.array([307, 554, 802, 963, 1047]),
    'T1':        307,
    'eta_sim':   np.array([1.000, 0.903, 0.871, 0.784, 0.682]),
    'beta':      0.066,
    'gamma':     0.003,
}
MASTER['ideal'] = MASTER['N'] * MASTER['T1']
MASTER['scale'] = MASTER['T'] / MASTER['T1']


class IEEEAccessFigures:

    def __init__(self, output_dir='figures_p3_IEEE'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def _save(self, name):
        base = self.output_dir / name
        plt.savefig(f"{base}.pdf", dpi=600, bbox_inches='tight')
        plt.savefig(f"{base}.png", dpi=600, bbox_inches='tight')
        plt.close()

    # ------------------------------------------------------------------
    # Figure 2: Throughput Scaling (matches Table 3)
    # ------------------------------------------------------------------
    def fig2_throughput_scaling(self):
        N     = MASTER['N']
        units = MASTER['T']
        scale = MASTER['scale']
        eff   = MASTER['eta_sim'] * 100

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))

        ax1.bar(N, units, width=0.6, color=COLORS['primary'],
                alpha=0.85, edgecolor='black', linewidth=1.4)
        for n, u, s in zip(N, units, scale):
            ax1.text(n, u + 30, f'{u:,}', ha='center',
                     fontweight='bold', fontsize=11)
            ax1.text(n, u / 2, f'{s:.2f}\u00d7', ha='center',
                     color='white', fontweight='bold', fontsize=11)

        ax1.set_xlabel('Number of Robots (N)')
        ax1.set_ylabel('Simulated Units per Shift (8 hours)')
        ax1.set_title('Manufacturing Throughput Scaling\n'
                      'Digital-Twin Campaign', pad=12)
        ax1.set_xticks(N)
        ax1.set_ylim([0, 1300])
        ax1.grid(True, axis='y', alpha=0.30, linewidth=0.8)
        ax1.yaxis.set_minor_locator(AutoMinorLocator(2))

        ax2.plot(N, eff, 'o-', color=COLORS['secondary'],
                 linewidth=2.8, markersize=11, markeredgecolor='black',
                 markeredgewidth=1.2)
        ax2.fill_between(N, eff, alpha=0.25, color=COLORS['secondary'])
        ax2.axhline(100, color='green', ls='--', lw=2, alpha=0.7,
                    label='Linear scaling (100 %)')
        for n, e in zip(N, eff):
            ax2.annotate(f'{e:.1f} %', xy=(n, e), xytext=(0, 13),
                         textcoords='offset points', ha='center',
                         fontweight='bold', fontsize=11)

        ax2.set_xlabel('Number of Robots (N)')
        ax2.set_ylabel('Coordination Efficiency (%)')
        ax2.set_title('Multi-Robot Coordination Efficiency', pad=12)
        ax2.set_xticks(N)
        ax2.set_ylim([0, 115])
        ax2.grid(True, alpha=0.30, ls='--', linewidth=0.8)
        ax2.legend(loc='upper right')
        plt.tight_layout()
        self._save('Fig2_Throughput_Scaling')

    # ------------------------------------------------------------------
    # Figure 3: Latency Scaling
    # ------------------------------------------------------------------
    def fig3_latency_scaling(self):
        N    = np.array([1, 2, 3, 4, 5])
        mean = np.array([37, 42, 48, 51, 54])
        p95  = np.array([52, 67, 74, 78, 82])
        pmax = np.array([68, 89, 103, 115, 127])

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(N, mean, 'o-',  label='Mean',
                color=COLORS['primary'],   lw=2.8, ms=10,
                markeredgecolor='black', markeredgewidth=1.2)
        ax.plot(N, p95,  's-',  label='95th percentile',
                color=COLORS['secondary'], lw=2.8, ms=9,
                markeredgecolor='black', markeredgewidth=1.2)
        ax.plot(N, pmax, '^-',  label='Maximum',
                color=COLORS['tertiary'],  lw=2.8, ms=9,
                markeredgecolor='black', markeredgewidth=1.2)

        slope = 4.25
        N_fit = np.linspace(1, 5, 100)
        fit   = slope * N_fit + (mean[0] - slope * N[0])
        ax.plot(N_fit, fit, '--', color='gray', alpha=0.55, lw=2,
                label=f'Linear fit: {slope:.2f} ms/robot')
        ax.axhline(100, color='red', ls=':', lw=2.2, alpha=0.7,
                   label='100 ms threshold (exceeded by max. for N>=3)')

        ax.set_xlabel('Number of Robots (N)')
        ax.set_ylabel('Latency (ms)')
        ax.set_title('Digital Twin Synchronization Latency Scaling\n'
                     'N = 1-5 Simulation Campaign', pad=12)
        ax.set_xticks(N)
        ax.set_ylim([0, 145])
        ax.grid(True, alpha=0.30, ls='--', linewidth=0.8)
        ax.legend(loc='upper left', framealpha=0.95)
        plt.tight_layout()
        self._save('Fig3_Latency_Scaling')

    # ------------------------------------------------------------------
    # Figure 1: Safety Performance (first figure after the 2026 section reorder)
    # ------------------------------------------------------------------
    def fig1_safety_performance(self):
        N     = np.array([1, 2, 3, 4, 5])
        trad  = np.array([1.20, 1.15, 1.22, 1.19, 1.18])
        learn = np.array([0.58, 0.71, 0.79, 0.80, 0.81])
        red   = ((trad - learn) / trad) * 100

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))
        x = np.arange(len(N))
        w = 0.34

        ax1.bar(x - w/2, trad,  w, label='Traditional',
                color=COLORS['quaternary'], alpha=0.82,
                edgecolor='black', lw=1.2)
        ax1.bar(x + w/2, learn, w, label='Learned CBF',
                color=COLORS['tertiary'],  alpha=0.82,
                edgecolor='black', lw=1.2)
        ax1.axhline(0.15, color='blue', ls=':', lw=2.5,
                    label='Design floor (0.15 m)')
        ax1.axhline(0.98, color='purple', ls='-.', lw=2.0, alpha=0.8,
                    label='PSD at 1.2 m/s (0.98 m)')
        for i, (t, l) in enumerate(zip(trad, learn)):
            ax1.text(i - w/2, t + 0.03, f'{t:.2f} m', ha='center',
                     fontweight='bold', fontsize=9.5)
            ax1.text(i + w/2, l + 0.03, f'{l:.2f} m', ha='center',
                     fontweight='bold', fontsize=9.5)
        ax1.set_xlabel('Number of Robots (N)')
        ax1.set_ylabel('Average Separation (m)')
        ax1.set_title('Human-Robot Separation Distance', pad=12)
        ax1.set_xticks(x); ax1.set_xticklabels(N)
        ax1.set_ylim([0, 1.60])
        ax1.legend(fontsize=9)
        ax1.grid(True, axis='y', alpha=0.30, linewidth=0.8)

        ax2.plot(x, red, 'o-', lw=3, ms=12, color=COLORS['primary'],
                 markeredgecolor='black', markeredgewidth=1.2)
        ax2.fill_between(x, red, alpha=0.25, color=COLORS['primary'])
        for n, r in zip(x, red):
            ax2.annotate(f'{r:.1f} %', xy=(n, r), xytext=(0, 13),
                         textcoords='offset points', ha='center',
                         fontweight='bold', fontsize=11)
        ax2.set_xlabel('Number of Robots (N)')
        ax2.set_ylabel('Conservatism Reduction (%)')
        ax2.set_title('Reduction in Separation Conservatism\n'
                      '(51.7 % at N = 1 to 31.4 % at N = 5)', pad=12)
        ax2.set_xticks(x); ax2.set_xticklabels(N)
        ax2.set_ylim([0, 60])
        ax2.grid(True, alpha=0.30, ls='--', linewidth=0.8)
        plt.tight_layout()
        self._save('Fig1_Safety_Performance')

    # ------------------------------------------------------------------
    # Figure 4: Disrupted campaign vs. undisrupted simulation (N = 2)
    # NOTE: Payback metric removed — cost modelling deferred to companion study.
    # ------------------------------------------------------------------
    def fig4_disruption_comparison(self):
        """
        Disrupted 60-shift campaign vs. the undisrupted N = 2 simulation.
        Left panel:  Disrupted / nominal ratio (all metrics on ~100% scale)
        Right panel: Relative deviation (%) with absolute annotations
        Both panels compare two simulation conditions; neither is an
        experimental validation and neither uses the closed-form prediction.
        """
        metrics  = ['Throughput', 'Defect rate', 'Energy', 'Uptime']
        units    = ['units/shift', '%', 'kWh/shift', '%']
        proj     = np.array([554,   0.6,  31.2,  98.5])   # undisrupted simulation
        sim      = np.array([547,   0.8,  32.8,  95.9])   # disrupted campaign

        # -- LEFT PANEL: Disrupted as % of nominal (undisrupted) simulation --
        pct_of_proj = (sim / proj) * 100

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.2))
        x = np.arange(len(metrics))
        bar_labels = [f'{m}\n({u})' for m, u in zip(metrics, units)]

        bar_cols_L = [COLORS['tertiary'] if abs(p - 100) <= 10
                      else COLORS['secondary'] for p in pct_of_proj]

        ax1.bar(x, pct_of_proj, width=0.6, color=bar_cols_L,
                alpha=0.82, edgecolor='black', linewidth=1.2)
        ax1.axhline(100, color='black', ls='--', lw=2,
                    label='Nominal simulation (100 %)')
        ax1.axhspan(90, 110, alpha=0.15, color='green',
                    label='\u00b110 % band')

        for i, (p, pr, ac) in enumerate(zip(pct_of_proj, proj, sim)):
            ax1.text(i, p + 2.5, f'{ac:g} / {pr:g}',
                     ha='center', fontweight='bold', fontsize=9)
            ax1.text(i, min(p, 100) - 5, f'{p:.1f} %',
                     ha='center', fontweight='bold', fontsize=10,
                     color='white')

        ax1.set_xticks(x)
        ax1.set_xticklabels(bar_labels, fontsize=9)
        ax1.set_ylabel('Disrupted / Nominal Simulation (\u00d7 100 %)')
        ax1.set_title('Disrupted vs. Undisrupted Simulation\n'
                      '60 Shifts, N = 2, per Station', pad=12)
        ax1.set_ylim([0, 145])
        ax1.legend(loc='upper right', fontsize=8.5)
        ax1.grid(True, axis='y', alpha=0.30, linewidth=0.8)

        # -- RIGHT PANEL: Relative deviation from the nominal simulation (%) --
        rel_err = ((sim - proj) / proj) * 100
        abs_err = sim - proj

        bar_cols_R = []
        for i, e in enumerate(rel_err):
            if metrics[i] in ['Throughput', 'Uptime']:
                bar_cols_R.append(COLORS['tertiary'] if e >= 0
                                  else COLORS['secondary'])
            else:
                bar_cols_R.append(COLORS['tertiary'] if e <= 0
                                  else COLORS['secondary'])

        ax2.barh(x, rel_err, height=0.62, color=bar_cols_R, alpha=0.82,
                 edgecolor='black', linewidth=1.2)
        ax2.axvline(0, color='black', ls='--', lw=2)
        ax2.axvspan(-10, 10, alpha=0.15, color='green',
                    label='\u00b110 %')

        for i, (re, ae, u) in enumerate(zip(rel_err, abs_err, units)):
            sign_re = '+' if re > 0 else ''
            sign_ae = '+' if ae > 0 else ''
            label = f'{sign_re}{re:.1f} %  ({sign_ae}{ae:g} {u})'
            offset = 1.5 if re >= 0 else -1.5
            ha = 'left' if re >= 0 else 'right'
            ax2.text(re + offset, i, label,
                     va='center', ha=ha,
                     fontweight='bold', fontsize=9)

        ax2.set_yticks(x)
        ax2.set_yticklabels(bar_labels, fontsize=9)
        ax2.set_xlabel('Relative Deviation from Nominal Simulation (%)')
        ax2.set_title('Cost of the Disruption Model\n'
                      '(% of the undisrupted value)', pad=12)
        ax2.legend(loc='upper right', fontsize=8.5)
        ax2.grid(True, axis='x', alpha=0.30, linewidth=0.8)
        ax2.set_xlim([-19.5, 49.5])

        plt.tight_layout()
        self._save('Fig4_Disruption_Comparison')

    # ------------------------------------------------------------------
    # Run all
    # ------------------------------------------------------------------
    def generate_all(self):
        print("\n" + "=" * 70)
        print("IEEE Access Industry 5.0 Paper - Figure Generation")
        print("Scalable Multi-Robot Architecture with Digital Twin")
        print("VERSION v5 - simulation framing; all series are digital-twin outputs")
        print("=" * 70)
        print(f"\nOutput : {self.output_dir.absolute()}")
        print(f"Font   : {_FONT_SERIF[0]}\n")

        figs = [
            ('Fig 1: Safety Performance',         self.fig1_safety_performance),
            ('Fig 2: Throughput Scaling',         self.fig2_throughput_scaling),
            ('Fig 3: Latency Scaling',            self.fig3_latency_scaling),
            ('Fig 4: Disruption Comparison',      self.fig4_disruption_comparison),
        ]

        for i, (name, func) in enumerate(figs, 1):
            print(f"  [{i}/{len(figs)}] {name} ...", end=' ')
            try:
                func()
                print("OK")
            except Exception as e:
                import traceback
                print(f"ERROR: {e}")
                traceback.print_exc()

        print("\n" + "=" * 70)
        print("Complete - PDF + PNG files ready")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', default='figures_p3_IEEE')
    args = parser.parse_args()

    gen = IEEEAccessFigures(args.output)
    gen.generate_all()
